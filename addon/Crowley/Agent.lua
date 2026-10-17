local _, ns = ...

-- Lossless, read-only telemetry surface. It is deliberately independent of the
-- scanner's command path: publishing cannot start, stop, or mutate a sweep.
local Agent = {}
ns.Agent = Agent

local WIDTH, HEIGHT, CAPACITY = 128, 128, 2048
local BYTES_PER_ROW = WIDTH / 8
local GLYPH_WIDTH, GLYPH_HEIGHT = 16, 2
local ATLAS_HEIGHT = 512
local PRESENTATION_WIDTH, PRESENTATION_HEIGHT = 1920, 1080
local ATLAS_PATH = "Interface\\AddOns\\Crowley\\Textures\\ByteAtlas"
local CROP_X, CROP_Y = 80, 48
local POSITION_LIMIT = 1000000
local FACING_LIMIT = 6.283185307179586
local SPEED_LIMIT = 1000
local sequence = 0
local boot = (tostring(time()) .. "-" .. tostring(math.random(100000, 999999)))
local surface
local cells = {}
local frameBytes = nil
local elapsed = 1
local nativePhase = "normal"
local nativeOrdinal = 0
local measurementToken = 0
local safePublish
local lastLuaHeap = { method = "collectgarbage_count", available = false, beforeKiB = 0, afterKiB = 0, netKiB = 0 }
local renderMetrics = {
  constructionSeconds = 0, updateCount = 0, updateP99Ms = 0, textureCount = 0,
  effectiveScale = 0, cellSize = { 2, 2 }, luaHeap = lastLuaHeap,
  nativePhase = nativePhase, nativeOrdinal = nativeOrdinal,
}
local updateSamples = {}
local lastPublishError

local function copy(value)
  if type(value) ~= "table" then return value end
  local result = {}
  for key, child in pairs(value) do result[key] = copy(child) end
  return result
end

local function u32(value)
  value = value % 4294967296
  return string.char(value % 256, math.floor(value / 256) % 256, math.floor(value / 65536) % 256, math.floor(value / 16777216) % 256)
end

local function xor32(left, right)
  local result, bit = 0, 1
  while bit <= 2147483648 do
    local l = left % (bit * 2) >= bit
    local r = right % (bit * 2) >= bit
    if l ~= r then result = result + bit end
    bit = bit * 2
  end
  return result
end

local function crc32(bytes)
  local crc = 4294967295
  for index = 1, #bytes do
    crc = xor32(crc, string.byte(bytes, index))
    for _ = 1, 8 do
      local odd = crc % 2
      crc = math.floor(crc / 2)
      if odd == 1 then crc = xor32(crc, 3988292384) end
    end
  end
  return xor32(crc, 4294967295) % 4294967296
end

local function sortedKeys(tableValue)
  local result = {}
  for key in pairs(tableValue or {}) do result[#result + 1] = key end
  table.sort(result)
  return result
end

local function activeEdit()
  if not ChatFrameUtil or type(ChatFrameUtil.GetActiveWindow) ~= "function" then
    return { active = false, focused = false, text = "" }
  end
  local edit = ChatFrameUtil.GetActiveWindow()
  if not edit then return { active = false, focused = false, text = "" } end
  -- The readback is a proof of the actual active EditBox.  Missing methods
  -- are an unavailable proof, never an implicit ``shown`` value.
  if type(edit.IsShown) ~= "function" or type(edit.HasFocus) ~= "function" or
      type(edit.GetText) ~= "function" then
    return { active = false, focused = false, text = "" }
  end
  local shown = edit:IsShown() == true
  local focused = edit:HasFocus() == true
  local text = edit:GetText()
  if type(text) ~= "string" or #text > 128 then
    -- Unbounded or malformed chat text cannot enter the telemetry frame and
    -- must force the executor to cancel before it can press Enter.
    return { active = false, focused = false, text = "" }
  end
  return { active = shown, focused = focused, text = text }
end

local function planInfo(plan)
  plan = plan or {}
  return {
    hash = plan.hash or "", count = plan.count or 0,
    cadenceSeconds = plan.cadenceSeconds or 0,
    sweepCapSeconds = plan.sweepCapSeconds or 600,
    initialPriceLevels = plan.initialPriceLevels or 0,
  }
end

local function finiteNumber(value, name, minimum, maximum)
  if type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge or
      value < minimum or value > maximum then
    error("Crowley movement telemetry has invalid " .. name)
  end
  return value
end

local function nativeBoolean(value, name)
  if type(value) ~= "boolean" then error("Crowley movement telemetry has invalid " .. name) end
  return value
end

local NATIVE_FAILURES = { "call_error", "missing", "wrong_type", "nil_result" }

local function nativeFailure(reason)
  for _, allowed in ipairs(NATIVE_FAILURES) do
    if reason == allowed then return reason end
  end
  error("Crowley movement telemetry has invalid native failure state")
end

local function ctmState()
  local result = {
    accessor = "C_CVar.GetCVarBool", cvar = "autointeract", state = "unknown", reason = "missing",
  }
  if type(C_CVar) ~= "table" or type(C_CVar.GetCVarBool) ~= "function" then return result end
  local ok, value = pcall(C_CVar.GetCVarBool, "autointeract")
  if not ok then
    result.reason = nativeFailure("call_error")
  elseif value == nil then
    result.reason = nativeFailure("nil_result")
  elseif type(value) ~= "boolean" then
    result.reason = nativeFailure("wrong_type")
  else
    result.state = value and "enabled" or "disabled"
    result.reason = ""
  end
  return result
end

local GROUND_PREDICATES = {
  { "flying", "IsFlying", false },
  { "falling", "IsFalling", false },
  { "swimming", "IsSwimming", false },
  { "submerged", "IsSubmerged", false },
  { "mounted", "IsMounted", false },
  { "taxi", "UnitOnTaxi", true },
}

local function groundState()
  local values = {
    state = "unknown", falling = "unknown", flying = "unknown", swimming = "unknown",
    submerged = "unknown", mounted = "unknown", taxi = "unknown", reason = "",
  }
  local anyTrue = false
  local firstFailureRank = 99
  local failureRank = { falling = 1, flying = 2, swimming = 3, submerged = 4, mounted = 5, taxi = 6 }
  local function markFailure(field, reason)
    local rank = failureRank[field]
    if rank < firstFailureRank then
      firstFailureRank, values.reason = rank, reason
    end
  end
  for _, entry in ipairs(GROUND_PREDICATES) do
    local field, accessor, playerArgument = entry[1], entry[2], entry[3]
    local fn = _G[accessor]
    if type(fn) ~= "function" then
      values[field] = "unknown"
      markFailure(field, "missing")
    else
      local ok, value
      if playerArgument then ok, value = pcall(fn, "player") else ok, value = pcall(fn) end
      if not ok then
        values[field] = "unknown"
        markFailure(field, "call_error")
      elseif value == nil then
        values[field] = "unknown"
        markFailure(field, "nil_result")
      elseif type(value) ~= "boolean" then
        values[field] = "unknown"
        markFailure(field, "wrong_type")
      else
        values[field] = value and "true" or "false"
        anyTrue = anyTrue or value
      end
    end
  end
  if values.reason ~= "" then
    values.state = "unknown"
  else
    values.state = anyTrue and "not_grounded" or "grounded"
  end
  return values
end

local function nativeBinding(action, field)
  if type(GetBindingKey) ~= "function" then
    error("Crowley movement telemetry requires GetBindingKey")
  end
  -- GetBindingKey's first return is the primary binding.  Preserve the exact
  -- native spelling; normalization would hide a client contract mismatch.
  local value = GetBindingKey(action)
  if type(value) ~= "string" or #value < 1 or #value > 32 or
      value:find("[^A-Z0-9%-]") or value:sub(1, 1) == "-" or value:sub(-1) == "-" or
      value:find("%-%-") then
    error("Crowley movement telemetry has invalid " .. field .. " binding")
  end
  return value
end

local function movementTelemetry()
  if type(UnitPosition) ~= "function" then error("Crowley movement telemetry requires UnitPosition") end
  if type(GetPlayerFacing) ~= "function" then error("Crowley movement telemetry requires GetPlayerFacing") end
  if type(GetUnitSpeed) ~= "function" then error("Crowley movement telemetry requires GetUnitSpeed") end
  if type(UnitAffectingCombat) ~= "function" then error("Crowley movement telemetry requires UnitAffectingCombat") end
  if type(UnitIsDeadOrGhost) ~= "function" then error("Crowley movement telemetry requires UnitIsDeadOrGhost") end
  local x, y, z, instance = UnitPosition("player")
  if type(instance) ~= "number" or instance ~= math.floor(instance) or instance < 0 or instance > 4294967295 then
    error("Crowley movement telemetry has invalid position.instance")
  end
  local position = {
    x = finiteNumber(x, "position.x", -POSITION_LIMIT, POSITION_LIMIT),
    y = finiteNumber(y, "position.y", -POSITION_LIMIT, POSITION_LIMIT),
    z = finiteNumber(z, "position.z", -POSITION_LIMIT, POSITION_LIMIT),
    instance = instance,
  }
  local currentSpeed, runSpeed, flightSpeed, swimSpeed = GetUnitSpeed("player")
  local native = {
    ctm = ctmState(),
    ground = groundState(),
    speedTuple = {
      current = finiteNumber(currentSpeed, "speedTuple.current", 0, SPEED_LIMIT),
      run = finiteNumber(runSpeed, "speedTuple.run", 0, SPEED_LIMIT),
      flight = finiteNumber(flightSpeed, "speedTuple.flight", 0, SPEED_LIMIT),
      swim = finiteNumber(swimSpeed, "speedTuple.swim", 0, SPEED_LIMIT),
      unitStatus = "unverified",
    },
  }
  return {
    position = position,
    facing = finiteNumber(GetPlayerFacing(), "facing", 0, FACING_LIMIT),
    speed = native.speedTuple.current,
    combat = nativeBoolean(UnitAffectingCombat("player"), "combat"),
    deadOrGhost = nativeBoolean(UnitIsDeadOrGhost("player"), "deadOrGhost"),
    bindings = {
      moveForward = nativeBinding("MOVEFORWARD", "moveForward"),
      moveBackward = nativeBinding("MOVEBACKWARD", "moveBackward"),
      strafeLeft = nativeBinding("STRAFELEFT", "strafeLeft"),
      strafeRight = nativeBinding("STRAFERIGHT", "strafeRight"),
      turnLeft = nativeBinding("TURNLEFT", "turnLeft"),
    },
    native = native,
  }
end

function Agent.Snapshot()
  local context = ns.Context.Snapshot()
  local house = ns.Context.House()
  local scanner = ns.Scanner.Status()
  local stored = scanner.pending or {}
  local acked = scanner.loaded or {}
  local last = scanner.lastSaved or {}
  local now = time()
  local uptime = math.floor((GetTime() or 0) * 1000) % 4294967296
  local scannerValue = {
    phase = scanner.phase, activeSweepId = "", startedAt = scanner.startedAt or 0,
    dueAt = scanner.dueAt or 0, ordinal = scanner.ordinal or 0, planned = scanner.planned,
    cursorItemID = scanner.cursorItemID or 0,
  }
  -- The fence proof is part of every frame, including the idle state.  This
  -- keeps controller admission independent of whether a previous frame saw a
  -- fence attempt.
  scannerValue.scheduleFence = copy(scanner.scheduleFence)
  local value = {
    schema = 3, boot = boot, sequence = sequence + 1, wallTime = now, uptimeMs = uptime,
    context = {
      addonVersion = context.addonVersion or ns.VERSION, interface = context.interface or 0,
      clientBuild = context.clientBuild or "", character = context.character or "", realm = context.realm or "",
      playerFaction = context.playerFaction or "", zone = context.zone or "", subzone = context.subzone or "",
      locale = context.locale or "", clientVersion = context.clientVersion or "",
    },
    house = { key = house.key, source = house.source }, plan = planInfo(scanner.plan), ahOpen = ns.ahOpen == true,
    scanner = scannerValue,
    lastSaved = {
      memoryUid = last.memoryUid or "", finishedAt = last.finishedAt or 0, planned = last.planned or 0,
      attempted = last.attempted or 0, failures = last.failures or 0, rows = last.rows or 0, persistence = "unknown",
    },
    pending = {
      ids = copy(stored), count = #stored, cap = 6, blocked = scanner.phase == "blocked",
      reason = scanner.reason or (scanner.phase == "blocked" and "queue_full" or ""),
    },
    loaded = { ackedIds = copy(acked), generatedAt = CROWLEY_DATA.generatedAt or 0 }, chatEdit = activeEdit(),
    motion = movementTelemetry(),
    render = copy(renderMetrics),
  }
  sequence = value.sequence
  return copy(value)
end

local function createSurface()
  local started = debugprofilestop()
  if not UIParent or type(UIParent.GetWidth) ~= "function" or type(UIParent.GetHeight) ~= "function" or
      type(UIParent.GetEffectiveScale) ~= "function" then
    error("Crowley telemetry requires UIParent geometry")
  end
  local rootWidth = UIParent:GetWidth()
  local rootHeight = UIParent:GetHeight()
  local rootEffective = UIParent:GetEffectiveScale()
  if type(rootWidth) ~= "number" or type(rootHeight) ~= "number" or type(rootEffective) ~= "number" or
      rootWidth <= 0 or rootHeight <= 0 or rootEffective <= 0 or
      rootWidth ~= rootWidth or rootHeight ~= rootHeight or rootEffective ~= rootEffective or
      rootWidth == math.huge or rootHeight == math.huge or rootEffective == math.huge or
      rootWidth == -math.huge or rootHeight == -math.huge or rootEffective == -math.huge then
    error("Crowley telemetry has invalid UIParent geometry")
  end
  local aspect = rootWidth / rootHeight
  if math.abs(aspect - PRESENTATION_WIDTH / PRESENTATION_HEIGHT) > 0.01 then
    error("Crowley telemetry requires the pinned 1920x1080 UIParent aspect")
  end
  -- GetPhysicalScreenSize is stale on the verified Wine client.  The root's
  -- logical extent and effective scale are the only native inputs used here;
  -- the presentation profile is pinned by the runtime identity at 1920x1080.
  local uiUnitsPerNativePixel = rootHeight * rootEffective / PRESENTATION_HEIGHT
  if uiUnitsPerNativePixel <= 0 or uiUnitsPerNativePixel ~= uiUnitsPerNativePixel or
      uiUnitsPerNativePixel == math.huge or uiUnitsPerNativePixel == -math.huge then
    error("Crowley telemetry has invalid UI units per native pixel")
  end
  surface = CreateFrame("Frame", "CrowleyAgentSurface", UIParent)
  surface:SetIgnoreParentScale(true)
  surface:SetScale(uiUnitsPerNativePixel)
  surface:SetAlpha(1)
  surface:SetFrameStrata("HIGH")
  surface:EnableMouse(false)
  local effective = surface:GetEffectiveScale()
  if type(effective) ~= "number" or effective <= 0 or effective ~= effective or
      effective == math.huge or effective == -math.huge then
    error("Crowley telemetry surface has invalid effective scale")
  end
  surface:SetSize(CROP_X + WIDTH * 2, CROP_Y + HEIGHT * 2)
  surface:SetPoint("TOPLEFT", UIParent, "TOPLEFT", 0, 0)
  if math.abs(effective - uiUnitsPerNativePixel) > 0.000001 then
    error("Crowley telemetry surface scale does not match the requested native factor")
  end
  for row = 0, HEIGHT - 1 do
    for column = 0, BYTES_PER_ROW - 1 do
      local texture = surface:CreateTexture(nil, "ARTWORK")
      texture:SetSnapToPixelGrid(true)
      texture:SetTexelSnappingBias(0.5)
      texture:SetSize(GLYPH_WIDTH, GLYPH_HEIGHT)
      texture:SetPoint(
        "TOPLEFT", surface, "TOPLEFT", CROP_X + column * GLYPH_WIDTH, -(CROP_Y + row * GLYPH_HEIGHT)
      )
      texture:SetTexture(ATLAS_PATH, "CLAMP", "CLAMP", "NEAREST")
      texture:SetTexCoord(0, 1, 0.5 / ATLAS_HEIGHT, 1.5 / ATLAS_HEIGHT)
      texture:Show()
      cells[row * BYTES_PER_ROW + column + 1] = texture
    end
  end
  surface:Show()
  renderMetrics.constructionSeconds = (debugprofilestop() - started) / 1000
  renderMetrics.textureCount = CAPACITY
  renderMetrics.effectiveScale = effective
  renderMetrics.cellSize = { 2, 2 }
end

local function setGlyph(texture, value)
  local top = (value * GLYPH_HEIGHT + 0.5) / ATLAS_HEIGHT
  local bottom = (value * GLYPH_HEIGHT + GLYPH_HEIGHT - 0.5) / ATLAS_HEIGHT
  texture:SetTexCoord(0, 1, top, bottom)
end

local function updateSurface(bytes)
  frameBytes = bytes
  for row = 0, HEIGHT - 1 do
    for column = 0, BYTES_PER_ROW - 1 do
      local byte = string.byte(bytes, row * BYTES_PER_ROW + column + 1)
      if byte == nil then error("Crowley telemetry frame is shorter than its fixed capacity") end
      setGlyph(cells[row * BYTES_PER_ROW + column + 1], byte)
    end
  end
end

local function countLuaMemory()
  local ok, value = pcall(function() return collectgarbage("count") end)
  if not ok or type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge or value < 0 then return nil end
  return value
end

local function setLuaHeap(beforeMemory, afterMemory)
  if beforeMemory == nil or afterMemory == nil then
    lastLuaHeap = { method = "collectgarbage_count", available = false, beforeKiB = 0, afterKiB = 0, netKiB = 0 }
  else
    lastLuaHeap = {
      method = "collectgarbage_count", available = true,
      beforeKiB = beforeMemory, afterKiB = afterMemory, netKiB = afterMemory - beforeMemory,
    }
  end
  renderMetrics.luaHeap = copy(lastLuaHeap)
end

local function setNativeState(phase, ordinal)
  nativePhase, nativeOrdinal = phase, ordinal
  renderMetrics.nativePhase, renderMetrics.nativeOrdinal = phase, ordinal
end

function Agent.Publish()
  renderMetrics.luaHeap = copy(lastLuaHeap)
  renderMetrics.nativePhase, renderMetrics.nativeOrdinal = nativePhase, nativeOrdinal
  local beforeMemory = countLuaMemory()
  local result, errorText
  local ok, failure = pcall(function()
    local started = debugprofilestop()
    local snapshot = Agent.Snapshot()
    local json = C_EncodingUtil.SerializeJSON(snapshot)
    local payload = C_EncodingUtil.CompressString(json, Enum.CompressionMethod.Deflate)
    if #payload < 1 or #payload > 2000 then error("Crowley telemetry payload exceeds 2000 bytes") end
    local header = "CRS1" .. string.char(1, 1, WIDTH, HEIGHT) .. string.char(#payload % 256, math.floor(#payload / 256)) ..
      u32(snapshot.sequence) .. u32(snapshot.wallTime) .. u32(snapshot.uptimeMs)
    local checksum = u32(crc32(header .. payload))
    local bytes = header .. checksum .. payload .. string.rep(string.char(0), CAPACITY - #header - #checksum - #payload)
    updateSurface(bytes)
    local elapsedMs = debugprofilestop() - started
    local afterMemory = countLuaMemory()
    setLuaHeap(beforeMemory, afterMemory)
    renderMetrics.updateCount = renderMetrics.updateCount + 1
    updateSamples[((renderMetrics.updateCount - 1) % 100) + 1] = elapsedMs
    if renderMetrics.updateCount >= 100 then
      local ordered = {}
      for index = 1, 100 do ordered[index] = updateSamples[index] end
      table.sort(ordered)
      renderMetrics.updateP99Ms = ordered[math.max(1, math.ceil(#ordered * 0.99))]
    end
    result = copy(snapshot)
  end)
  if not ok then errorText = failure end
  if errorText then error(errorText) end
  return result
end

function Agent.FrameBytes() return frameBytes end
function Agent.Surface() return surface end

function Agent.NativeState()
  return { phase = nativePhase, ordinal = nativeOrdinal }
end

local function scheduleMeasurementStep(token)
  C_Timer.After(1, function()
    if token ~= measurementToken or nativePhase ~= "updates" then return end
    nativeOrdinal = nativeOrdinal + 1
    if nativeOrdinal >= 100 then
      setNativeState("held", 100)
      safePublish()
      return
    end
    setNativeState("updates", nativeOrdinal)
    safePublish()
    scheduleMeasurementStep(token)
  end)
end

function Agent.Hold()
  if nativePhase ~= "normal" then return false, "agent_not_normal" end
  measurementToken = measurementToken + 1
  elapsed = 0
  setNativeState("held", 0)
  safePublish()
  return true
end

function Agent.Measure()
  if nativePhase ~= "held" or nativeOrdinal ~= 0 then return false, "agent_measure_requires_held0" end
  measurementToken = measurementToken + 1
  local token = measurementToken
  nativeOrdinal = 1
  setNativeState("updates", 1)
  safePublish()
  scheduleMeasurementStep(token)
  return true
end

function Agent.Resume()
  if nativePhase ~= "held" then return false, "agent_resume_requires_held" end
  measurementToken = measurementToken + 1
  elapsed = 0
  setNativeState("normal", 0)
  safePublish()
  return true
end

safePublish = function()
  local ok, errorText = pcall(Agent.Publish)
  if ok then
    lastPublishError = nil
  elseif ns.Print then
    local text = tostring(errorText)
    if text ~= lastPublishError then
      lastPublishError = text
      ns.Print("agent telemetry blocked: " .. text)
    end
  end
end

if not surface then createSurface() end
surface:SetScript("OnUpdate", function(_, delta)
  if nativePhase ~= "normal" then return end
  elapsed = elapsed + (delta or 0)
  if elapsed >= 1 then elapsed = 0 safePublish() end
end)

ns.On("ADDON_LOADED", function(_, name)
  if name == "Crowley" and ns.db then
    ns.db.agentLastSaved = ns.db.agentLastSaved or {
      memoryUid = "", finishedAt = 0, planned = 0, attempted = 0, failures = 0, rows = 0,
    }
    safePublish()
  end
end)
