import json

import httpx
import pytest

from crowley.companion.config import CompanionSettings
from crowley.companion.sync import Companion, State
from crowley.core import savedvars
from crowley.core.luawriter import render_assignment
from crowley.core.watchlist import load_catalog

from .test_core import raw_scan


def write_savedvars(path, scans, probe=None):
    db = {"scans": {scan["id"]: scan for scan in scans}}
    if probe is not None:
        db["probe"] = probe
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
