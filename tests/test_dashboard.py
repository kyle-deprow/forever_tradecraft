"""Executable, browser-independent tests for the paper dashboard page."""

import json
import shutil
import subprocess
from pathlib import Path

from crowley.trading.engine import _allocate_capital

ROOT = Path(__file__).parents[1]
DASHBOARD = ROOT / "src/crowley/server/static/dashboard.html"


def _node(script: str) -> dict:
    node = shutil.which("node")
    assert node is not None, "node is required for dashboard tests"
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _pure_script() -> str:
    html = DASHBOARD.read_text(encoding="utf-8")
    start_marker = "/* DASHBOARD PURE LOGIC START */"
    end_marker = "/* DASHBOARD PURE LOGIC END */"
    start = html.index(start_marker) + len(start_marker)
    end = html.index(end_marker, start)
    return html[start:end]


def _emit_script(body: str) -> str:
    return f"""
{_pure_script()}
function emit(value) {{
  console.log(JSON.stringify(value, (_, item) => typeof item === "bigint" ? item.toString() : item));
}}
{body}
"""


def _detail() -> dict:
    return {
        "name": "large-capital",
        "house": "test-house",
        "client_build": "1.60.1.70450",
        "start_t": 100,
        "capital_copper": "9007199254740993",
        "strategies": ["alpha", "beta"],
        "weights": ["1", "2"],
        "demand_share": "1/2",
        "created_at": "2026-01-01T00:00:00Z",
        "latest_step_t": 100,
        "latest_total_equity": "120000",
        "latest_total_realized": "20000",
        "pending_step_t": 200,
        "curve": [
            {
                "t": 100,
                "equity": {"alpha": "40000", "beta": "80000", "total": "120000"},
                "realized": {"alpha": "5000", "beta": "15000", "total": "20000"},
                "cash": {"alpha": "40000", "beta": "80000", "total": "120000"},
            }
        ],
        "recent_intents": [
            {
                "t": 100,
                "strategy": "alpha",
                "ordinal": 0,
                "intent": {"type": "Buy", "item_id": 2319, "max_unit_price": "27000", "quantity": 24},
                "outcome": "executed",
                "detail": {"filled": 24},
            }
        ],
        "pending": {
            "t": 200,
            "sweep_key": "pending",
            "intents": {"beta": [{"type": "VendorBuy", "item_id": 2319, "quantity": 3}]},
        },
    }


def test_exact_dashboard_logic_and_engine_allocation():
    cases = [
        (100000, ["1", "2"]),
        (7, ["1", "1", "1"]),
        (9007199254740993, ["1/3", "2/3"]),
        (100000000000000000000, ["2", "3", "5"]),
    ]
    detail = _detail()
    actual = _node(
        _emit_script(
            f"""
            const detail = {json.dumps(detail)};
            const allocationInputs = {json.dumps([[str(capital), weights] for capital, weights in cases])};
            const broken = JSON.parse(JSON.stringify(detail));
            broken.curve[0].equity.alpha = "not-copper";
            let malformed = "";
            try {{ validateRunDetail(broken); }} catch (error) {{ malformed = error.message; }}
            let numberRejected = "";
            try {{ parseExactRational(27000); }} catch (error) {{ numberRejected = error.message; }}
            validateRunDetail(detail);
            emit({{
              formats: [formatCopperAsGold("27000"), formatCopperAsGold("12345/2"), formatCopperAsGold("-27000"), formatCopperAsGold("9007199254740993")],
              returns: formatReturnPercent("120000", "100000"),
              allocations: allocationInputs.map(([capital, weights]) => allocateCapitalExact(capital, weights).map((share) => share.numerator.toString())),
              performance: buildPerformanceModel(detail).rows.map((row) => ({{ strategy: row.strategy, start: row.start.numerator.toString(), equity: row.equity.numerator.toString(), returnValue: formatReturnPercent(row.equity, row.start) }})),
              decisions: buildDecisionModel(detail),
              pending: buildPendingModel(detail),
              malformed,
              numberRejected,
            }});
            """
        )
    )
    assert actual["formats"] == ["2.70g", "0.62g", "−2.70g", "900719925474.10g"]
    assert actual["returns"] == "20.00%"
    for (capital, weights), shares in zip(cases, actual["allocations"], strict=True):
        assert shares == [str(share) for share in _allocate_capital(capital, weights)]
    assert actual["performance"] == [
        {"strategy": "alpha", "start": "3002399751580331", "equity": "40000", "returnValue": "−100.00%"},
        {"strategy": "beta", "start": "6004799503160662", "equity": "80000", "returnValue": "−100.00%"},
    ]
    assert actual["decisions"][0]["action"] == "Buy ≤ 2.70g ×24 (item 2319)"
    assert actual["pending"] == [{"strategy": "beta", "action": "Buy from vendor ×3 (item 2319)"}]
    assert "equity" in actual["malformed"]
    assert "exact copper string" in actual["numberRejected"]


def _full_script() -> str:
    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.index("<script>") + len("<script>")
    end = html.index("</script>", start)
    return html[start:end]


def _fake_dom_script(detail: dict) -> str:
    return f"""
class FakeClassList {{
  constructor() {{ this.values = new Set(); }}
  toggle(name, enabled) {{ if (enabled) this.values.add(name); else this.values.delete(name); }}
  contains(name) {{ return this.values.has(name); }}
}}
class FakeNode {{
  constructor(id = "") {{ this.id = id; this.children = []; this.innerHTML = ""; this.hidden = false; this.value = ""; this.classList = new FakeClassList(); }}
  set textContent(value) {{ this._textContent = String(value); this.innerHTML = this._textContent.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;"); }}
  get textContent() {{ return this._textContent || ""; }}
  append(...nodes) {{ this.children.push(...nodes); }}
  appendChild(node) {{ this.children.push(node); return node; }}
  replaceChildren(...nodes) {{ this.children = [...nodes]; }}
  addEventListener() {{}}
  setAttribute() {{}}
  querySelector(selector) {{ return this[selector === "tbody" ? "tbody" : selector === "tfoot" ? "tfoot" : "queryChild"]; }}
}}
const nodes = new Map();
for (const id of ["token-form", "forget-token", "token", "status", "run-select", "dashboard-content", "run-meta", "chart", "sparks", "decisions-empty", "pending-content"]) nodes.set(id, new FakeNode(id));
const performanceTable = new FakeNode("performance-table");
performanceTable.tbody = new FakeNode("performance-body");
performanceTable.tfoot = new FakeNode("performance-foot");
nodes.set("performance-table", performanceTable);
const decisionsTable = new FakeNode("decisions-table");
decisionsTable.tbody = new FakeNode("decisions-body");
nodes.set("decisions-table", decisionsTable);
global.document = {{
  getElementById: (id) => nodes.get(id),
  createElement: () => new FakeNode(),
  createElementNS: () => new FakeNode(),
}};
global.localStorage = {{ getItem: () => "", setItem: () => {{}}, removeItem: () => {{}} }};
global.window = {{ prompt: () => "", setInterval: () => 0 }};
global.fetch = () => {{ throw new Error("fetch should not run in this rendering test"); }};
{_full_script()}
const detail = {json.dumps(detail)};
const valid = window.__crowleyDashboardTest.renderDashboardDetail(detail);
const validRows = nodes.get("performance-table").tbody.innerHTML;
const validDecisions = nodes.get("decisions-table").tbody.innerHTML;
const validPending = nodes.get("pending-content").children.map((child) => child.innerHTML).join("|");
nodes.get("performance-table").tbody.innerHTML = "";
nodes.get("decisions-table").tbody.innerHTML = "";
nodes.get("pending-content").replaceChildren();
const malformed = JSON.parse(JSON.stringify(detail));
malformed.curve[0].equity.alpha = "not-copper";
const malformedResult = window.__crowleyDashboardTest.renderDashboardDetail(malformed);
emit({{
  valid,
  validRows,
  validDecisions,
  validPending,
  malformedResult,
  malformedStatus: nodes.get("status").textContent,
  malformedStatusIsError: nodes.get("status").classList.contains("error"),
  malformedRows: nodes.get("performance-table").tbody.innerHTML,
}});
"""


def test_real_rendering_and_error_path_use_a_fake_dom():
    detail = _detail()
    script = _fake_dom_script(detail)
    script = script.replace(
        'global.window = { prompt: () => "", setInterval: () => 0 };',
        'global.window = { prompt: () => "", setInterval: () => 0 };\nfunction emit(value) { console.log(JSON.stringify(value)); }',
    )
    actual = _node(script)
    assert actual["valid"] is True
    assert "alpha" in actual["validRows"] and "beta" in actual["validRows"]
    assert "300239975158.03g" in actual["validRows"]
    assert "Buy ≤ 2.70g ×24 (item 2319)" in actual["validDecisions"]
    assert "beta" in actual["validPending"] and "Buy from vendor ×3 (item 2319)" in actual["validPending"]
    assert actual["malformedResult"] is False
    assert actual["malformedStatusIsError"] is True
    assert "exact copper string" in actual["malformedStatus"]
    assert actual["malformedRows"] == ""
