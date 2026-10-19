"""End-to-end fake-clock session lifecycle through the real socket dispatcher."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import threading
import time
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image

from crowley.core.luawriter import render_assignment
from crowley.core.scanformat import encode_json_payload
from crowley.core.watchlist import load_catalog
from crowley.session import Controller, ControllerState, DesktopDriver, SessionConfig, SessionDaemon
from crowley.session.calibration import (
    LinuxProcStatusVmHwmReset5,
    NativeCalibrationRunner,
    NativeMemoryMeasurement,
    NativeMemoryResetRecord,
    OwnedWindow,
    XTestInputProfile,
)
from crowley.session.cli import _socket_request, serve
from crowley.session.daemon import _NativeObservationDiagnostic
from crowley.session.decoder import Sample
from crowley.session.driver import (
    DriverError,
    DriverProfile,
    WindowIdentity,
    X11Backend,
)
from crowley.session.evidence import EvidenceError, read_stable_saved_scan
from crowley.session.input_events import EventClass, XI2Event
from crowley.session.journal import DEFAULT_STATE, Journal, JournalError
from crowley.session.model import ModelDecision, ModelObservation
from crowley.session.protocol import decode_frame
from tests.test_session_input_tool import fixture_input_tool

from .wow_harness import Auction, WowClient

_REVERSE_BITS = bytes(int(f"{value:08b}"[::-1], 2) for value in range(256))


class _FixtureNativeMemoryMeter(LinuxProcStatusVmHwmReset5):
    """Deterministic reset5 contract for the headless daemon lifecycle."""

    def __init__(self, identity: WindowIdentity) -> None:
        self.pid = identity.pid
        self.process_start = identity.process_start
        self.process_executable = identity.executable
        self.identity_fingerprint = identity.fingerprint
        self.expected_uid = os.getuid()
        self.kernel_release = os.uname().release
        self._pending = None

    def begin_window(self, phase: str, ordinal: int, *, limit_bytes: int, before_reset):
        if self._pending is not None:
            raise AssertionError("fixture reset5 window was not finished")
        record = NativeMemoryResetRecord(
            method=self.METHOD,
            phase=phase,
            ordinal=ordinal,
            pid=self.pid,
            process_start=self.process_start,
            process_executable=self.process_executable,
            identity_fingerprint=self.identity_fingerprint,
            uid=self.expected_uid,
            kernel_release=self.kernel_release,
            historical_hwm_bytes=0,
            rss_before_reset_bytes=0,
            limit_bytes=limit_bytes,
        )
        before_reset(record)
        self._pending = SimpleNamespace(
            meter=self,
            method=self.METHOD,
            phase=phase,
            ordinal=ordinal,
            pid=self.pid,
            process_start=self.process_start,
            process_executable=self.process_executable,
            identity_fingerprint=self.identity_fingerprint,
            uid=self.expected_uid,
            kernel_release=self.kernel_release,
            historical_hwm_bytes=0,
            rss_before_reset_bytes=0,
            reset_completed_monotonic=time.monotonic(),
            post_reset_hwm_bytes=0,
            rss_after_reset_bytes=0,
            limit_bytes=limit_bytes,
        )
        return self._pending

    def finish_window(
        self,
        pending,
        *,
        workload_start_monotonic: float,
        workload_end_monotonic: float,
        workload_start_ordinal: int,
        workload_end_ordinal: int,
    ) -> NativeMemoryMeasurement:
        if pending is not self._pending:
            raise AssertionError("fixture reset5 token was replayed")
        self._pending = None
        return NativeMemoryMeasurement(
            method=self.METHOD,
            phase=pending.phase,
            ordinal=pending.ordinal,
            pid=self.pid,
            process_start=self.process_start,
            process_executable=self.process_executable,
            identity_fingerprint=self.identity_fingerprint,
            uid=self.expected_uid,
            kernel_release=self.kernel_release,
            historical_hwm_bytes=0,
            rss_before_reset_bytes=0,
            reset_completed_monotonic=pending.reset_completed_monotonic,
            post_reset_hwm_bytes=0,
            rss_after_reset_bytes=0,
            workload_start_monotonic=workload_start_monotonic,
            workload_end_monotonic=workload_end_monotonic,
            workload_start_ordinal=workload_start_ordinal,
            workload_end_ordinal=workload_end_ordinal,
            final_hwm_bytes=0,
            final_rss_bytes=0,
            growth_bytes=0,
            limit_bytes=pending.limit_bytes,
        )


def _snapshot(wall: int, *, boot: str = "boot-1", sequence: int = 1) -> dict:
    return {
        "schema": 3,
        "boot": boot,
        "sequence": sequence,
        "wallTime": wall,
        "uptimeMs": sequence,
        "context": {
            "addonVersion": "0.2.0",
            "interface": 16001,
            "clientBuild": "70450",
            "character": "Arthur",
            "realm": "Classic Beta PvE 2",
            "playerFaction": "Alliance",
            "zone": "",
            "subzone": "",
            "locale": "enUS",
            "clientVersion": "1.60.1",
        },
        "house": {"key": "beta-normal-alliance", "source": "auto"},
        "plan": {
            "hash": load_catalog().scan_plan()["planHash"],
            "count": 428,
            "cadenceSeconds": 900,
            "sweepCapSeconds": 600,
            "initialPriceLevels": 20,
        },
        "ahOpen": True,
        "scanner": {
            "phase": "ready",
            "activeSweepId": "",
            "startedAt": 0,
            "dueAt": wall,
            "ordinal": 0,
            "planned": 428,
            "cursorItemID": 0,
            "scheduleFence": {"state": "inactive", "reason": "", "command": "/crowley session fence"},
        },
        "lastSaved": {
            "memoryUid": "",
            "finishedAt": 0,
            "planned": 0,
            "attempted": 0,
            "failures": 0,
            "rows": 0,
            "persistence": "unknown",
        },
        "pending": {"ids": [], "count": 0, "cap": 6, "blocked": False, "reason": ""},
        "loaded": {"ackedIds": [], "generatedAt": 0},
        "chatEdit": {"active": True, "focused": True, "text": ""},
        "motion": {
            "position": {"x": 100.25, "y": 200.5, "z": 30.75, "instance": 1},
            "facing": 1.25,
            "speed": 0,
            "combat": False,
            "deadOrGhost": False,
            "bindings": {
                "moveForward": "W",
                "moveBackward": "S",
                "strafeLeft": "A",
                "strafeRight": "D",
                "turnLeft": "Q",
            },
            "native": {
                "ctm": {
                    "accessor": "C_CVar.GetCVarBool",
                    "cvar": "autointeract",
                    "state": "disabled",
                    "reason": "",
                },
                "ground": {
                    "state": "grounded",
                    "falling": "false",
                    "flying": "false",
                    "swimming": "false",
                    "submerged": "false",
                    "mounted": "false",
                    "taxi": "false",
                    "reason": "",
                },
                "speedTuple": {
                    "current": 0,
                    "run": 0,
                    "flight": 0,
                    "swim": 0,
                    "unitStatus": "unverified",
                },
            },
        },
        "render": {
            "constructionSeconds": 0.001,
            "updateCount": 100,
            "updateP99Ms": 1,
            "textureCount": 16_384,
            "effectiveScale": 1,
            "cellSize": [2, 2],
            "luaHeap": {
                "method": "collectgarbage_count",
                "available": False,
                "beforeKiB": 0,
                "afterKiB": 0,
                "netKiB": 0,
            },
            "nativePhase": "normal",
            "nativeOrdinal": 0,
        },
    }


def _saved_fixture(path: Path, uid: str, started: int) -> None:
    plan = load_catalog().scan_plan()
    observations: dict[str, dict] = {}
    for ordinal, item_id in enumerate(plan["itemIDs"], 1):
        observation = {
            "itemID": item_id,
            "ordinal": ordinal,
            "kind": "commodity",
            "query": {"kind": "queried", "startedAt": started, "finishedAt": started + 1},
            "coverage": "full",
            "sourceComplete": True,
            "cutoff": {"kind": "unbounded"},
            "higherPriceWitness": {"kind": "unknown"},
            "reasonCode": "ok",
            "rowCount": 1,
            "rows": {
                "row:1": {
                    "resultID": ordinal,
                    "itemID": item_id,
                    "itemKey": str(item_id),
                    "rawItemKey": {
                        "itemID": item_id,
                        "itemLevel": 0,
                        "itemSuffix": 0,
                        "battlePetSpeciesID": 0,
                        "bonusIDs": [],
                    },
                    "link": {"kind": "unknown"},
                    "quantity": 1,
                    "price": {"kind": "unit", "copper": 100 + ordinal},
                    "unitPrice": {"numerator": 100 + ordinal, "denominator": 1},
                    "owners": {
                        "names": [],
                        "totalNumberOfOwners": 0,
                        "containsOwnerItem": False,
                        "containsAccountItem": False,
                        "identityKind": "grouped",
                    },
                    "timeLeft": {"kind": "unknown"},
                }
            },
        }
        observations[str(item_id)] = observation
    first_owned_id = plan["itemIDs"][0]
    owned_row = {
        "auctionID": 1,
        "itemID": first_owned_id,
        "itemKey": str(first_owned_id),
        "rawItemKey": {
            "itemID": first_owned_id,
            "itemLevel": 0,
            "itemSuffix": 0,
            "battlePetSpeciesID": 0,
            "bonusIDs": [],
        },
        "itemLink": f"item:{first_owned_id}:0:0:0:0:0:0:0:0:0:0:0:0",
        "quantity": 1,
        "buyout": {"kind": "known", "copper": 1},
        "status": "active",
    }
    payload = {
        "planHash": plan["planHash"],
        "planJSON": plan["planJSON"],
        "observations": observations,
        "owned": {
            "status": "full",
            "query": {"kind": "queried", "startedAt": started, "finishedAt": started + 1},
            "reasonCode": "ok",
            "rowCount": 1,
            "rows": {"1": owned_row},
        },
    }
    envelope = {
        "id": uid,
        "format": 2,
        "startedAt": started,
        "finishedAt": started + 2,
        "house": {
            "region": "beta",
            "ruleset": "normal",
            "faction": "alliance",
            "source": "auto",
            "key": "beta-normal-alliance",
        },
        "context": {
            "character": "Arthur",
            "realm": "Classic Beta PvE 2",
            "playerFaction": "Alliance",
            "zone": "",
            "subzone": "",
            "locale": "enUS",
            "clientVersion": "1.60.1",
            "clientBuild": "70450",
            "interface": 16001,
            "addonVersion": "0.2.0",
        },
        "numRows": 428,
        "numObservations": 428,
        "payload": encode_json_payload(payload),
    }
    path.write_text(render_assignment("CrowleyDB", {"scans": {uid: envelope}, "sweeps": {}}, "fixture"))


def _attach_recording_anchor_provider(driver: DesktopDriver, root: Path) -> None:
    """Supply one complete, sealed visual record immediately before each action."""

    scenes = {
        "dismiss_disconnect": "disconnect_dialog",
        "reconnect_game": "game_client",
        "select_arthur": "character_select",
        "enter_world": "character_select",
        "open_ah": "world",
        "logout": "world",
    }
    state = {"generation": 0, "sequence": 0}

    def provider(identity: WindowIdentity, action: str):
        state["sequence"] += 1
        capture = root / f"anchor-{action}-{state['sequence']}.capture"
        capture.write_bytes(f"owned visual capture:{action}:{state['sequence']}".encode())
        captured_at = driver._clock()
        return driver.build_measured_anchor(
            action=action,
            x=80,
            y=60,
            capture_path=capture,
            capture_id=hashlib.sha256(capture.read_bytes()).hexdigest(),
            capture_sequence=state["sequence"],
            capture_monotonic=captured_at,
            scene=scenes[action],
            bounds=(40, 30, 80, 60),
            target_xid=identity.child_xid,
            target_ancestry=(identity.child_xid,),
            generation=state["generation"],
            facts=(("fixture", "owned-recording-backend"),),
        )

    driver.measured_anchor_provider = provider
    original_run = driver.run

    def run(name: str, generation: int, **kwargs: object) -> None:
        if name in scenes:
            state["generation"] = generation
            driver.measure_pointer_anchor(name, generation=generation)
        if name == "submit_command" and "precondition" not in kwargs:
            expected = driver.resolve_identity().fingerprint
            kwargs["precondition"] = lambda identity: identity.fingerprint == expected
        original_run(name, generation, **kwargs)

    driver.run = run  # type: ignore[method-assign]


class LifecycleBackend(X11Backend):
    def __init__(self, root: Path):
        super().__init__(
            DriverProfile(xauthority="/tmp/test-Xauthority", wine_prefix="/tmp/test-wine-prefix"),
            input_tool=fixture_input_tool(root / "tool"),
        )
        self.root = root
        self.events: list[dict[str, object]] = []
        self.capture_paths: list[Path] = []
        self.command_buffer = ""
        self.current = _snapshot(1000)
        self.captures = 0
        self.cycle = 0
        self.uid = ""
        self.boot_number = 1
        self.character_select = False
        self.saved_reload_done = False
        self.agent_client: WowClient | None = None
        self.lifecycle_agent = False
        self.lifecycle_sequence = 0
        self.agent_load_requested = False
        self.agent_commands: list[tuple[str, int]] = []
        self.agent_last_capture_sequence = 0
        self.virtual_clock: object | None = None
        self.agent_trace: list[tuple[int, str, int, float]] = []
        self.runtime_observer: _FixtureInputObserver | None = None
        self.runtime_driver: DesktopDriver | None = None
        self.runtime_event_number = 1000
        self.runtime_timestamp = 1000
        self.identity = WindowIdentity(
            1,
            os.getpid(),
            "test",
            "World of Warcraft",
            "wowb.exe",
            2,
            (0, 0, 1928, 1092),
            (0, 0, 1920, 1080),
            1,
            "test",
            ":0",
            "test",
            0x1,
            1,
            frozenset({1, 2}),
        )

    def xtest_input_profile(self, hierarchy, **_kwargs):
        """Return the sealed native fixture profile without querying host X11."""

        return XTestInputProfile(
            4,
            2,
            "XTEST pointer",
            3,
            ((0, "Rel X", "relative", -1.0, -1.0, 0), (1, "Rel Y", "relative", -1.0, -1.0, 0)),
            1,
            1,
            (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
            0x374,
            (0, 0, 1920, 1080),
            tuple(hierarchy),
        )

    def _run(self, args, **_kwargs):
        del args
        raise DriverError("unmodeled native fixture command refused locally")

    def resolve_identity(
        self,
        *,
        require_foreground: bool = True,
        deadline_monotonic: float | None = None,
    ) -> WindowIdentity:
        del require_foreground
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            raise DriverError("fixture identity query exceeded its deadline")
        return self.identity

    def verify_identity(self, identity: WindowIdentity) -> WindowIdentity:
        if identity.fingerprint != self.identity.fingerprint:
            raise DriverError("fixture identity changed")
        return self.identity

    def calibration_focus(self, window_id: str, **kwargs: object) -> None:
        self.events.append({"name": "calibration_focus", "window": window_id, **kwargs})

    def activate_generation(self, generation: int) -> None:
        self.events.append({"name": "activate_generation", "generation": generation})

    def observe_keymap(self, *, deadline_monotonic: float | None = None) -> dict[str, int]:
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            raise DriverError("fixture keymap query exceeded its deadline")
        return {
            "Return": 36,
            "Escape": 9,
            "Control_L": 37,
            "slash": 47,
            "space": 65,
            **{character: index for index, character in enumerate("abcdefghijklmnopqrstuvwxyz", 10)},
        }

    def capture(
        self,
        path: Path,
        *,
        identity: WindowIdentity | None = None,
        deadline_monotonic: float | None = None,
    ) -> WindowIdentity:
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            raise DriverError("fixture capture exceeded its deadline")
        self.captures += 1
        self.capture_paths.append(path)
        self._load_real_agent()
        if self.lifecycle_agent and self.current["scanner"]["phase"] in {"item", "owned"} and not self.uid:
            self.uid = f"uid-{self.cycle}"
            self.current["lastSaved"] = {
                "memoryUid": self.uid,
                "finishedAt": self.current["wallTime"] + 2,
                "planned": 428,
                "attempted": 428,
                "failures": 0,
                "rows": 428,
                "persistence": "unknown",
            }
            _saved_fixture(self.root / "Crowley.lua", self.uid, self.current["scanner"]["startedAt"])
            companion = {"uploaded": {self.uid: self.current["wallTime"] + 3}, "probes": []}
            (self.root / "companion.json").write_text(json.dumps(companion))
            data = {
                "generatedAt": self.current["wallTime"],
                "ackedScans": [self.uid],
                "scanPlan": load_catalog().scan_plan(),
                "shoppingLists": [],
            }
            (self.root / "Data.lua").write_text(render_assignment("CROWLEY_DATA", data, "fixture"))
        if self.agent_client is None:
            # Let bounded daemon waits progress while the real addon is
            # absent.  This is the same virtual monotonic source injected
            # into the runner, so the negative no-Agent interval cannot hang
            # forever behind a wall-clock sleep.
            advance = getattr(self.virtual_clock, "advance", None)
            if callable(advance):
                advance(1.0)
            Image.new("RGB", (1920, 1080), (17, 17, 17)).save(path, compress_level=0)
            return self.identity
        if self.lifecycle_agent:
            self._publish_lifecycle_agent()
        else:
            self._service_agent_operator()
        raw = self.agent_client.agent_frame
        frame = decode_frame(raw, plan_item_ids=load_catalog().scan_plan()["itemIDs"])
        render = frame.snapshot["render"]
        previous_sequence = self.agent_last_capture_sequence
        # Agent's scheduled one-hertz callbacks are driven by the fixture's
        # explicit clock, but publication is scheduled only after a capture
        # completes.  The next daemon capture-start clock read consumes that
        # schedule, so capture timestamps and publication cadence share one
        # coherent namespace.
        if (
            frame.sequence == self.agent_last_capture_sequence
            and render["nativePhase"] == "updates"
            and render["nativeOrdinal"] < 100
        ):
            schedule = (
                getattr(self.virtual_clock, "schedule_native_publication", None)
                if getattr(self.virtual_clock, "native_schedule", False)
                else None
            )
            if callable(schedule):
                raise AssertionError("native publication was not consumed between captures")
            else:
                advance = getattr(self.virtual_clock, "advance", None)
                if not callable(advance):
                    raise AssertionError("runtime fixture requires a virtual clock for native cadence")
                advance(1.0)
                self.agent_client.advance_with_timers(1)
            raw = self.agent_client.agent_frame
            frame = decode_frame(raw, plan_item_ids=load_catalog().scan_plan()["itemIDs"])
        if self.lifecycle_agent:
            # The lifecycle producer is exercised against the daemon's
            # wall-clock visual path.  Keep the injected driver clock in that
            # same namespace while preserving the explicit virtual cadence
            # used by the native handshake above.
            self.virtual_clock.value = time.monotonic()
        elif frame.sequence != previous_sequence:
            advance = getattr(self.virtual_clock, "advance", None)
            if not callable(advance):
                raise AssertionError("runtime fixture requires a virtual clock for native timestamps")
            advance(0.01)
        self.agent_last_capture_sequence = frame.sequence
        now = getattr(self.virtual_clock, "value", time.monotonic())
        render = frame.snapshot["render"]
        self.agent_trace.append((frame.sequence, render["nativePhase"], render["nativeOrdinal"], float(now)))
        schedule = (
            getattr(self.virtual_clock, "schedule_native_publication", None)
            if getattr(self.virtual_clock, "native_schedule", False)
            else None
        )
        if callable(schedule) and render["nativePhase"] == "updates" and render["nativeOrdinal"] < 100:
            schedule(1.0, self.agent_client.advance_with_timers)
        # The protocol packs each row LSB-first while Pillow's mode-1 image
        # stores rows MSB-first.  Reverse each row, scale the actual
        # AgentFrameBytes cell surface, and paste it into the verified desktop
        # crop.  This keeps the fixture production-decoded without a Python
        # pixel loop on every one-hertz update.
        packed_cells = b"".join(raw[row * 16 : (row + 1) * 16].translate(_REVERSE_BITS) for row in range(128))
        cells = Image.frombytes("1", (128, 128), packed_cells)
        crop = cells.resize((256, 256), Image.Resampling.NEAREST).convert("RGB")
        image = Image.new("RGB", (1920, 1080), (0, 0, 0))
        image.paste(crop, (80, 48))
        image.save(path, compress_level=0)
        return self.identity

    def _load_real_agent(self) -> None:
        if not self.agent_load_requested or self.agent_client is not None:
            return
        self.agent_load_requested = False
        self.agent_client = WowClient(
            faction="Alliance",
            realm="Classic Beta PvE 2",
            zone="Stormwind",
            current_region=110,
            current_region_name="beta",
        )
        self.agent_client.lua.globals().UnitName = lambda _unit: "Arthur"
        self.agent_client.set_canonical_plan()
        self.agent_client.set_auctions(
            [
                Auction(itemID=item_id, name=f"item-{item_id}", count=1, buyout=101, isCommodity=True)
                for item_id in load_catalog().scan_plan()["itemIDs"]
            ]
        )
        self.agent_client.lua.globals()._now = self.current["wallTime"]
        self.agent_client.login()
        # Keep the first production Agent frame aligned with the backend's
        # initial world observation.  Assigning the addon-owned flag avoids
        # firing AUCTION_HOUSE_SHOW, whose production handler would also
        # schedule a real scanner run before the controller's command.
        self.agent_client.ns.ahOpen = True
        self.agent_client.set_chat_edit(active=True, focused=True)
        self.agent_client.publish_agent()

    def use_lifecycle_agent(self) -> None:
        """Switch the post-calibration lifecycle to production wire encoding."""

        client = WowClient(
            faction="Alliance",
            realm="Classic Beta PvE 2",
            zone="Stormwind",
            current_region=110,
            current_region_name="beta",
        )
        client.lua.globals().UnitName = lambda _unit: "Arthur"
        client.set_canonical_plan()
        client.login()
        client.set_chat_edit(active=True, focused=True)
        self.agent_client = client
        self.lifecycle_agent = True
        self.lifecycle_sequence = 0
        self._publish_lifecycle_agent()

    def _publish_lifecycle_agent(self) -> None:
        if self.agent_client is None:
            return
        self.lifecycle_sequence += 1
        value = json.loads(json.dumps(self.current))
        value["sequence"] = self.lifecycle_sequence
        value["uptimeMs"] = self.lifecycle_sequence
        value["render"] = {
            "constructionSeconds": 0.001,
            "updateCount": 100,
            "updateP99Ms": 1,
            "textureCount": 16_384,
            "effectiveScale": 1,
            "cellSize": [2, 2],
            "luaHeap": {
                "method": "collectgarbage_count",
                "available": False,
                "beforeKiB": 0,
                "afterKiB": 0,
                "netKiB": 0,
            },
            "nativePhase": "normal",
            "nativeOrdinal": 0,
        }
        client = self.agent_client
        client.ns.Agent.Snapshot = lambda: client._to_lua(value)
        client.publish_agent()

    def _restart_real_agent(self) -> None:
        """Give the production Agent a new boot while retaining durable scan facts."""

        old = self.agent_client
        if old is None:
            return
        client = WowClient(
            faction="Alliance",
            realm="Classic Beta PvE 2",
            zone="Stormwind",
            current_region=110,
            current_region_name="beta",
        )
        client.lua.globals().UnitName = lambda _unit: "Arthur"
        client.set_canonical_plan()
        client.set_auctions(
            [
                Auction(itemID=item_id, name=f"item-{item_id}", count=1, buyout=101, isCommodity=True)
                for item_id in load_catalog().scan_plan()["itemIDs"]
            ]
        )
        client.lua.globals()._now = self.current["wallTime"]
        client.login()
        client.ns.ahOpen = bool(self.current["ahOpen"])
        client.set_chat_edit(active=True, focused=True)
        db = client.lua.globals().CrowleyDB
        db.agentLastSaved = client._to_lua(self.current["lastSaved"])
        scanner = self.current["scanner"]
        db.lastSweepStart = int(scanner.get("dueAt", self.current["wallTime"])) - 900
        if self.uid:
            db.scans[self.uid] = client._to_lua({"id": self.uid})
        client.lua.globals().CROWLEY_DATA.ackedScans = client._to_lua(self.current["loaded"]["ackedIds"])
        client.lua.globals().CROWLEY_DATA.generatedAt = self.current["loaded"].get("generatedAt", 0)
        client.publish_agent()
        self.agent_client = client

    def _service_agent_operator(self) -> None:
        if self.agent_client is None:
            return
        if not self.agent_commands:
            return
        command, remaining = self.agent_commands[0]
        if remaining > 0:
            self.agent_commands[0] = (command, remaining - 1)
            return
        self.agent_commands.pop(0)
        self.agent_client.slash(f"agent {command}")

    def load_agent(self) -> None:
        self.agent_load_requested = True

    def request_agent_command(self, command: str, *, delayed_captures: int = 3) -> None:
        self.agent_commands.append((command, delayed_captures))

    def _runtime_event(
        self,
        event_class: EventClass,
        *,
        master: int,
        source: int,
        detail: int,
        child: int | None = None,
        root_coordinates: tuple[float, float] | None = None,
        event_coordinates: tuple[float, float] | None = None,
    ) -> XI2Event:
        event = _fixture_event(
            self.runtime_event_number,
            event_class,
            master,
            source,
            self.runtime_timestamp,
            detail,
            self.identity.child_xid if child is None and not event_class.name.startswith("RAW_") else child,
            root_xy=root_coordinates,
            event_xy=event_coordinates,
        )
        self.runtime_event_number += 1
        self.runtime_timestamp += 1
        return event

    def _emit_runtime_key_operation(self, operation: str, payload: str = "") -> None:
        observer = self.runtime_observer
        driver = self.runtime_driver
        evidence = getattr(driver, "_input_evidence", None)
        if observer is None or driver is None or evidence is None:
            raise AssertionError("runtime fixture has no owned observer/input evidence")
        for phase, _keysym, detail, _modifiers, _effective in driver._keyboard_operation_facts(
            operation, payload, evidence
        ):
            raw_class = EventClass.RAW_KEY_PRESS if phase == "press" else EventClass.RAW_KEY_RELEASE
            delivered_class = EventClass.KEY_PRESS if phase == "press" else EventClass.KEY_RELEASE
            observer._add(self._runtime_event(raw_class, master=3, source=5, detail=detail, child=None))
            observer._add(
                self._runtime_event(
                    delivered_class, master=5, source=5, detail=detail, child=self.identity.child_xid
                )
            )

    def _emit_runtime_pointer_click(
        self, button: int, *, coordinates: tuple[tuple[float, float], tuple[float, float]]
    ) -> None:
        observer = self.runtime_observer
        if observer is None:
            raise AssertionError("runtime fixture has no owned observer")
        observer._add(
            self._runtime_event(EventClass.RAW_BUTTON_PRESS, master=2, source=4, detail=button, child=None)
        )
        observer._add(
            self._runtime_event(
                EventClass.BUTTON_PRESS,
                master=4,
                source=4,
                detail=button,
                child=self.identity.child_xid,
                root_coordinates=coordinates[0],
                event_coordinates=coordinates[1],
            )
        )
        observer._add(
            self._runtime_event(EventClass.RAW_BUTTON_RELEASE, master=2, source=4, detail=button, child=None)
        )
        observer._add(
            self._runtime_event(
                EventClass.BUTTON_RELEASE,
                master=4,
                source=4,
                detail=button,
                child=self.identity.child_xid,
                root_coordinates=coordinates[0],
                event_coordinates=coordinates[1],
            )
        )

    def action(self, name: str, **kwargs) -> None:
        command = self.command_buffer if name == "submit_command" else ""
        self.events.append({"name": name, **kwargs})
        if name == "type_allowlisted_command":
            self._emit_runtime_key_operation("type_allowlisted_command", str(kwargs["command"]))
        elif name == "open_chat":
            self._emit_runtime_key_operation("open_chat")
        elif name == "submit_command":
            self._emit_runtime_key_operation("submit_command")
        elif name == "open_ah":
            click = kwargs.get("_click_plan")
            point = getattr(click, "point", None)
            if point is None:
                anchor = getattr(self.runtime_driver, "_measured_anchors", {}).get("open_ah")
                point = SimpleNamespace(x=getattr(anchor, "x", -1), y=getattr(anchor, "y", -1))
            if int(point.x) < 0 or int(point.y) < 0:
                raise AssertionError("runtime pointer action has no measured click point")
            client_x, client_y = int(point.x), int(point.y)
            left, top, _width, _height = self.identity.child_geometry
            self._emit_runtime_pointer_click(
                3,
                coordinates=(
                    (float(left + client_x), float(top + client_y)),
                    (float(client_x), float(client_y)),
                ),
            )
        if name == "type_allowlisted_command":
            self.command_buffer = str(kwargs["command"])
            self.current["chatEdit"]["text"] = self.command_buffer
            if self.agent_client is not None:
                self.agent_client.set_chat_edit(active=True, focused=True, text=self.command_buffer)
                if self.lifecycle_agent:
                    self._publish_lifecycle_agent()
                else:
                    self.agent_client.publish_agent()
        elif name == "submit_command":
            self.command_buffer = ""
            self.current["chatEdit"]["text"] = ""
            if command == "/crowley scan":
                self.cycle += 1
                started = self.current["wallTime"]
                self.uid = ""
                self.saved_reload_done = False
                self.current["scanner"] = {
                    "phase": "item",
                    "activeSweepId": "",
                    "startedAt": started,
                    "dueAt": started + 900,
                    "ordinal": 1,
                    "planned": 428,
                    "cursorItemID": load_catalog().scan_plan()["itemIDs"][0],
                    "scheduleFence": {"state": "inactive", "reason": "", "command": "/crowley session fence"},
                }
                if self.agent_client is not None and not self.lifecycle_agent:
                    self.agent_client.lua.globals()._now = started
                    self.agent_client.ns.ahOpen = True
                    self.agent_client.slash("scan")
                    self.agent_client.set_chat_edit(active=True, focused=True)
                    self.agent_client.publish_agent()
                elif self.lifecycle_agent:
                    self._publish_lifecycle_agent()
            elif command == "/crowley session fence":
                scanner = self.current["scanner"]
                if scanner["phase"] in {"ready", "scheduled"} and not scanner["activeSweepId"]:
                    scanner["scheduleFence"] = {
                        "state": "armed",
                        "reason": "",
                        "command": "/crowley session fence",
                    }
                if self.agent_client is not None and not self.lifecycle_agent:
                    self.agent_client.lua.globals()._now = self.current["wallTime"]
                    self.agent_client.slash("session fence")
                    self.agent_client.set_chat_edit(active=True, focused=True)
                    self.agent_client.publish_agent()
                elif self.lifecycle_agent:
                    self._publish_lifecycle_agent()
                else:
                    scanner["scheduleFence"] = {
                        "state": "refused",
                        "reason": "scan_active",
                        "command": "/crowley session fence",
                    }
            elif command == "/reload":
                self.boot_number += 1
                self.current["boot"] = f"boot-{self.boot_number}"
                # Advance the fake addon clock across the companion upload
                # before the controller records either publication witness.
                self.current["wallTime"] += 3
                if self.saved_reload_done and self.uid:
                    self.advance_ack()
                    self.current["ahOpen"] = False
                else:
                    self.saved_reload_done = True
                if self.agent_client is not None and not self.lifecycle_agent:
                    self._restart_real_agent()
                if self.agent_client is not None and not self.lifecycle_agent:
                    self.agent_client.ns.ahOpen = bool(self.current["ahOpen"])
                    self.agent_client.set_chat_edit(active=True, focused=True)
                    self.agent_client.publish_agent()
                elif self.lifecycle_agent:
                    self._publish_lifecycle_agent()
            elif command == "/logout":
                self.character_select = True
                self.current["context"]["character"] = ""
                self.current["context"]["realm"] = ""
                (self.root / "Crowley.lua").write_text(
                    render_assignment("CrowleyDB", {"scans": {}, "sweeps": {}}, "logout flush")
                )
                empty_data = {
                    "generatedAt": self.current["wallTime"],
                    "ackedScans": [],
                    "scanPlan": load_catalog().scan_plan(),
                    "shoppingLists": [],
                }
                (self.root / "Data.lua").write_text(
                    render_assignment("CROWLEY_DATA", empty_data, "logout flush")
                )
                if self.agent_client is not None and not self.lifecycle_agent:
                    self.agent_client.set_chat_edit(active=True, focused=True)
                    self.agent_client.publish_agent()
                elif self.lifecycle_agent:
                    self._publish_lifecycle_agent()
        elif name == "open_chat":
            if self.agent_client is not None:
                self.agent_client.set_chat_edit(active=True, focused=True)
                if self.lifecycle_agent:
                    self._publish_lifecycle_agent()
                else:
                    self.agent_client.publish_agent()
        elif name == "open_ah":
            self.current["ahOpen"] = True
            self.current["wallTime"] = self.cycle * 900 + 1000
            self.current["scanner"] = {
                "phase": "ready",
                "activeSweepId": "",
                "startedAt": 0,
                "dueAt": self.current["wallTime"],
                "ordinal": 0,
                "planned": 428,
                "cursorItemID": 0,
                "scheduleFence": {"state": "inactive", "reason": "", "command": "/crowley session fence"},
            }
            if self.agent_client is not None and not self.lifecycle_agent:
                self.agent_client.ns.ahOpen = True
                self.agent_client.set_chat_edit(active=True, focused=True)
                self.agent_client.publish_agent()
            elif self.lifecycle_agent:
                self._publish_lifecycle_agent()

    def advance_ack(self) -> None:
        if self.uid:
            data = {
                "generatedAt": self.current["wallTime"],
                "ackedScans": [self.uid],
                "scanPlan": load_catalog().scan_plan(),
                "shoppingLists": [],
            }
            (self.root / "Data.lua").write_text(render_assignment("CROWLEY_DATA", data, "fixture"))
            if self.agent_client is not None:
                self.agent_client.lua.globals().CROWLEY_DATA.ackedScans = self.agent_client._to_lua(
                    [self.uid]
                )
                self.agent_client.lua.globals().CROWLEY_DATA.generatedAt = self.current["wallTime"]
            self.current["loaded"]["ackedIds"] = [self.uid]
            self.current["loaded"]["generatedAt"] = self.current["wallTime"]
            self.current["pending"]["ids"] = []
            self.current["pending"]["count"] = 0
            self.current["scanner"] = {
                "phase": "ready",
                "activeSweepId": "",
                "startedAt": 0,
                "dueAt": self.current["wallTime"] + 900,
                "ordinal": 0,
                "planned": 428,
                "cursorItemID": 0,
                "scheduleFence": {"state": "inactive", "reason": "", "command": "/crowley session fence"},
            }


def test_lifecycle_fixture_rejects_unmodeled_native_command_without_host_dispatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The lifecycle fixture must remain closed even if production gains a new query."""

    def host_dispatch(*_args: object, **_kwargs: object) -> None:
        pytest.fail("unmodeled native fixture command reached host dispatch")

    monkeypatch.setattr(X11Backend, "_run", host_dispatch)
    backend = LifecycleBackend(tmp_path)
    with pytest.raises(DriverError, match="unmodeled native fixture command"):
        backend._run(["xinput", "list", "--future-command"])


class _NativeProviderBackend(LifecycleBackend):
    """Real Agent producer with controls for one bounded provider wait."""

    def __init__(
        self,
        root: Path,
        *,
        load_after_captures: int | None = 0,
        publication_fault: str | None = None,
    ) -> None:
        super().__init__(root)
        self.load_after_captures = load_after_captures
        self.publication_fault = publication_fault
        self.capture_started = threading.Event()
        self.advance_cached_clock = False

    def capture(
        self,
        path: Path,
        *,
        identity: WindowIdentity | None = None,
        deadline_monotonic: float | None = None,
    ) -> WindowIdentity:
        if (
            self.agent_client is None
            and self.load_after_captures is not None
            and self.captures >= self.load_after_captures
        ):
            self.load_agent()
        self.capture_started.set()
        observed = super().capture(
            path,
            identity=identity,
            deadline_monotonic=deadline_monotonic,
        )
        if self.advance_cached_clock and self.agent_client is not None:
            advance = getattr(self.virtual_clock, "advance", None)
            if not callable(advance):
                raise AssertionError("native provider fixture requires a virtual clock")
            advance(1.0)
        return observed

    def _service_agent_operator(self) -> None:
        if self.agent_client is not None and self.publication_fault is not None:
            fault, self.publication_fault = self.publication_fault, None
            if fault == "wrong_phase":
                # A real operator transition publishes held/0 while construct
                # is still waiting for the required normal/0 frame.
                self.agent_client.slash("agent hold")
            elif fault == "skipped_ordinal":
                # Publish actual Agent bytes at updates/3, skipping the
                # requested updates/1 frame.
                self.agent_client.slash("agent hold")
                self.agent_client.slash("agent measure")
                self.agent_client.advance_with_timers(2)
            else:
                raise AssertionError(f"unknown native provider fixture fault {fault!r}")
        super()._service_agent_operator()


class _VirtualMonotonic:
    def __init__(self) -> None:
        self.value = time.monotonic()
        self.native_schedule = False
        self._pending_native_publication: tuple[float, object] | None = None

    def monotonic(self) -> float:
        if self.native_schedule and self._pending_native_publication is not None:
            seconds, callback = self._pending_native_publication
            self._pending_native_publication = None
            self.value += seconds
            if not callable(callback):
                raise AssertionError("native publication callback is not callable")
            callback(1)
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds

    def schedule_native_publication(self, seconds: float, callback: object) -> None:
        if not self.native_schedule:
            raise AssertionError("native publication scheduling is not enabled")
        if self._pending_native_publication is not None:
            raise AssertionError("native publication schedule was not consumed")
        self._pending_native_publication = (seconds, callback)


def test_native_capture_start_uses_driver_clock_domain(tmp_path: Path) -> None:
    """Native capture freshness remains comparable with the driver's clock."""

    virtual_clock = _VirtualMonotonic()
    virtual_clock.value = 123.0
    daemon = SessionDaemon.__new__(SessionDaemon)
    daemon._native_clock = virtual_clock.monotonic
    daemon.config = SimpleNamespace(journal=tmp_path / "session.json")
    daemon.capture_index = 0
    daemon._native_owned_capture_paths = set()
    daemon._native_bootstrap_lock = threading.RLock()
    capture_path = tmp_path / "capture.png"
    capture_path.write_bytes(b"capture")
    daemon._capture_client_crop_for_identity = lambda identity, deadline=None: capture_path
    daemon._remove_native_capture = lambda path: None
    daemon.driver = SimpleNamespace(
        decode_native_capture=lambda path, *, identity, decoder: Sample(
            "FRESH", None, 999.0, (0, 0, 256, 256), 1, identity.fingerprint
        )
    )
    identity = SimpleNamespace(fingerprint="client-1")

    sample, _digest, retained = daemon._capture_native_frame_with_capture(identity, object())

    assert sample.capture_monotonic == pytest.approx(123.0)
    assert retained.is_file()


def _runtime_daemon(
    root: Path,
    *,
    journal_changes: dict[str, object] | None = None,
    backend: LifecycleBackend | None = None,
    lease_path: Path | None = None,
) -> tuple[SessionDaemon, LifecycleBackend, DesktopDriver, Controller, SessionConfig, _VirtualMonotonic]:
    """Build one real daemon consumer around the production fixture backend."""

    virtual_clock = _VirtualMonotonic()
    backend = backend or LifecycleBackend(root)
    backend.virtual_clock = virtual_clock
    driver = DesktopDriver(
        profile=DriverProfile(xauthority="/tmp/test-Xauthority", wine_prefix="/tmp/test-wine-prefix"),
        backend=backend,
        monotonic=virtual_clock.monotonic,
        lease_path=lease_path,
    )
    plan = load_catalog().scan_plan()
    config = SessionConfig(
        profile=driver.profile,
        journal=root / "session.json",
        socket=root / "session.sock",
        plan_hash=plan["planHash"],
        plan_json=plan["planJSON"],
        capture_dir=root / "captures",
        saved_variables=root / "Crowley.lua",
        companion_state=root / "companion.json",
        data_lua=root / "Data.lua",
    )
    value = copy.deepcopy(DEFAULT_STATE)
    for key, child in (journal_changes or {}).items():
        if isinstance(child, dict) and isinstance(value.get(key), dict):
            value[key].update(copy.deepcopy(child))
        else:
            value[key] = copy.deepcopy(child)
    journal = Journal(config.journal)
    journal.write(value)
    controller = Controller(
        journal,
        driver=driver,
        clock=virtual_clock.monotonic,
        wall_clock=lambda: backend.current["wallTime"],
        recover_on_restart=False,
    )
    if lease_path is None:
        daemon = SessionDaemon(config, controller=controller, driver=driver)
    else:
        with patch("crowley.session.daemon.LunaAdapter", _RuntimeFixtureModel):
            daemon = SessionDaemon(config, controller=controller, driver=driver)
    return daemon, backend, driver, controller, config, virtual_clock


def _fixture_event(
    number: int,
    event_class: EventClass,
    master: int,
    source: int,
    timestamp: int,
    detail: int | None,
    child: int | None,
    coordinates: tuple[float, float] | None = None,
    root_xy: tuple[float, float] | None = None,
    event_xy: tuple[float, float] | None = None,
    valuators: tuple[tuple[int, float, float | None], ...] = (),
) -> XI2Event:
    delivered = event_class in {
        EventClass.KEY_PRESS,
        EventClass.KEY_RELEASE,
        EventClass.BUTTON_PRESS,
        EventClass.BUTTON_RELEASE,
    }
    has_modifiers = delivered or event_class is EventClass.MOTION
    if coordinates is None:
        coordinates = (1.0, 1.0) if child is not None else None
    if root_xy is None:
        root_xy = coordinates
    if event_xy is None:
        event_xy = coordinates
    return XI2Event(
        number,
        event_class,
        master,
        source,
        timestamp,
        detail,
        0x374 if child is not None else None,
        0x374 if child is not None else None,
        child,
        root_xy,
        event_xy,
        (0, 0, 0) if has_modifiers else None,
        (),
        0 if has_modifiers else None,
        valuators,
    )


def _fixture_event_trace(events: list[XI2Event]) -> str:
    blocks: list[str] = []
    for event in events:
        block = [
            f"EVENT type {event.type_number} ({event.event_class.value})",
            f"    device: {event.master_device} ({event.source_device})",
            f"    time: {event.timestamp_ms}",
        ]
        if event.detail is not None:
            block.append(f"    detail: {event.detail}")
        if event.is_raw or (event.event_class is EventClass.MOTION and event.source_device == 4):
            block.append("    valuators:")
            for axis, value, raw_value in event.valuators:
                suffix = f" ({raw_value:.2f})" if raw_value is not None else ""
                block.append(f"    {axis}: {value:.2f}{suffix}")
        if event.child_xid is not None:
            root_xid = event.root_xid if event.root_xid is not None else 0x374
            event_xid = event.event_xid if event.event_xid is not None else root_xid
            root_xy = event.root_xy or (1.0, 1.0)
            event_xy = event.event_xy or root_xy
            block.extend(
                (
                    f"    root: {root_xy[0]:.2f}/{root_xy[1]:.2f}",
                    f"    event: {event_xy[0]:.2f}/{event_xy[1]:.2f}",
                    "    modifiers: locked 0 latched 0 base 0 effective: 0",
                    f"    windows: root {hex(root_xid)} event {hex(event_xid)} child {hex(event.child_xid)}",
                )
            )
        blocks.append("\n".join(block))
    return "\n".join(blocks)


class _FixtureInputObserver:
    def __init__(self, callback: object, synthetic: list[XI2Event], human: list[XI2Event]):
        self.callback = callback
        self.synthetic = synthetic
        self.human = human
        self._events: list[XI2Event] = []

    def _add(self, event: XI2Event) -> None:
        self._events.append(event)
        self.callback(event)  # type: ignore[operator]

    def events(self) -> list[XI2Event]:
        return list(self._events)

    def collect_until(self, predicate: object, *, timeout: float) -> str:
        del timeout
        for event in self.synthetic:
            self._add(event)
        assert predicate(self.events())  # type: ignore[operator]
        return _fixture_event_trace(self.synthetic)

    def wait_for_human(self, predicate: object, *, timeout: float) -> None:
        del timeout
        for event in self.human:
            self._add(event)
        assert predicate(self.events())  # type: ignore[operator]

    def stop(self) -> str:
        return _fixture_event_trace(self._events)


class _FixtureInputTarget:
    last_created = None

    def __init__(self, trace: list[str] | None = None) -> None:
        self.trace = trace if trace is not None else []
        self.prompt_acknowledged = False
        type(self).last_created = self
        self.window = OwnedWindow(
            os.getpid(),
            0x600119,
            "CROWLEY INPUT CALIBRATION ONLY",
            (0, 0, 480, 240),
            object(),
            frozenset({0x600119}),
            "/usr/bin/python3",
            "fixture-target-start",
            0x600118,
            (0, 0, 500, 260),
            frozenset({0x600118, 0x600119}),
        )

    def create(self) -> OwnedWindow:
        return self.window

    def close(self) -> None:
        return None

    def show_human_prompt(self) -> None:
        # The real GTK child ACKs after label.set_text and the parent then
        # publishes readiness.  Keep that ordering observable in the
        # deterministic target instead of silently treating prompt() as a
        # readiness assertion.
        self.prompt_acknowledged = True
        self.trace.append("prompt_ack")


class _FixtureLunaAdapter:
    """Bounded visual/decision adapter for the headless lifecycle fixture."""

    def __init__(self, backend: LifecycleBackend) -> None:
        self.backend = backend

    def cancel(self) -> None:
        return None

    def shutdown(self) -> None:
        self.cancel()

    def decide(self, image: bytes, *, target: str, verified_crop: object) -> ModelDecision:
        del image, verified_crop
        assert target == "game-client"
        return ModelDecision("enter_world", target)

    def observe(
        self,
        image: bytes,
        *,
        target: str,
        verified_crop: object,
        requested_state: str | None = None,
        requested_control: str | None = None,
        timeout: float | None = None,
    ) -> ModelObservation:
        del image, verified_crop, requested_control, timeout
        assert target == "game-client"
        if requested_state is not None:
            state = requested_state
        elif self.backend.character_select:
            state = "character_select"
        elif self.backend.current["ahOpen"]:
            state = "auction_house_open"
        else:
            state = "world"
        facts = {
            "disconnect_dialog": {
                "scene": "disconnect_dialog",
                "character": "",
                "realm": "",
                "modal": "WOW51900319",
                "code": "WOW51900319",
                "control": "dismiss_disconnect",
                "idle": "false",
            },
            "game_client": {
                "scene": "game_client",
                "character": "",
                "realm": "",
                "modal": "none",
                "code": "",
                "control": "client",
                "idle": "false",
            },
            "character_select": {
                "scene": "character_select",
                "character": "Arthur",
                "realm": "Classic Beta PvE 2",
                "modal": "character_select",
                "code": "",
                "control": "character_list",
                "idle": "true",
            },
            "arthur_selected": {
                "scene": "character_select",
                "character": "Arthur",
                "realm": "Classic Beta PvE 2",
                "modal": "character_select",
                "code": "",
                "control": "arthur_row",
                "idle": "true",
            },
            "world": {
                "scene": "world",
                "character": "Arthur",
                "realm": "Classic Beta PvE 2",
                "modal": "none",
                "code": "",
                "control": "world",
                "idle": "true",
            },
            "auction_house_open": {
                "scene": "world",
                "character": "Arthur",
                "realm": "Classic Beta PvE 2",
                "modal": "auction_house",
                "code": "",
                "control": "auctioneer_buckler",
                "idle": "true",
            },
        }[state]
        return ModelObservation(state, facts, anchor=(40, 30, 80, 60))


def test_three_cycle_daemon_and_socket_lifecycle(tmp_path: Path, monkeypatch) -> None:
    virtual_clock = _VirtualMonotonic()
    virtual_clock.native_schedule = True
    real_sleep = time.sleep
    backend = LifecycleBackend(tmp_path)
    backend.virtual_clock = virtual_clock

    driver = DesktopDriver(
        profile=DriverProfile(xauthority="/tmp/test-Xauthority", wine_prefix="/tmp/test-wine-prefix"),
        backend=backend,
        monotonic=virtual_clock.monotonic,
    )
    journal = tmp_path / "session.json"
    plan = load_catalog().scan_plan()
    config = SessionConfig(
        profile=driver.profile,
        journal=journal,
        socket=tmp_path / "session.sock",
        plan_hash=plan["planHash"],
        plan_json=plan["planJSON"],
        capture_dir=tmp_path / "captures",
        saved_variables=tmp_path / "Crowley.lua",
        companion_state=tmp_path / "companion.json",
        data_lua=tmp_path / "Data.lua",
    )
    controller = Controller(
        journal, driver=driver, clock=lambda: 0, wall_clock=lambda: backend.current["wallTime"]
    )
    daemon = SessionDaemon(config, controller=controller, driver=driver)
    driver.native_memory_meter = _FixtureNativeMemoryMeter(backend.identity)
    try:
        daemon.model = _FixtureLunaAdapter(backend)
        hierarchy = (
            (2, 3, "master", "pointer"),
            (3, 2, "master", "keyboard"),
            (4, 2, "slave", "XTEST pointer"),
            (5, 3, "slave", "XTEST keyboard"),
            (7, 2, "slave", "human pointer"),
            (9, 3, "slave", "human keyboard"),
        )
        synthetic = [
            _fixture_event(13, EventClass.RAW_KEY_PRESS, 3, 5, 100, 8, None),
            _fixture_event(2, EventClass.KEY_PRESS, 5, 5, 100, 8, 0x600119),
            _fixture_event(14, EventClass.RAW_KEY_RELEASE, 3, 5, 110, 8, None),
            _fixture_event(3, EventClass.KEY_RELEASE, 5, 5, 110, 8, 0x600119),
            _fixture_event(
                17,
                EventClass.RAW_MOTION,
                2,
                4,
                120,
                0,
                None,
                valuators=((0, 2.0, 2.0), (1, 2.0, 2.0)),
            ),
            # XI2 delivered Motion reports the source device in both the
            # master/source fields on this host (the preflight trace has
            # device 4 for the synthetic pointer).  Keep the fixture aligned
            # with the production pairing validator; device 2 is the raw
            # master and is used only by the raw button events below.
            _fixture_event(
                6,
                EventClass.MOTION,
                4,
                4,
                120,
                0,
                0x600119,
                coordinates=(2.0, 2.0),
                root_xy=(1.0, 1.0),
                event_xy=(1.0, 1.0),
                valuators=((0, 2.0, 2.0), (1, 2.0, 2.0)),
            ),
            _fixture_event(15, EventClass.RAW_BUTTON_PRESS, 2, 4, 121, 1, None),
            _fixture_event(4, EventClass.BUTTON_PRESS, 4, 4, 121, 1, 0x600119, coordinates=(2.0, 2.0)),
            _fixture_event(16, EventClass.RAW_BUTTON_RELEASE, 2, 4, 130, 1, None),
            _fixture_event(5, EventClass.BUTTON_RELEASE, 4, 4, 130, 1, 0x600119, coordinates=(2.0, 2.0)),
        ]
        # The real calibration owns the complete sealed keyboard vocabulary,
        # including every allowlisted command and the Control+A chord.  Feed
        # the same finite raw/delivered pairs to the deterministic observer so
        # this headless lifecycle exercises that production validator.
        keymap = backend.observe_keymap()
        event_number = 100
        timestamp = 300
        for operation in driver.calibration_keyboard_operations():
            for step in operation.steps:
                detail = keymap.get(step.keysym, keymap.get(step.keysym.rsplit("+", 1)[-1]))
                assert detail is not None
                raw_class = EventClass.RAW_KEY_PRESS if step.phase == "press" else EventClass.RAW_KEY_RELEASE
                delivered_class = EventClass.KEY_PRESS if step.phase == "press" else EventClass.KEY_RELEASE
                synthetic.extend(
                    (
                        _fixture_event(event_number, raw_class, 3, 5, timestamp, detail, None),
                        _fixture_event(event_number + 1, delivered_class, 5, 5, timestamp, detail, 0x600119),
                    )
                )
                event_number += 2
                timestamp += 1
        human = [
            _fixture_event(13, EventClass.RAW_KEY_PRESS, 3, 9, 200, 8, None),
            _fixture_event(2, EventClass.KEY_PRESS, 9, 9, 200, 8, 0x600119),
            _fixture_event(14, EventClass.RAW_KEY_RELEASE, 3, 9, 210, 8, None),
            _fixture_event(3, EventClass.KEY_RELEASE, 9, 9, 210, 8, 0x600119),
            # The live XI2 trace delivers human Motion with its source device
            # in both device fields.  Keep this event in the X11-backed
            # fixture: the workflow requires a measured human motion, and the
            # native seal must admit it only as an exact controlled echo.
            _fixture_event(6, EventClass.MOTION, 7, 7, 220, 0, 0x600119, coordinates=(2.0, 2.0)),
            _fixture_event(15, EventClass.RAW_BUTTON_PRESS, 2, 7, 221, 1, None),
            _fixture_event(4, EventClass.BUTTON_PRESS, 7, 7, 221, 1, 0x600119, coordinates=(2.0, 2.0)),
            _fixture_event(16, EventClass.RAW_BUTTON_RELEASE, 2, 7, 230, 1, None),
            _fixture_event(5, EventClass.BUTTON_RELEASE, 7, 7, 230, 1, 0x600119, coordinates=(2.0, 2.0)),
        ]

        driver.input_hierarchy = lambda **_kwargs: hierarchy  # type: ignore[method-assign]

        def synthetic_target_key_click(_window):
            backend._last_synthetic_motion_query = (1, 1, 0x600119, 2, 2, 2, 2, 0x600119)

        driver.synthetic_target_key_click = synthetic_target_key_click  # type: ignore[method-assign]
        driver.synthetic_target_keyboard_profile = (  # type: ignore[method-assign]
            lambda _window, *, operations, calibration_ticket: setattr(
                backend,
                "_last_synthetic_motion_query",
                (1, 1, 0x600119, 2, 2, 2, 2, 0x600119),
            )
        )

        def start_input_observer(
            *, calibration: bool = False, callback: object = None
        ) -> _FixtureInputObserver:
            if calibration:
                assert callback is not None
                return _FixtureInputObserver(callback, synthetic, human)
            observer = _FixtureInputObserver(driver._external_input, (), ())
            backend.runtime_observer = observer
            backend.runtime_driver = driver
            return observer

        driver.start_input_observer = start_input_observer  # type: ignore[method-assign]
        driver.stop_input_observer = lambda *_args, **_kwargs: None  # type: ignore[method-assign]

        server = threading.Thread(target=serve, args=(config.socket, controller, daemon), daemon=True)
        server.start()
        for _ in range(100):
            if config.socket.exists():
                break
            __import__("time").sleep(0.01)

        def wait_for_operation(kind: str) -> dict:
            # The Lua Agent itself drives hold/measure/resume.  These requests
            # are delayed a few captures so the daemon must wait for actual
            # fresh publications rather than accepting its readiness signal.
            operator_actions = {"load": False, "hold": False, "measure": False, "resume": False}
            for _ in range(30000):
                response = _socket_request(config.socket, {"command": "calibration_status"})
                handshake = response["status"]["nativeHandshake"]
                if handshake["state"] == "bootstrap_ready" and not operator_actions["load"]:
                    backend.load_agent()
                    operator_actions["load"] = True
                if handshake["holdRequired"] and not operator_actions["hold"]:
                    backend.request_agent_command("hold")
                    operator_actions["hold"] = True
                if handshake["measureReady"] and not operator_actions["measure"]:
                    backend.request_agent_command("measure")
                    operator_actions["measure"] = True
                if handshake["resumeRequired"] and not operator_actions["resume"]:
                    backend.request_agent_command("resume")
                    operator_actions["resume"] = True
                operation = response["status"]["calibrationOperation"]
                if operation["kind"] == kind and operation["state"] in {"complete", "error"}:
                    details = operation | {"agentTrace": backend.agent_trace[-12:]}
                    if operation["state"] != "complete":
                        raise AssertionError(details)
                    return response["status"]
                real_sleep(0.005)
            raise AssertionError(f"{kind} calibration did not finish")

        start = _socket_request(config.socket, {"command": "start", "generation": 0, "mode": "validation"})
        start_generation = start["status"]["generation"]
        bootstrap_calls: list[int | None] = []

        native_bootstrap = daemon.native_bootstrap

        def fixture_native_bootstrap(*, expected_generation: int | None = None) -> dict:
            bootstrap_calls.append(expected_generation)
            assert expected_generation == start_generation
            assert daemon.status_dict()["state"] == "NATIVE_CALIBRATION"
            return native_bootstrap(expected_generation=expected_generation)

        monkeypatch.setattr(daemon, "native_bootstrap", fixture_native_bootstrap)
        bootstrap = _socket_request(
            config.socket,
            {"command": "native_bootstrap", "generation": start_generation},
        )
        assert bootstrap["ok"]
        assert bootstrap_calls == [start_generation]

        native_start = _socket_request(
            config.socket,
            {"command": "native_calibrate", "generation": start_generation},
        )
        assert native_start["ok"]
        native_status = wait_for_operation("native")
        assert native_status["state"] == "INPUT_CALIBRATION"
        native_handshake = native_status["nativeHandshake"]
        assert native_handshake["state"] == "resume_ready"
        assert native_handshake["resumeRequired"]
        assert native_handshake["resumeReady"]
        assert native_handshake["restored"] is True
        assert [receipt["phase"] for receipt in native_handshake["archiveReceipts"]] == [
            "construction",
            "updates",
        ]
        assert all(receipt["recordSha256"] for receipt in native_handshake["archiveReceipts"])
        native_record = json.loads(journal.read_text())["calibrationEvidence"]["native"]
        retained_native_capture = Path(native_record["capture_path"])
        assert retained_native_capture.is_file()
        assert retained_native_capture.parent == journal.parent / "native-evidence"
        assert retained_native_capture.stat().st_mode & 0o777 == 0o600
        assert [path for path in retained_native_capture.parent.iterdir()] == [retained_native_capture]
        native_generation = native_status["generation"]

        from crowley.session import calibration as calibration_module

        real_input_workflow = calibration_module.InputCalibrationWorkflow
        calibration_trace: list[str] = []

        class FixtureInputCalibrationWorkflow(real_input_workflow):
            def __init__(self, owned_driver, *, display, on_ready):
                super().__init__(
                    owned_driver,
                    display=display,
                    on_ready=on_ready,
                    window_factory=lambda: _FixtureInputTarget(calibration_trace),
                )

            def run(self) -> object:
                return super().run(human_timeout=0.05)

        monkeypatch.setattr(
            calibration_module,
            "InputCalibrationWorkflow",
            FixtureInputCalibrationWorkflow,
        )
        real_issue_ticket = driver.issue_calibration_ticket
        real_focus_target = driver.focus_calibration_target
        real_notify_ready = driver.notify_input_calibration_ready
        real_queue_delayed = driver.queue_delayed_calibration_action

        def issue_ticket(window):
            calibration_trace.append("ticket")
            return real_issue_ticket(window)

        def focus_target(window, *, calibration_ticket):
            calibration_trace.append("focus")
            return real_focus_target(window, calibration_ticket=calibration_ticket)

        def notify_ready(readiness):
            calibration_trace.append("ready")
            return real_notify_ready(readiness)

        def queue_delayed(window, *, delay, calibration_ticket):
            calibration_trace.append("schedule")
            return real_queue_delayed(
                window,
                delay=delay,
                calibration_ticket=calibration_ticket,
            )

        def synthetic_profile(_window, *, operations, calibration_ticket):
            assert operations
            assert calibration_ticket is not None
            calibration_trace.append("synthetic")
            backend._last_synthetic_motion_query = (1, 1, 0x600119, 2, 2, 2, 2, 0x600119)

        driver.issue_calibration_ticket = issue_ticket  # type: ignore[method-assign]
        driver.focus_calibration_target = focus_target  # type: ignore[method-assign]
        driver.notify_input_calibration_ready = notify_ready  # type: ignore[method-assign]
        driver.queue_delayed_calibration_action = queue_delayed  # type: ignore[method-assign]
        driver.synthetic_target_keyboard_profile = synthetic_profile  # type: ignore[method-assign]
        input_start = _socket_request(
            config.socket,
            {"command": "input_calibrate", "generation": native_generation},
        )
        assert input_start["ok"]
        paused_status = wait_for_operation("input")
        assert paused_status["state"] == "PAUSED"
        assert _FixtureInputTarget.last_created is not None
        assert _FixtureInputTarget.last_created.prompt_acknowledged
        # The delayed-action due fence is sealed before readiness is published;
        # a consumer cannot observe a human window before its timer exists.
        assert calibration_trace == ["ticket", "focus", "synthetic", "prompt_ack", "schedule", "ready"]
        paused_generation = paused_status["generation"]
        assert paused_generation > native_generation
        # Native cadence deliberately advances the injected clock by one
        # second per real Agent tick.  Rebase the headless lifecycle clock
        # before handing control to the daemon's model-backed visual
        # producer, whose timing remains wall-clock scoped in production.
        virtual_clock.value = time.monotonic()
        backend.use_lifecycle_agent()

        resumed = _socket_request(
            config.socket,
            {"command": "resume", "generation": paused_generation},
        )
        assert resumed["ok"], resumed
        assert resumed["status"]["state"] == "RECONCILE"
        _attach_recording_anchor_provider(driver, tmp_path)

        advanced_uids: set[str] = set()
        for _ in range(160):
            daemon.run_once()
            if backend.uid and backend.current["loaded"]["ackedIds"] and backend.uid not in advanced_uids:
                backend.advance_ack()
                advanced_uids.add(backend.uid)
            status = _socket_request(config.socket, {"command": "status"})["status"]
            if status["state"] == "STOPPED":
                break
        final_status = _socket_request(config.socket, {"command": "status"})["status"]
        assert final_status["streak"] == 3, final_status
        assert final_status["state"] == "STOPPED", final_status
        assert any(
            event["name"] == "submit_command" and event.get("command") == "/logout"
            for event in backend.events
        )
        assert any(
            event["name"] == "submit_command" and event.get("command") == "/crowley session fence"
            for event in backend.events
        )
    finally:
        daemon.request_shutdown()
        driver.close()


def test_live_daemon_binds_owned_visual_and_render_providers(tmp_path: Path) -> None:
    plan = load_catalog().scan_plan()
    profile = DriverProfile(
        xauthority="/tmp/test-Xauthority",
        wine_prefix="/measured/wine-prefix",
    )
    backend = X11Backend(profile, input_tool=fixture_input_tool(tmp_path / "tool"))
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "desktop.lock")
    config = SessionConfig(
        profile=profile,
        journal=tmp_path / "session.json",
        socket=tmp_path / "session.sock",
        plan_hash=plan["planHash"],
        plan_json=plan["planJSON"],
    )
    daemon = SessionDaemon(config, driver=driver)
    try:
        assert getattr(driver._named_state_observer, "__self__", None) is daemon
        assert getattr(driver.native_measurement_provider, "__self__", None) is daemon
        assert getattr(driver.measured_anchor_provider, "__self__", None) is daemon
    finally:
        daemon.request_shutdown()
        driver.close()


def test_default_native_meter_binds_real_child_and_closes_on_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    child = subprocess.Popen(["/bin/sleep", "30"])
    stat = Path(f"/proc/{child.pid}/stat").read_text(encoding="ascii")
    process_start = stat[stat.rfind(")") + 2 :].split()[19]
    linux_executable = os.path.realpath(os.readlink(f"/proc/{child.pid}/exe"))
    profile = DriverProfile(xauthority="/tmp/test-Xauthority", wine_prefix="/tmp/test-wine-prefix")
    backend = object.__new__(X11Backend)
    backend.profile = profile
    backend.xauthority = profile.xauthority
    backend.input_tool = fixture_input_tool(tmp_path / "tool")
    identity = WindowIdentity(
        0x1800001,
        child.pid,
        "WowB.exe",
        "World of Warcraft",
        "wowb.exe,wowb.exe",
        0x1600011,
        (0, 0, 1928, 1092),
        (0, 0, 1920, 1080),
        0x1800001,
        process_start,
        ":test",
        "default-meter-child",
        0x1,
        0x1800001,
        frozenset({0x1800001, 0x1600011}),
    )
    backend.resolve_identity = lambda require_foreground=True: identity  # type: ignore[attr-defined]
    driver = DesktopDriver(profile=profile, backend=backend, lease_path=tmp_path / "default-meter.lock")
    plan = load_catalog().scan_plan()
    config = SessionConfig(
        profile=profile,
        journal=tmp_path / "session.json",
        socket=tmp_path / "session.sock",
        plan_hash=plan["planHash"],
        plan_json=plan["planJSON"],
        codex_path="/home/dev/.cache/crowley/codex/0.162.1/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex",
    )
    journal = Journal(config.journal)
    journal.write(
        {**copy.deepcopy(DEFAULT_STATE), "state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4}
    )
    controller = Controller(journal, driver=driver, recover_on_restart=False)
    daemon = SessionDaemon(config, controller=controller, driver=driver)
    meters: list[LinuxProcStatusVmHwmReset5] = []
    outcomes = iter(("failure", "success"))

    class ProbeRunner:
        def __init__(
            self, owned_driver: DesktopDriver, *, monotonic: object, diagnostic: object | None = None
        ) -> None:
            del monotonic
            del diagnostic
            meter = owned_driver.native_memory_meter
            assert isinstance(meter, LinuxProcStatusVmHwmReset5)
            assert meter.pid == identity.pid
            assert meter.process_start == identity.process_start
            assert meter.process_executable == linux_executable
            assert meter.identity_fingerprint == identity.fingerprint
            meters.append(meter)

        def run(self) -> object:
            if next(outcomes) == "failure":
                raise DriverError("default meter probe failure")
            return SimpleNamespace()

    monkeypatch.setattr("crowley.session.daemon.NativeCalibrationRunner", ProbeRunner)

    def native_calibrated(
        _evidence: object,
        *,
        preconstruction_proof: dict[str, object] | None = None,
        expected_generation: int | None = None,
        expected_state: ControllerState | None = None,
    ) -> object:
        del preconstruction_proof
        assert expected_generation == 4
        assert expected_state is ControllerState.NATIVE_CALIBRATION
        return replace(controller.status(), state=ControllerState.INPUT_CALIBRATION)

    controller.native_calibrated = native_calibrated  # type: ignore[method-assign]
    try:
        with pytest.raises(DriverError, match="default meter probe failure"):
            daemon.run_native_calibration(expected_generation=4)
        assert daemon._native_handshake["state"] == "error"
        assert daemon._native_handshake["restored"] is False
        assert driver.native_memory_meter is None
        assert meters[0]._closed

        result = daemon.run_native_calibration(expected_generation=4)
        assert result["calibration"] == "native"
        assert len(meters) == 2
        assert meters[1] is not meters[0]
        assert meters[1]._closed
        assert driver.native_memory_meter is None
    finally:
        daemon.request_shutdown()
        driver.close()
        child.terminate()
        child.wait(timeout=3)


def test_runtime_reconcile_ready_scanner_is_idle_with_pending_saved_uid(tmp_path: Path) -> None:
    daemon, backend, driver, _controller, config, _clock = _runtime_daemon(tmp_path)
    uid = "runtime-pending-uid"
    _saved_fixture(config.saved_variables, uid, 100)  # type: ignore[arg-type]
    assert config.companion_state is not None
    assert config.data_lua is not None
    config.companion_state.write_text(json.dumps({"uploaded": {uid: 103}, "probes": []}))
    config.data_lua.write_text(
        render_assignment(
            "CROWLEY_DATA",
            {
                "generatedAt": 103,
                "ackedScans": [uid],
                "scanPlan": load_catalog().scan_plan(),
                "shoppingLists": [],
            },
            "runtime pending UID",
        )
    )
    snapshot = _snapshot(1000)
    snapshot["lastSaved"] = {
        "memoryUid": uid,
        "finishedAt": 102,
        "planned": 428,
        "attempted": 428,
        "failures": 0,
        "rows": 428,
        "persistence": "unknown",
    }
    snapshot["pending"] = {"ids": [uid], "count": 1, "cap": 6, "blocked": False, "reason": ""}
    try:
        facts = daemon._reconcile_durable_files(snapshot)
        assert facts["scanner_phase"] == "ready"
        assert facts["scanner_idle"] is True
        assert facts["stable_format2_uid"] == uid
        assert facts["stable_format2_evidence"] is not None
    finally:
        daemon.request_shutdown()
        driver.close()


def test_runtime_uncertain_no_agent_never_recovers_login_or_input(tmp_path: Path) -> None:
    cases = ("logout", "enter_world")
    for action in cases:
        root = tmp_path / action
        uid = f"runtime-{action}-uid"
        daemon, backend, driver, controller, config, _clock = _runtime_daemon(
            root,
            journal_changes={
                "state": ControllerState.RECONCILE.value,
                "generation": 4,
                "restartUncertain": True,
                "reconciliationRequired": True,
                "current": {
                    "uid": uid,
                    "pending": True,
                    "startedAt": 100,
                    "action": action,
                    "actionAttempt": 2,
                    "actionResult": "dispatched",
                },
            },
        )
        try:
            _saved_fixture(config.saved_variables, uid, 100)  # type: ignore[arg-type]
            assert config.companion_state is not None
            assert config.data_lua is not None
            config.companion_state.write_text(json.dumps({"uploaded": {uid: 103}, "probes": []}))
            config.data_lua.write_text(
                render_assignment(
                    "CROWLEY_DATA",
                    {
                        "generatedAt": 103,
                        "ackedScans": [uid],
                        "scanPlan": load_catalog().scan_plan(),
                        "shoppingLists": [],
                    },
                    "runtime unsettled queue",
                )
            )
            backend.current = _snapshot(1000)
            backend.current["lastSaved"]["memoryUid"] = uid
            backend.current["pending"] = {
                "ids": [uid],
                "count": 1,
                "cap": 6,
                "blocked": False,
                "reason": "",
            }
            if action == "logout":
                backend.character_select_observed = lambda: True  # type: ignore[attr-defined]
            else:

                def loading_capture() -> object:
                    raise OSError("telemetry canvas absent while world loads")

                daemon.capture_status = loading_capture  # type: ignore[method-assign]

            def forbidden_recovery() -> None:
                raise AssertionError("uncertain restart dispatched login recovery")

            daemon._recover_login = forbidden_recovery  # type: ignore[method-assign]
            before = controller.journal.read()
            status = daemon.run_once()
            assert status["state"] == ControllerState.RECONCILE.value
            assert status["actionIntent"] == action
            assert controller.journal.read() == before
            assert backend.events == []
        finally:
            daemon.request_shutdown()
            driver.close()


def test_runtime_ack_reload_missing_full_evidence_does_not_complete(tmp_path: Path) -> None:
    uid = "runtime-missing-evidence"
    daemon, _backend, driver, controller, config, _clock = _runtime_daemon(
        tmp_path,
        journal_changes={
            "state": ControllerState.ACK_RELOAD_WAIT.value,
            "generation": 4,
            "current": {
                "uid": uid,
                "pending": True,
                "startedAt": 100,
                "action": "ack_reload",
                "actionAttempt": 2,
                "actionResult": "dispatched",
                "frameBoot": "ack-boot",
                "frameSequence": 2,
                "evidence": {
                    "uid": uid,
                    "stableSavedUid": uid,
                    "finishedAt": 102,
                    "uploadTimestamp": 103,
                    "ackPublicationAt": 103,
                    "atomicCompanionUploadedUid": uid,
                    "dataAckUid": uid,
                },
            },
        },
    )
    try:
        # Deliberately remove the stable SavedVariables path.  The loaded/pending
        # telemetry is positive, but no complete SweepEvidence is available to
        # qualify this UID.
        object.__setattr__(config, "saved_variables", None)
        snapshot = _snapshot(104, boot="ack-boot", sequence=2)
        snapshot["loaded"] = {"ackedIds": [uid], "generatedAt": 104}
        snapshot["pending"] = {"ids": [], "count": 0, "cap": 6, "blocked": False, "reason": ""}
        try:
            daemon._advance(snapshot, fence=controller.observation_fence())
        except EvidenceError as exc:
            assert "stable evidence path" in str(exc)
        status = controller.status()
        assert status.state is not ControllerState.REOPEN
        assert status.state in {ControllerState.ACK_RELOAD_WAIT, ControllerState.BLOCKED}
        assert controller.journal.read()["current"]["pending"] is True
        assert controller.journal.read()["qualification"]["totalAccepted"] == 0
    finally:
        daemon.request_shutdown()
        driver.close()


def test_runtime_qualification_retry_journal_error_preserves_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = "runtime-qualification-retry"
    daemon, _backend, driver, controller, config, _clock = _runtime_daemon(
        tmp_path,
        journal_changes={"state": ControllerState.WAIT_DUE.value},
    )
    assert config.saved_variables is not None
    _saved_fixture(config.saved_variables, uid, 100)
    snapshot = _snapshot(1000)
    evidence = read_stable_saved_scan(
        config.saved_variables,
        uid=uid,
        planned=428,
        **daemon._saved_scan_kwargs(snapshot),
    )
    try:
        controller.begin_scan(started_at=100)
        controller.saved(uid)
        controller.reload_sent()
        controller.expect_boot("save-old")
        controller.observe_frame(boot="save-boot", sequence=1, crc32=1)
        controller.stable_saved(evidence)
        controller.uploaded(uid, accepted=True, upload_time=103, data_ack_uid=uid)
        controller.record_ack_publication(
            uid,
            companion_uid=uid,
            data_uid=uid,
            publication_time=103,
            boot="save-boot",
            sequence=1,
        )
        controller.ack_reload_command_sent()
        controller.expect_boot("ack-old", acknowledgement=True)
        controller.observe_frame(boot="ack-boot", sequence=2, crc32=2)
        controller.ack_reload_complete(
            pending_ids=set(),
            loaded_uid=uid,
            loaded_at=105,
            boot="ack-boot",
            sequence=2,
        )

        original_write = controller.journal._write_archive_artifact
        first_failure = True

        def fail_first_publication(kind: str, ordinal: int, record: dict) -> None:
            nonlocal first_failure
            if first_failure and kind == "runs":
                first_failure = False
                raise JournalError("runtime injected qualification publication failure")
            original_write(kind, ordinal, record)

        monkeypatch.setattr(controller.journal, "_write_archive_artifact", fail_first_publication)
        with pytest.raises(JournalError):
            controller.qualify(evidence, started_at=100)

        def fail_retry_publication(kind: str, ordinal: int, record: dict) -> None:
            del kind, ordinal, record
            raise JournalError("runtime retry publication failure")

        monkeypatch.setattr(controller.journal, "_write_archive_artifact", fail_retry_publication)
        durable_before_retry = controller.journal.read()
        try:
            daemon.run_once()
        except JournalError:
            pass
        durable_after_retry = controller.journal.read()
        assert durable_after_retry == durable_before_retry
        assert controller.status().state is ControllerState.QUALIFY_PENDING
        assert controller.journal.read()["qualification"]["totalAccepted"] == 0
    finally:
        daemon.request_shutdown()
        driver.close()


def _assert_native_provider_cleanup(
    root: Path, backend: _NativeProviderBackend, daemon: SessionDaemon
) -> None:
    assert daemon._native_owned_capture_paths == set()
    assert all(not path.exists() for path in backend.capture_paths)
    evidence_dir = root / "native-evidence"
    if evidence_dir.exists():
        assert not list(evidence_dir.glob("*.png"))


def _diagnostic_fixture_daemon(root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        config=SimpleNamespace(journal=root / "session.json"),
        _runtime_source_binding={
            "daemon.py": "a" * 64,
            "protocol.py": "b" * 64,
        },
        _loaded_config_semantic_sha256="c" * 64,
        driver=SimpleNamespace(profile=SimpleNamespace(telemetry_region_executable_sha256="d" * 64)),
        controller=SimpleNamespace(status=lambda: SimpleNamespace(generation=7)),
    )


class _RuntimeFixtureModel:
    def __init__(self, **_kwargs: object) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def shutdown(self) -> None:
        self.cancelled = True


def test_runtime_native_observation_diagnostic_is_bounded_private_and_bound(tmp_path: Path) -> None:
    daemon = _diagnostic_fixture_daemon(tmp_path)
    diagnostic = _NativeObservationDiagnostic(daemon)
    diagnostic.start_run()
    with diagnostic.span("identity_pre_provider", requested_stage="updates", requested_ordinal=1):
        pass
    for ordinal in range(1, 20):
        diagnostic.begin_attempt("updates", ordinal)
        diagnostic.finish_attempt(status="no_change")

    capture = tmp_path / "candidate.png"
    Image.new("RGB", (256, 256), (0, 0, 0)).save(capture, format="PNG")
    frame = SimpleNamespace(
        snapshot=SimpleNamespace(value={"render": {"nativePhase": "updates", "nativeOrdinal": 20}}),
        boot="boot-7",
        sequence=27,
        uptime_ms=20_000,
    )
    sample = SimpleNamespace(kind="FRESH", frame=frame, capture_monotonic=123.5)
    diagnostic.begin_attempt("updates", 20)
    diagnostic.record_candidate(sample, "e" * 64, capture)
    diagnostic.set_status(status="mismatch", error="wrong publication")
    with diagnostic.span("identity_poll"):
        pass
    diagnostic.fail(
        "native updates/20 returned 'updates'/21",
        stage="updates",
        ordinal=20,
        offending_path=capture,
        mismatch=True,
    )
    capture.unlink()
    diagnostic.mark_release(capture)

    failure = diagnostic.failure_path
    offending = diagnostic.offending_path
    assert failure is not None and failure.is_file()
    assert offending is not None and offending.is_file()
    with Image.open(offending) as image:
        assert image.size == (256, 256)
    assert stat.S_IMODE(failure.stat().st_mode) == 0o600
    assert stat.S_IMODE(failure.parent.stat().st_mode) == 0o700
    payload = json.loads(failure.read_text())
    assert payload["trace_schema"] == "native-observation-diagnostic-v1"
    assert payload["protocol_sha256"] == payload["source_binding"]["protocol.py"]
    assert isinstance(payload["source_binding_current"], dict)
    assert isinstance(payload["source_binding_current_sha256"], str)
    assert isinstance(payload["calibration_source_sha256_current"], str)
    assert payload["source_binding_error"] is None
    assert payload["source_drift"] is True
    assert payload["binary_sha256"] == "d" * 64
    assert len(payload["attempts"]) == 16
    assert payload["attempts"][0]["requested_ordinal"] == 5
    assert payload["attempts"][-1]["actual"]["publisher_uptime_ms"] == 20_000
    assert payload["attempts"][-1]["spans"]["identity_poll"]["duration_ns"] is not None
    assert payload["attempts"][-1]["spans"]["cells"]["duration_ns"] is None
    assert payload["attempts"][-1]["release_outcome"] == "released"
    assert payload["run_spans"][0]["name"] == "identity_pre_provider"
    assert payload["run_spans"][0]["requested_stage"] == "updates"
    assert payload["run_spans"][0]["requested_ordinal"] == 1
    assert payload["run_spans"][0]["duration_ns"] is not None
    assert str(tmp_path) not in failure.read_text()
    assert (
        payload["failure"]["offending_capture_sha256"] == hashlib.sha256(offending.read_bytes()).hexdigest()
    )


def test_runtime_native_observation_diagnostic_persistence_failure_preserves_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    daemon = _diagnostic_fixture_daemon(tmp_path)
    diagnostic = _NativeObservationDiagnostic(daemon)
    diagnostic.start_run()
    monkeypatch.setattr(diagnostic, "_failure_directory", lambda: Path("/proc/does-not-exist"))
    diagnostic.fail("original native mismatch", stage="updates", ordinal=4)
    assert diagnostic.failure_path is None
    assert diagnostic._persistence_error is not None


def test_runtime_native_observation_diagnostic_success_writes_no_artifact(tmp_path: Path) -> None:
    daemon = _diagnostic_fixture_daemon(tmp_path)
    diagnostic = _NativeObservationDiagnostic(daemon)
    diagnostic.start_run()
    diagnostic.begin_attempt("construct", 0)
    diagnostic.finish_attempt(status="accepted")
    diagnostic.finish_success()
    assert not (tmp_path / "native-observation-diagnostics").exists()


def test_runtime_native_observation_recording_overhead_is_bounded(tmp_path: Path) -> None:
    daemon = _diagnostic_fixture_daemon(tmp_path)
    diagnostic = _NativeObservationDiagnostic(daemon)
    diagnostic.start_run()
    iterations = 128
    baseline_started = time.perf_counter_ns()
    for ordinal in range(iterations):
        diagnostic.begin_attempt("updates", ordinal)
        with nullcontext():
            hashlib.sha256(f"recorded-{ordinal}".encode()).hexdigest()
        with nullcontext():
            json.dumps({"ordinal": ordinal}, sort_keys=True)
        diagnostic.finish_attempt(status="no_change")
    baseline_ns = time.perf_counter_ns() - baseline_started

    recorded_started = time.perf_counter_ns()
    for ordinal in range(iterations):
        diagnostic.begin_attempt("updates", ordinal)
        with diagnostic.span("provider_hash"):
            hashlib.sha256(f"recorded-{ordinal}".encode()).hexdigest()
        with diagnostic.span("provider_decode"):
            json.dumps({"ordinal": ordinal}, sort_keys=True)
        diagnostic.finish_attempt(status="no_change")
    recorded_ns = time.perf_counter_ns() - recorded_started
    assert recorded_ns - baseline_ns < 250_000_000


def test_runtime_native_provider_delayed_agent_and_hold_use_real_publications(tmp_path: Path) -> None:
    backend = _NativeProviderBackend(tmp_path, load_after_captures=3)
    daemon, _backend, driver, controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    try:
        identity = backend.identity
        constructed = daemon._native_measurement_provider(identity, "construct", 0)
        assert constructed.native_phase == "normal"
        assert constructed.native_ordinal == 0
        assert backend.agent_client is not None
        assert backend.captures >= 4  # three genuine no-Agent polls precede addon load
        daemon.release_native_capture(Path(constructed.capture_path))

        backend.request_agent_command("hold", delayed_captures=3)
        held = daemon._native_measurement_provider(identity, "held", 0)
        assert held.native_phase == "held"
        assert held.native_ordinal == 0
        held_index = next(
            index for index, item in enumerate(backend.agent_trace) if item[1] == "held" and item[2] == 0
        )
        assert all(item[1] == "normal" for item in backend.agent_trace[:held_index])
        daemon.release_native_capture(Path(held.capture_path))

        backend.request_agent_command("measure", delayed_captures=3)
        update = daemon._native_measurement_provider(identity, "updates", 1)
        assert update.native_phase == "updates"
        assert update.native_ordinal == 1
        daemon.release_native_capture(Path(update.capture_path))

        backend.agent_client.advance_with_timers(99)
        held_final = daemon._native_measurement_provider(identity, "held", 100)
        assert held_final.native_phase == "held"
        assert held_final.native_ordinal == 100
        held_final_sequence = held_final.sequence
        daemon.release_native_capture(Path(held_final.capture_path))

        backend.request_agent_command("resume", delayed_captures=3)
        resumed = daemon._native_measurement_provider(identity, "resume", 0)
        assert resumed.native_phase == "normal"
        assert resumed.native_ordinal == 0
        assert resumed.sequence == held_final_sequence + 1
        daemon.release_native_capture(Path(resumed.capture_path))
        _assert_native_provider_cleanup(tmp_path, backend, daemon)
    finally:
        daemon.request_shutdown()
        driver.close()


def test_runtime_native_observation_couples_provider_and_runner_spans(tmp_path: Path) -> None:
    """The real provider and runner hooks share one attributed attempt trace."""

    backend = _NativeProviderBackend(tmp_path, load_after_captures=0)
    daemon, _backend, driver, _controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    diagnostic = daemon._native_observation_diagnostic
    runner = NativeCalibrationRunner(driver, diagnostic=diagnostic)
    decoder = driver.new_native_decoder()
    released = False
    try:
        identity = backend.identity
        diagnostic.start_run()
        with runner._diagnostic_span(
            "identity_pre_provider", requested_stage="construct", requested_ordinal=0
        ):
            assert driver.resolve_identity().fingerprint == identity.fingerprint
        observation = daemon._native_measurement_provider(identity, "construct", 0)
        with runner._diagnostic_span("runner_hash"):
            capture_path = runner._capture_observation(identity, observation)
        with runner._diagnostic_span("runner_decode"):
            decoded = driver.decode_native_capture(capture_path, identity=identity, decoder=decoder)
        assert decoded.frame is not None

        attempt = diagnostic._attempts[-1]
        assert attempt["requested_stage"] == "construct"
        assert attempt["requested_ordinal"] == 0
        for name in ("provider_hash", "provider_decode", "runner_hash", "runner_decode"):
            assert attempt["spans"][name]["duration_ns"] is not None
            assert attempt["spans"][name]["outcome"] == "ok"
        assert diagnostic._current is attempt
        runner._release_capture(Path(observation.capture_path))
        released = True
        assert attempt["release_outcome"] == "released"
        assert diagnostic._current is None
        with runner._diagnostic_span("identity_pre_provider", requested_stage="updates", requested_ordinal=1):
            assert driver.resolve_identity().fingerprint == identity.fingerprint
        pre_provider = [span for span in diagnostic._run_spans if span["name"] == "identity_pre_provider"]
        assert len(pre_provider) == 2
        assert pre_provider[0]["requested_stage"] == "construct"
        assert pre_provider[0]["requested_ordinal"] == 0
        assert pre_provider[1]["requested_stage"] == "updates"
        assert pre_provider[1]["requested_ordinal"] == 1
    finally:
        if not released and "observation" in locals() and observation.capture_path is not None:
            daemon.release_native_capture(Path(observation.capture_path))
        daemon.request_shutdown()
        driver.close()


def test_runtime_native_provider_absence_times_out_and_cleans_artifacts(tmp_path: Path) -> None:
    backend = _NativeProviderBackend(tmp_path, load_after_captures=None)
    daemon, _backend, driver, _controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    try:
        with pytest.raises(DriverError, match="did not produce the requested fresh frame"):
            daemon._native_measurement_provider(backend.identity, "construct", 0)
        assert backend.agent_client is None
        assert backend.captures >= 30
        _assert_native_provider_cleanup(tmp_path, backend, daemon)
    finally:
        daemon.request_shutdown()
        driver.close()


def test_runtime_native_provider_generation_revocation_cleans_artifacts(tmp_path: Path) -> None:
    backend = _NativeProviderBackend(tmp_path, load_after_captures=None)
    daemon, _backend, driver, controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    failures: list[BaseException] = []

    def wait_for_frame() -> None:
        try:
            daemon._native_measurement_provider(backend.identity, "construct", 0)
        except BaseException as exc:  # the assertion below reports the exact provider failure
            failures.append(exc)

    worker = threading.Thread(target=wait_for_frame, name="runtime-native-provider")
    try:
        worker.start()
        assert backend.capture_started.wait(timeout=2)
        controller.pause("runtime native generation revoked")
        worker.join(timeout=2)
        assert not worker.is_alive()
        assert len(failures) == 1
        assert isinstance(failures[0], DriverError)
        assert "generation was revoked" in str(failures[0])
        _assert_native_provider_cleanup(tmp_path, backend, daemon)
    finally:
        if worker.is_alive():
            daemon.request_shutdown()
            worker.join(timeout=2)
        daemon.request_shutdown()
        driver.close()


@pytest.mark.parametrize(
    ("fault", "message"),
    [
        ("wrong_phase", "native construct/0 returned 'held'/0"),
        ("skipped_ordinal", "native updates/1 returned 'updates'/3"),
    ],
)
def test_runtime_native_provider_rejects_wrong_or_skipped_real_publication(
    tmp_path: Path, fault: str, message: str
) -> None:
    backend = _NativeProviderBackend(tmp_path, publication_fault=fault if fault == "wrong_phase" else None)
    daemon, _backend, driver, _controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    with daemon._native_construction_lock:
        daemon._native_construction_handshake = {"state": "running"}
        daemon._native_construction_reset_history_locked()
        daemon._native_construction_start_context_locked(generation=4, deferred=False)
    try:
        if fault == "wrong_phase":
            with pytest.raises(DriverError, match=re.escape(message)):
                daemon._native_measurement_provider(backend.identity, "construct", 0)
        else:
            constructed = daemon._native_measurement_provider(backend.identity, "construct", 0)
            daemon.release_native_capture(Path(constructed.capture_path))
            backend.publication_fault = "skipped_ordinal"
            with pytest.raises(DriverError, match=re.escape(message)):
                daemon._native_measurement_provider(backend.identity, "updates", 1)
        diagnostic_path = daemon._native_observation_diagnostic.failure_path
        assert diagnostic_path is not None and diagnostic_path.is_file()
        diagnostic_payload = json.loads(diagnostic_path.read_text())
        assert diagnostic_payload["failure"]["stage"] in {"construct", "updates"}
        assert diagnostic_payload["failure"]["ordinal"] in {0, 1}
        assert diagnostic_payload["failure"]["offending_capture_name"] == "offending-capture.png"
        offending = diagnostic_path.parent / "offending-capture.png"
        assert offending.is_file()
        with Image.open(offending) as image:
            assert image.size == (256, 256)
        assert (
            diagnostic_payload["failure"]["offending_capture_sha256"]
            == hashlib.sha256(offending.read_bytes()).hexdigest()
        )
        assert diagnostic_payload["source_drift"] is False
        assert diagnostic_payload["source_binding_error"] is None
        assert diagnostic_payload["source_binding_start_error"] is None
        assert diagnostic_payload["calibration_source_error"] is None
        original_run_id = diagnostic_payload["run_id"]
        original_attempts = diagnostic_payload["attempts"]
        # The production runner reports the provider failure and then its outer
        # exception path reports again.  The latter must remain idempotent: one
        # run, one directory, and the first causal reason/ring are retained.
        daemon.notify_native_measurement_failed(backend.identity, "outer native calibration failure")
        diagnostic_dirs = list((tmp_path / "native-observation-diagnostics").iterdir())
        assert len(diagnostic_dirs) == 1
        refreshed = json.loads(diagnostic_path.read_text())
        assert refreshed["run_id"] == original_run_id
        assert refreshed["failure"]["reason"] == diagnostic_payload["failure"]["reason"]
        assert refreshed["attempts"] == original_attempts
        assert stat.S_IMODE(diagnostic_path.stat().st_mode) == 0o600
        _assert_native_provider_cleanup(tmp_path, backend, daemon)
    finally:
        daemon.request_shutdown()
        driver.close()


def test_runtime_native_observation_trace_write_failure_preserves_provider_error_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = _NativeProviderBackend(tmp_path, publication_fault="wrong_phase")
    daemon, _backend, driver, _controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    diagnostic = daemon._native_observation_diagnostic

    def fail_write(_payload: dict[str, object]) -> Path:
        raise OSError("diagnostic filesystem unavailable")

    monkeypatch.setattr(diagnostic, "_write_payload", fail_write)
    try:
        with pytest.raises(DriverError, match=re.escape("native construct/0 returned 'held'/0")):
            daemon._native_measurement_provider(backend.identity, "construct", 0)
        assert diagnostic.failure_path is None
        assert diagnostic._persistence_error is not None
        assert not list(tmp_path.rglob("offending-capture.png"))
        _assert_native_provider_cleanup(tmp_path, backend, daemon)
    finally:
        daemon.request_shutdown()
        driver.close()


def test_runtime_native_observation_cleanup_failure_is_retained_and_traced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = _NativeProviderBackend(tmp_path, publication_fault="wrong_phase")
    daemon, _backend, driver, _controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    with daemon._native_construction_lock:
        daemon._native_construction_handshake = {"state": "running"}
        daemon._native_construction_reset_history_locked()
        daemon._native_construction_start_context_locked(generation=4, deferred=False)
    original_remove = daemon._remove_native_capture
    monkeypatch.setattr(daemon, "_remove_native_capture", lambda _path: None)
    try:
        with pytest.raises(DriverError, match="native construct/0 returned 'held'/0"):
            daemon._native_measurement_provider(backend.identity, "construct", 0)
        diagnostic_path = daemon._native_observation_diagnostic.failure_path
        assert diagnostic_path is not None and diagnostic_path.is_file()
        payload = json.loads(diagnostic_path.read_text())
        attempt = payload["attempts"][-1]
        assert attempt["release_outcome"] == "retained"
        assert attempt["spans"]["cleanup"]["outcome"] == "failed"
        assert payload["failure"]["reason"] == "native construct/0 returned 'held'/0"
    finally:
        monkeypatch.setattr(daemon, "_remove_native_capture", original_remove)
        daemon.request_shutdown()
        driver.close()


def test_runtime_native_observation_identity_mutation_preserves_error_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = _NativeProviderBackend(tmp_path)
    daemon, _backend, driver, _controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    original_capture = backend.capture

    def mutate_during_capture(path: Path, **kwargs: object) -> WindowIdentity:
        captured = original_capture(path, **kwargs)
        backend.identity = replace(backend.identity, fingerprint="mutated-identity")
        return captured

    monkeypatch.setattr(backend, "capture", mutate_during_capture)
    try:
        identity = backend.identity
        with pytest.raises(DriverError, match="native client identity changed during operator wait"):
            constructed = daemon._native_measurement_provider(identity, "construct", 0)
            daemon.release_native_capture(Path(constructed.capture_path))
            daemon._native_measurement_provider(identity, "held", 0)
        _assert_native_provider_cleanup(tmp_path, backend, daemon)
    finally:
        daemon.request_shutdown()
        driver.close()


def test_runtime_native_provider_cached_publication_times_out_cleanly(tmp_path: Path) -> None:
    backend = _NativeProviderBackend(tmp_path)
    daemon, _backend, driver, _controller, _config, _clock = _runtime_daemon(
        tmp_path,
        backend=backend,
        journal_changes={"state": ControllerState.NATIVE_CALIBRATION.value, "generation": 4},
        lease_path=tmp_path / "native-provider.lock",
    )
    try:
        constructed = daemon._native_measurement_provider(backend.identity, "construct", 0)
        daemon.release_native_capture(Path(constructed.capture_path))
        backend.advance_cached_clock = True
        with pytest.raises(DriverError, match="did not produce the requested fresh frame"):
            daemon._native_measurement_provider(backend.identity, "held", 0)
        _assert_native_provider_cleanup(tmp_path, backend, daemon)
    finally:
        daemon.request_shutdown()
        driver.close()
