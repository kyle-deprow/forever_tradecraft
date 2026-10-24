// Offline DB2 + DBCache exporter. Runtime input is only the local client.
using System.Globalization;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using DBCD;
using DBCD.IO;
using DBCD.IO.Common;
using DBCD.Providers;
using TACTSharp;

var opt = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
for (var i = 0; i < args.Length; i += 2)
{
    if (i + 1 >= args.Length) throw new ArgumentException($"missing value for {args[i]}");
    opt[args[i].TrimStart('-')] = args[i + 1];
}
string Required(string key) => opt.TryGetValue(key, out var value) ? value : throw new ArgumentException($"missing --{key}");

var wow = Required("wow");
var product = Required("product");
var productDir = Required("productdir");
var expectedBuild = Required("expected-build");
var outDir = Required("out");
var cacheDir = Required("cache");
var dbdDir = Required("dbd");
var tables = Required("tables").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
Directory.CreateDirectory(Path.Combine(outDir, "db2"));
Directory.CreateDirectory(Path.Combine(outDir, "csv"));
Directory.CreateDirectory(cacheDir);

var buildInfoPath = Path.Combine(wow, ".build.info");
var buildInfoBytes = File.ReadAllBytes(buildInfoPath);
var buildInfoLines = Encoding.UTF8.GetString(buildInfoBytes).Split('\n', StringSplitOptions.RemoveEmptyEntries);
if (buildInfoLines.Length < 2) throw new InvalidDataException(".build.info has no rows");
var headers = buildInfoLines[0].TrimEnd('\r').Split('|').Select(x => x.Split('!')[0]).ToArray();
var activeRows = buildInfoLines.Skip(1).Select(line => line.TrimEnd('\r').Split('|'))
    .Where(fields => fields.Length == headers.Length)
    .Select(fields => headers.Zip(fields).ToDictionary(x => x.First, x => x.Second))
    .Where(row => row.GetValueOrDefault("Product") == product && row.GetValueOrDefault("Active") == "1")
    .ToList();
if (activeRows.Count != 1) throw new InvalidDataException($"expected one active {product} row, got {activeRows.Count}");
var buildInfo = activeRows[0];
var version = buildInfo["Version"];
if (version != expectedBuild) throw new InvalidDataException($"client build {version} is not {expectedBuild}");
var buildNumber = int.Parse(version.Split('.')[3], CultureInfo.InvariantCulture);
var flavorPath = Path.Combine(wow, productDir, ".flavor.info");
var flavorLines = File.ReadAllLines(flavorPath);
if (flavorLines.Length < 2 || flavorLines[1].Trim() != product)
    throw new InvalidDataException($".flavor.info does not identify {product}");

var dbcachePath = Path.Combine(wow, productDir, "Cache", "ADB", "enUS", "DBCache.bin");
byte[] dbcache;
using (var stream = new FileStream(dbcachePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
{
    dbcache = new byte[stream.Length];
    stream.ReadExactly(dbcache);
}
var hotfix = new HotfixReader(new MemoryStream(dbcache));
if (hotfix.BuildId != buildNumber) throw new InvalidDataException($"DBCache build {hotfix.BuildId} != client build {buildNumber}");

var build = new BuildInstance();
build.Settings.BaseDir = wow;
build.Settings.Product = product;
build.Settings.TryCDN = false;
build.Settings.ListfileFallback = false;
build.Settings.CacheDir = cacheDir;
build.Settings.Locale = RootInstance.LocaleFlags.enUS;
build.cdn.ProductDirectory = buildInfo["CDN Path"];
build.LoadConfigs(buildInfo["Build Key"], buildInfo["CDN Key"]);
build.Load();

var fdidsPath = Required("fdids");
var fdidsBytes = File.ReadAllBytes(fdidsPath);
var fdidsSha256 = Convert.ToHexString(SHA256.HashData(fdidsBytes)).ToLowerInvariant();
var fdids = File.ReadAllLines(fdidsPath)
    .Where(line => !string.IsNullOrWhiteSpace(line))
    .Select(line => line.Split(';'))
    .ToDictionary(parts => Path.GetFileNameWithoutExtension(parts[1]).ToLowerInvariant(), parts => uint.Parse(parts[0], CultureInfo.InvariantCulture));
var jenkins = new Jenkins96();
var provider = new MemProvider();
var dbcd = new DBCD.DBCD(provider, new FilesystemDBDProvider(dbdDir));
var summary = new Dictionary<string, object>();

byte[] Extract(string table)
{
    if (!fdids.TryGetValue(table.ToLowerInvariant(), out var fdid)) throw new InvalidDataException($"no pinned FDID for {table}");
    var byName = build.Root.GetEntriesByLookup(jenkins.ComputeHash($"DBFilesClient\\{table}.db2"));
    if (byName.Count > 0 && byName[0].fileDataID != fdid)
        throw new InvalidDataException($"FDID mismatch for {table}: pinned {fdid}, root {byName[0].fileDataID}");
    var bytes = build.OpenFileByFDID(fdid);
    if (bytes.Length < 4) throw new InvalidDataException($"empty DB2 for {table}");
    provider.Files[table] = bytes;
    File.WriteAllBytes(Path.Combine(outDir, "db2", table + ".db2"), bytes);
    return bytes;
}

static int HotfixOp(IHotfixEntry row)
{
    var inner = row.GetType().GetField("m_hotfixEntry", BindingFlags.NonPublic | BindingFlags.Instance)?.GetValue(row)
        ?? throw new InvalidDataException("DBCD hotfix internals changed");
    var op = inner.GetType().GetField("op", BindingFlags.NonPublic | BindingFlags.Instance)?.GetValue(inner)
        ?? throw new InvalidDataException("DBCD hotfix op field changed");
    return Convert.ToInt32(op, CultureInfo.InvariantCulture);
}

static string FormatValue(object? value) => value switch
{
    null => "",
    float valueFloat => valueFloat.ToString("R", CultureInfo.InvariantCulture),
    double valueDouble => valueDouble.ToString("R", CultureInfo.InvariantCulture),
    string valueString => valueString.Contains(',') || valueString.Contains('"') || valueString.Contains('\n') || valueString.Contains('\r')
        ? $"\"{valueString.Replace("\"", "\"\"")}\"" : valueString,
    IFormattable formattable => formattable.ToString(null, CultureInfo.InvariantCulture) ?? "",
    _ => value.ToString() ?? "",
};

static string RowKey(DBCDRow row, string[] columns) => string.Join("|", columns.Select(column =>
    row[column] is Array array ? string.Join(";", array.Cast<object>().Select(FormatValue)) : FormatValue(row[column])));

(IDBCDStorage Storage, Dictionary<string, object> Info) LoadTable(string table)
{
    var bytes = Extract(table);
    var tableHash = new DBParser(new MemoryStream(bytes)).TableHash;
    var storage = dbcd.Load(table, version);
    var columns = storage.AvailableColumns;
    var baseRows = storage.ToDictionary().ToDictionary(pair => pair.Key, pair => RowKey(pair.Value, columns));
    var operations = new SortedDictionary<int, int>();
    var results = new Dictionary<string, int>();
    var touched = new HashSet<int>();
    var log = new List<(int Id, int Push, int Op, int Size, string Result)>();
    var entries = 0;
    var pushed = 0;
    var cached = 0;
    storage.ApplyingHotfixes(hotfix, (row, shouldDelete) =>
    {
        entries++;
        var op = HotfixOp(row);
        operations[op] = operations.GetValueOrDefault(op) + 1;
        if (row.PushId == -1) cached++; else pushed++;
        var result = HotfixReader.DefaultProcessor(row, shouldDelete);
        results[result.ToString()] = results.GetValueOrDefault(result.ToString()) + 1;
        touched.Add(row.RecordId);
        log.Add((row.RecordId, row.PushId, op, row.DataSize, result.ToString()));
        return result;
    });
    var added = 0;
    var changed = 0;
    var identical = 0;
    var deleted = 0;
    var absentDeletes = 0;
    foreach (var id in touched)
    {
        var wasPresent = baseRows.TryGetValue(id, out var before);
        var isPresent = storage.TryGetValue(id, out var after);
        if (!wasPresent && isPresent) added++;
        else if (wasPresent && !isPresent) deleted++;
        else if (!wasPresent) absentDeletes++;
        else if (RowKey(after!, columns) == before) identical++;
        else changed++;
    }
    Directory.CreateDirectory(Path.Combine(outDir, "hotfix-log"));
    using (var writer = new StreamWriter(Path.Combine(outDir, "hotfix-log", table + ".csv"), false, new UTF8Encoding(false)))
    {
        writer.WriteLine("RecordID,PushID,Op,DataSize,Result,InBase,InFinal,Change");
        foreach (var item in log)
        {
            var wasPresent = baseRows.TryGetValue(item.Id, out var before);
            var isPresent = storage.TryGetValue(item.Id, out var after);
            var change = !wasPresent && isPresent ? "added" : wasPresent && !isPresent ? "deleted" : !wasPresent ? "noop" : RowKey(after!, columns) == before ? "identical" : "changed";
            writer.WriteLine($"{item.Id},{item.Push},{item.Op},{item.Size},{item.Result},{wasPresent},{isPresent},{change}");
        }
    }

    var encrypted = storage.GetEncryptedSections();
    var encryptedIds = storage.GetEncryptedIDs();
    Directory.CreateDirectory(Path.Combine(outDir, "encrypted-ids"));
    File.WriteAllLines(Path.Combine(outDir, "encrypted-ids", table + ".csv"),
        new[] { "TactKeyLookup,KeyKnown,RecordID,PresentAfterHotfix" }.Concat(
            encryptedIds.SelectMany(pair => pair.Value.Select(id => $"{pair.Key:X16},{KeyService.TryGetKey(pair.Key, out _)},{id},{storage.ContainsKey(id)}"))));
    var encryptedInfo = encrypted.Select(pair =>
    {
        var ids = encryptedIds.TryGetValue(pair.Key, out var values) ? values : Array.Empty<int>();
        var known = KeyService.TryGetKey(pair.Key, out _);
        return new
        {
            key = pair.Key.ToString("X16"),
            sectionRecords = pair.Value,
            keyKnown = known,
            encryptedIds = ids.Length,
            encryptedIdsPresentAfterHotfix = ids.Count(storage.ContainsKey),
            hiddenIds = known ? Array.Empty<int>() : ids,
        };
    }).ToList();
    var info = new Dictionary<string, object>
    {
        ["fdid"] = fdids[table.ToLowerInvariant()],
        ["tableHash"] = tableHash.ToString("X8"),
        ["layoutHash"] = storage.LayoutHash.ToString("X8"),
        ["baseRows"] = baseRows.Count,
        ["finalRows"] = storage.Count,
        ["hotfixEntries"] = entries,
        ["hotfixEntriesPushed"] = pushed,
        ["hotfixEntriesPushIdMinus1"] = cached,
        ["hotfixOps"] = operations.ToDictionary(pair => pair.Key.ToString(CultureInfo.InvariantCulture), pair => pair.Value),
        ["hotfixResults"] = results,
        ["distinctRecordsTouched"] = touched.Count,
        ["hotfixAdded"] = added,
        ["hotfixChanged"] = changed,
        ["hotfixIdentical"] = identical,
        ["hotfixDeleted"] = deleted,
        ["deletesOfAbsentRows"] = absentDeletes,
        ["rowsHiddenByMissingKeys"] = encryptedInfo.Sum(item => item.hiddenIds.Length),
        ["hiddenIds"] = encryptedInfo.SelectMany(item => item.hiddenIds).Distinct().OrderBy(id => id).ToArray(),
        ["encryptedSections"] = encryptedInfo,
    };
    return (storage, info);
}

// TACT keys are read from the client's own TactKeyLookup/TactKey tables only.
var (lookupStorage, lookupInfo) = LoadTable("TactKeyLookup");
var (keyStorage, keyInfo) = LoadTable("TactKey");
var keysLoaded = 0;
foreach (var pair in lookupStorage.ToDictionary())
{
    if (!keyStorage.TryGetValue(pair.Key, out var keyRow)) continue;
    var name = BitConverter.ToUInt64(((byte[])pair.Value["TACTID"]).ToArray());
    var key = (byte[])keyRow["Key"];
    if (key.All(value => value == 0)) continue;
    KeyService.SetKey(name, key);
    keysLoaded++;
}
summary["_tactKeys"] = new { keysLoaded, lookupInfo, keyInfo };

foreach (var table in tables)
{
    var (storage, info) = LoadTable(table);
    var columns = storage.AvailableColumns;
    var first = storage.Values.FirstOrDefault();
    var header = new List<string>();
    foreach (var column in columns)
    {
        if (first is not null && first[column] is Array array)
            for (var index = 0; index < array.Length; index++) header.Add($"{column}[{index}]");
        else header.Add(column);
    }
    using (var writer = new StreamWriter(Path.Combine(outDir, "csv", table + ".csv"), false, new UTF8Encoding(false)))
    {
        writer.WriteLine(string.Join(',', header));
        foreach (var id in storage.Keys.OrderBy(value => value))
        {
            var row = storage[id];
            var values = new List<string>();
            foreach (var column in columns)
            {
                if (row[column] is Array array) values.AddRange(array.Cast<object>().Select(FormatValue));
                else values.Add(FormatValue(row[column]));
            }
            writer.WriteLine(string.Join(',', values));
        }
    }
    info["columns"] = header.Count;
    info["csvSha256"] = Sha256(Path.Combine(outDir, "csv", table + ".csv"));
    summary[table] = info;
}

var buildInfoSha256 = Convert.ToHexString(SHA256.HashData(buildInfoBytes)).ToLowerInvariant();
var dbcacheSha256 = Convert.ToHexString(SHA256.HashData(dbcache)).ToLowerInvariant();
var exportKey = $"{version}-{dbcacheSha256[..12]}";
var manifest = new Dictionary<string, object>
{
    ["manifest_version"] = 1,
    ["export_key"] = exportKey,
    ["client_build"] = version,
    ["product"] = product,
    ["build_name"] = build.BuildConfig.Values["build-name"][0],
    ["build_key"] = buildInfo["Build Key"],
    ["cdn_key"] = buildInfo["CDN Key"],
    ["build_info_sha256"] = buildInfoSha256,
    ["dbcache_sha256"] = dbcacheSha256,
    ["dbcache_build"] = hotfix.BuildId,
    ["dbcache_version"] = hotfix.Version,
    ["tool_pins"] = new Dictionary<string, string>
    {
        ["sdk_image"] = "mcr.microsoft.com/dotnet/sdk@sha256:747cbade5bfd918a175ac32f8f1d931edec2c7d0d5397a3de72eaef1ac1f66d2",
        ["runtime_image"] = "mcr.microsoft.com/dotnet/runtime@sha256:0cf09aaccf6a9f68900aed4c73fb28fe25bb59ec85de4dea08ba02240a8635f3",
        ["TACTSharp"] = "wowdev/TACTSharp@d89204e07fa062ccc8f2738ebd0209782912da48",
        ["DBCD"] = "wowdev/DBCD@e732093f8864240fc5884bd1bba6b02f3dfc0d56",
        ["DBDefsLib"] = "1.1.0",
        ["WoWDBDefs"] = "wowdev/WoWDBDefs@7eaa562b62037d12327543fe22719a59870bb905",
        ["fdids"] = "app/fdids.csv",
        ["fdids_sha256"] = fdidsSha256,
        ["listfile_release"] = "202610202236",
        ["listfile_sha256"] = "4af8062799478d6f7a038ac9b9f3df1d9d519230e369e1bb399ff0ab41507fd6",
    },
    ["tables"] = summary.Where(pair => pair.Key != "_tactKeys").ToDictionary(pair => pair.Key, pair => pair.Value),
};
File.WriteAllText(Path.Combine(outDir, "manifest.json"), JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true }));
File.WriteAllText(Path.Combine(outDir, "summary.json"), JsonSerializer.Serialize(summary, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine("done");

static string Sha256(string path)
{
    using var stream = File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
}

sealed class MemProvider : IDBCProvider
{
    public Dictionary<string, byte[]> Files { get; } = new();
    public Stream StreamForTableName(string tableName, string build) => new MemoryStream(Files[tableName]);
}
