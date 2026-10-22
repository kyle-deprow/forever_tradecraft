import json
from pathlib import Path

import httpx
import pytest

from crowley.companion.config import CompanionSettings
from crowley.companion.sync import Companion, State
from crowley.core import savedvars
from crowley.core.luawriter import render_assignment
from crowley.core.queue import build_queue, render_queue_lua
from crowley.core.watchlist import load_catalog

from .test_core import raw_scan
from .wow_harness import WowClient

FIXTURE = Path(__file__).parent / "fixtures/native-construction-unknown-savedvars.lua"


def write_savedvars(path, scans, probe=None, reference=None, account=None, executions=None):
    db = {"scans": {scan["id"]: scan for scan in scans}}
    if probe is not None:
        db["probe"] = probe
    if reference is not None:
        db["reference"] = reference
    if account is not None:
        db["account"] = account
    if executions is not None:
        db["executions"] = executions
    path.write_text(render_assignment("CrowleyDB", db, header="test"))


@pytest.fixture
def companion(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    settings = CompanionSettings(wow_dir=tmp_path, server_url="http://test", api_token="test-token")
    saved = tmp_path / "WTF/Account/Test/SavedVariables/Crowley.lua"
    saved.parent.mkdir(parents=True)
    settings.data_lua.parent.mkdir(parents=True)
    instance = Companion(settings)
    instance.client.close()
    try:
        yield instance, saved
    finally:
        instance.client.close()


@pytest.mark.parametrize("failure", ["s1", "s2", "probe"])
def test_retries_failed_file_without_reuploading_successful_scans(companion, failure):
    instance, saved = companion
    probe = {"at": 1760000000}
    write_savedvars(saved, [raw_scan(id="s1"), raw_scan(id="s2")], probe)
    attempts = []
    uploaded = []
    probes = []
    failed = False
    plan = load_catalog().scan_plan()

    def respond(request):
        nonlocal failed
        body = json.loads(request.content)
        if request.url.path == "/v1/scans":
            target = body["id"]
        elif request.url.path == "/v1/probes":
            target = "probe"
        else:
            return httpx.Response(
                200,
                json={"generatedAt": 1, "ackedScans": uploaded.copy(), "shoppingLists": [], "scanPlan": plan},
            )
        attempts.append(target)
        if target == failure and not failed:
            failed = True
            raise httpx.ConnectError("temporary outage", request=request)
        if target == "probe":
            probes.append(body)
            return httpx.Response(200, json={"status": "ok"})
        uploaded.append(target)
        return httpx.Response(200, json={"house": "us-normal-alliance", "listings": 2, "status": "created"})

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    instance.tick()  # First observation: wait for the file to hold still.
    assert attempts == []
    with pytest.raises(httpx.ConnectError):
        instance.tick()
    instance.tick()  # Unchanged file must be retried on the next poll.

    assert uploaded == ["s1", "s2"]
    assert probes == [probe]
    assert attempts.count(failure) == 2
    assert all(attempts.count(target) == 1 for target in {"s1", "s2", "probe"} - {failure})
    persisted = State.load(instance.state_file)
    assert set(persisted.uploaded) == {"s1", "s2"}
    assert persisted.probes == [probe["at"]]
    data = savedvars.load_file(instance.settings.data_lua)["CROWLEY_DATA"]
    assert data["ackedScans"] == ["s1", "s2"]
    assert data["scanPlan"] == plan

    instance.tick()
    assert len(attempts) == 4  # Completed files stay processed.


def test_changed_file_waits_for_stability_after_failed_upload(companion):
    instance, saved = companion
    write_savedvars(saved, [raw_scan(id="s1")])
    attempts = []

    def respond(request):
        if request.url.path == "/v1/scans":
            attempts.append(json.loads(request.content)["id"])
            if len(attempts) == 1:
                raise httpx.ConnectError("temporary outage", request=request)
            return httpx.Response(
                200, json={"house": "us-normal-alliance", "listings": 2, "status": "created"}
            )
        return httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    instance.tick()
    with pytest.raises(httpx.ConnectError):
        instance.tick()

    write_savedvars(saved, [raw_scan(id="s1"), raw_scan(id="s2")])
    instance.tick()
    assert attempts == ["s1"]  # Changed content needs a new stability interval.
    instance.tick()
    assert attempts == ["s1", "s1", "s2"]


def test_unknown_native_marker_fixture_preserves_scan_wire_and_is_not_uploaded(companion):
    instance, saved = companion
    fixture = savedvars.load_file(FIXTURE)
    marker = fixture["CrowleyDB"]["nativeConstruction"]
    scan = fixture["CrowleyDB"]["scans"]["fixture-native-construction"]
    assert marker["state"] == "mystery"
    assert marker["extra"] == "must-not-leak"
    original_payload = scan["payload"]
    saved.write_bytes(FIXTURE.read_bytes())
    uploaded = []

    def respond(request):
        if request.url.path == "/v1/scans":
            body = json.loads(request.content)
            uploaded.append(body)
            return httpx.Response(
                200, json={"house": "us-normal-alliance", "listings": 1, "status": "created"}
            )
        return httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    instance.once()
    assert len(uploaded) == 1
    assert uploaded[0]["payload"] == original_payload
    assert "nativeConstruction" not in uploaded[0]


def test_item_reference_upload_is_remembered_and_retried_on_error(companion):
    instance, saved = companion
    reference = {
        "format": 1,
        "id": "us-normal-alliance-1760000000-Tester-0001",
        "house": {
            "region": "us",
            "ruleset": "normal",
            "faction": "alliance",
            "source": "auto",
            "key": "us-normal-alliance",
        },
        "context": {
            "character": "Tester",
            "realm": "Normal",
            "playerFaction": "Alliance",
            "zone": "Orgrimmar",
            "subzone": "",
            "locale": "enUS",
            "clientVersion": "1.60.1",
            "clientBuild": "70450",
            "interface": 16001,
            "addonVersion": "0.2.0",
        },
        "startedAt": 1760000000,
        "finishedAt": 1760000000,
        "ahOpen": False,
        "items": {
            "2589": {
                "itemID": 2589,
                "status": "ok",
                "info": {
                    "quality": 1,
                    "itemLevel": 0,
                    "minLevel": 0,
                    "classID": 7,
                    "subclassID": 0,
                    "maxStack": 20,
                    "sellPrice": 3,
                    "bindType": 0,
                    "expansionID": 1,
                    "isCraftingReagent": True,
                },
                "deposit": {"kind": "unqueried", "reason": "ah_closed"},
            }
        },
    }
    write_savedvars(saved, [], reference=reference)
    calls = []

    def respond(request):
        if request.url.path == "/v1/item-reference":
            calls.append(json.loads(request.content))
            return httpx.Response(200, json={"status": "created", "items": 1})
        return httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    instance.once()
    instance.once()
    assert len(calls) == 1
    assert State.load(instance.state_file).references == [reference["id"]]

    failure = httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(
            lambda request: (
                httpx.Response(302, text="redirect")
                if request.url.path == "/v1/item-reference"
                else httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})
            )
        ),
    )
    instance.client.close()
    instance.client = failure
    new_reference = dict(reference, id="us-normal-alliance-1760000000-Tester-0002")
    write_savedvars(saved, [], reference=new_reference)
    with pytest.raises(RuntimeError, match="server rejected item reference"):
        instance.once()
    assert State.load(instance.state_file).references == [reference["id"]]

    successful_calls = []

    def succeed(request):
        if request.url.path == "/v1/item-reference":
            successful_calls.append(json.loads(request.content)["id"])
            return httpx.Response(200, json={"status": "created", "items": 1})
        return httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})

    instance.client.close()
    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(succeed))
    instance.once()
    assert successful_calls == [new_reference["id"]]
    assert State.load(instance.state_file).references == [reference["id"], new_reference["id"]]
    # once() reprocesses the file unconditionally, so only the remembered id prevents a second upload.
    instance.once()
    assert successful_calls == [new_reference["id"]]


def test_account_upload_is_remembered_and_retried_on_error(companion):
    instance, saved = companion
    wow = WowClient(money=321)
    wow.login()
    account = savedvars.loads(wow.saved_variables())["CrowleyDB"]["account"]
    write_savedvars(saved, [], account=account)
    attempts = []
    failed = False

    def respond(request):
        nonlocal failed
        if request.url.path == "/v1/account-state":
            attempts.append(json.loads(request.content)["id"])
            if not failed:
                failed = True
                raise httpx.ConnectError("temporary outage", request=request)
            return httpx.Response(200, json={"status": "created", "items": 0})
        return httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    with pytest.raises(httpx.ConnectError):
        instance.once()
    assert State.load(instance.state_file).accounts == []

    instance.once()
    instance.once()
    assert attempts == [account["id"], account["id"]]
    assert State.load(instance.state_file).accounts == [account["id"]]


def test_account_upload_rejects_non_2xx_and_retries(companion):
    instance, saved = companion
    wow = WowClient(money=654)
    wow.login()
    account = savedvars.loads(wow.saved_variables())["CrowleyDB"]["account"]
    write_savedvars(saved, [], account=account)
    attempts = 0

    def respond(request):
        nonlocal attempts
        if request.url.path == "/v1/account-state":
            attempts += 1
            if attempts == 1:
                return httpx.Response(422, text="malformed account")
            return httpx.Response(200, json={"status": "created", "items": 0})
        return httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    with pytest.raises(RuntimeError, match="server rejected account state"):
        instance.once()
    assert State.load(instance.state_file).accounts == []

    instance.once()
    assert attempts == 2
    assert State.load(instance.state_file).accounts == [account["id"]]


def test_queue_lua_is_written_only_when_content_changes(companion, monkeypatch):
    instance, _ = companion
    instance.settings.house_key = "us-normal-alliance"
    instance.settings.character = "Tester"
    queue = build_queue(
        {
            "house": "us-normal-alliance",
            "character": "Tester",
            "generatedAt": 1_700_000_000,
            "expiresAt": 1_700_000_600,
            "actions": [{"seq": 1, "kind": "vendor_buy", "itemID": 1, "quantity": 1}],
        }
    )
    writes = []

    def record_write(path, text):
        writes.append((path, text))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    monkeypatch.setattr("crowley.companion.sync.atomic_write", record_write)
    instance.client = httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=queue)),
    )
    instance.write_queue()
    instance.write_queue()
    assert len(writes) == 1
    assert savedvars.load_file(instance.settings.queue_lua)["CROWLEY_QUEUE"] == queue


def test_unconfigured_queue_is_cleared_even_when_addon_data_fails(companion):
    instance, saved = companion
    write_savedvars(saved, [])
    stale = build_queue(
        {
            "house": "us-normal-alliance",
            "character": "Tester",
            "generatedAt": 1_700_000_000,
            "expiresAt": 1_700_000_600,
            "actions": [{"seq": 1, "kind": "vendor_buy", "itemID": 1, "quantity": 1}],
        }
    )
    instance.settings.queue_lua.write_text(render_queue_lua(stale))

    def respond(request):
        if request.url.path == "/v1/addon-data":
            raise httpx.ConnectError("temporary outage", request=request)
        raise AssertionError(f"unexpected request {request.url}")

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    with pytest.raises(httpx.ConnectError):
        instance.once()
    assert savedvars.load_file(instance.settings.queue_lua) == {"CROWLEY_QUEUE": False}


def test_execution_upload_retries_then_is_remembered(companion):
    instance, saved = companion
    queue = build_queue(
        {
            "house": "us-normal-alliance",
            "character": "Tester",
            "generatedAt": 1_700_000_000,
            "expiresAt": 1_700_000_600,
            "actions": [{"seq": 1, "kind": "vendor_buy", "itemID": 1, "quantity": 1}],
        }
    )
    execution = {
        "queueId": queue["queueId"],
        "house": queue["house"],
        "character": queue["character"],
        "results": [],
    }
    write_savedvars(saved, [], executions={queue["queueId"]: execution})
    attempts = 0

    def respond(request):
        nonlocal attempts
        if request.url.path == "/v1/executions":
            attempts += 1
            if attempts == 1:
                raise httpx.ConnectError("temporary outage", request=request)
            return httpx.Response(200, json={"status": "created"})
        return httpx.Response(200, json={"generatedAt": 1, "ackedScans": [], "shoppingLists": []})

    instance.client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    with pytest.raises(httpx.ConnectError):
        instance.once()
    instance.once()
    instance.once()
    assert attempts == 2
    assert queue["queueId"] in State.load(instance.state_file).executions
