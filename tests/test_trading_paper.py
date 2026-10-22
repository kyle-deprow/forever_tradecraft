from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path

import psycopg
import pytest
from psycopg.types.json import Jsonb

from crowley.analysis.books import Book, Group
from crowley.trading import paper
from crowley.trading.api import Buy, Craft, ItemFacts, Recipe, VendorBuy
from crowley.trading.data import vendor_supply_ids
from crowley.trading.engine import run_backtest

DB_URL = os.environ.get("CROWLEY_TEST_DATABASE_URL")


class Script:
    name = "paper_test"
    professions = frozenset({"alchemy"})

    def __init__(self, actions):
        self.actions = actions

    def decide(self, market, account):
        return self.actions.get(market.sweep_index, ())


def _book(t: int, sweep_id: int) -> Book:
    return Book(
        t=t,
        groups=[Group("unit", Fraction(30), 5, 100_000)],
        item_id=7,
        sweep_id=sweep_id,
    )


def test_step_log_records_execution_effects_and_rejections():
    result = run_backtest(
        {7: [_book(0, 1), _book(900, 2)]},
        {},
        {7: ItemFacts(7, 0, None, None, 20, 0)},
        (),
        [Script({0: [Buy(7, 30, 5), Buy(7, 30, 5)]})],
        None,
        100,
        wind_down_hours=0,
    )

    decisions = result.step_log[0]["strategies"]["paper_test"]
    assert decisions[0] == {
        "intent": {"type": "Buy", "item_id": 7, "max_unit_price": 30, "quantity": 5},
        "outcome": "executed",
        "detail": {"filled": 3},
    }
    assert decisions[1]["outcome"] == "cash"
    assert decisions[1]["detail"] == {"filled": 0}


def test_step_log_records_actual_craft_times():
    recipe = Recipe(22, frozenset({"alchemy"}), ((8, 1),), ((9, 1),), None, 0, "test")
    facts = {
        7: ItemFacts(7, 0, None, None, 20, 0),
        8: ItemFacts(8, 0, 1, 1, 20, 0),
        9: ItemFacts(9, 0, None, None, 20, 0),
    }
    result = run_backtest(
        {7: [_book(0, 1), _book(900, 2)]},
        {},
        facts,
        (recipe,),
        [Script({0: [VendorBuy(8, 200), Craft(22, 200)]})],
        None,
        1_000,
        wind_down_hours=0,
    )

    decisions = result.step_log[0]["strategies"]["paper_test"]
    assert decisions[1]["outcome"] == "executed"
    assert decisions[1]["detail"] == {"times": 148}


def test_paper_timer_and_service_have_required_guards():
    root = Path(__file__).parents[1]
    service = (root / "deploy/crowley-paper-trading.service").read_text()
    timer = (root / "deploy/crowley-paper-trading.timer").read_text()
    assert "EnvironmentFile=%h/.config/crowley/paper.env" in service
    assert "UMask=0077" in service
    assert "NoNewPrivileges=true" in service
    assert "TimeoutStartSec=14min" in service
    assert "paper-step --name ${CROWLEY_PAPER_RUN}" in service
    assert "OnCalendar=*:0/15" in timer
    assert "Persistent=true" in timer


@pytest.mark.skipif(not DB_URL, reason="CROWLEY_TEST_DATABASE_URL not set")
def test_paper_step_replays_the_old_latest_step_when_a_sweep_arrives(monkeypatch):
    """A zero-hour wind-down must not make the previous latest step diverge."""

    from crowley.server.db import migrate

    suffix = uuid.uuid4().hex
    house_key = f"paper-regression-{suffix}"
    export_key = f"paper-regression-{suffix}"
    plan_hash = hashlib.sha256(f"plan-{suffix}".encode()).hexdigest()
    run_name = f"paper-regression-{suffix}"
    item_id = min(vendor_supply_ids())
    build_name = "1.60.1.70450"
    sweep_ids: list[int] = []

    class TestStrategy:
        name = "paper_test"
        professions = frozenset()

        def decide(self, market, account):
            return [Buy(item_id, 99, 1), VendorBuy(item_id, 1)]

    strategy = TestStrategy()
    from crowley.trading.strategies import build as registered_build

    monkeypatch.setattr(paper, "build", lambda name: strategy)

    def insert_sweep(
        conn,
        ordinal: int,
        t: int,
        *,
        build: str = build_name,
        started_at: int | None = None,
    ) -> int:
        client_version, client_build = build.rsplit(".", 1)
        started_at = t if started_at is None else started_at
        sweep_id = conn.execute(
            """
            INSERT INTO market_sweeps
                (sweep_uid, house_id, plan_hash, started_at, finished_at, character,
                 client_version, client_build, interface, house_source, num_rows,
                 num_observations, context, payload, content_digest, raw_path)
            VALUES (%s, %s, %s, %s, %s, 'Tester', %s, %s, 1, 'auto',
                    1, 1, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                f"{run_name}-sweep-{ordinal}",
                house_id,
                plan_hash,
                datetime.fromtimestamp(started_at, UTC),
                datetime.fromtimestamp(t + 1, UTC),
                client_version,
                client_build,
                Jsonb({}),
                Jsonb({}),
                hashlib.sha256(f"payload-{ordinal}".encode()).hexdigest(),
                f"/tmp/{run_name}-{ordinal}.json",
            ),
        ).fetchone()[0]
        query = {"kind": "queried", "startedAt": t, "finishedAt": t + 1}
        row_data = {
            "owners": {"totalNumberOfOwners": 0},
            "timeLeft": {"kind": "exact", "seconds": 3600},
        }
        conn.execute(
            """
            INSERT INTO market_observations
                (sweep_id, house_id, item_id, item_key, ordinal, kind, query, coverage,
                 source_complete, cutoff, higher_price_witness, reason_code, row_count, observation)
            VALUES (%s, %s, %s, %s, 1, 'commodity', %s, 'full', true, %s, %s, 'ok', 1, %s)
            """,
            (
                sweep_id,
                house_id,
                item_id,
                str(item_id),
                Jsonb(query),
                Jsonb({"kind": "unbounded"}),
                Jsonb({"kind": "unknown"}),
                Jsonb({}),
            ),
        )
        conn.execute(
            """
            INSERT INTO market_captured_rows
                (sweep_id, item_id, row_key, result_id, item_key, raw_item_key,
                 quantity, unit_numerator, unit_denominator, row_data)
            VALUES (%s, %s, 'row:1', 1, %s, %s, 10, 50, 1, %s)
            """,
            (sweep_id, item_id, str(item_id), Jsonb({"itemID": item_id}), Jsonb(row_data)),
        )
        sweep_ids.append(sweep_id)
        return sweep_id

    with psycopg.connect(DB_URL) as conn:
        migrate(conn)
        with conn.transaction():
            house_id = conn.execute(
                """
                INSERT INTO houses (key, region, ruleset, faction)
                VALUES (%s, 'test', 'normal', %s)
                RETURNING id
                """,
                (house_key, suffix),
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO market_plans (plan_hash, plan_json, plan_body)
                VALUES (%s, %s, %s)
                """,
                (plan_hash, "{}", Jsonb({})),
            )
            insert_sweep(conn, 1, 1_800_000_000)
            insert_sweep(conn, 2, 1_800_000_900)
            export_id = conn.execute(
                """
                INSERT INTO client_data_exports (export_key, client_build, manifest, manifest_sha256)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    export_key,
                    build_name,
                    Jsonb({"test": run_name}),
                    hashlib.sha256(json.dumps({"test": run_name}).encode()).hexdigest(),
                ),
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO client_items
                    (export_id, item_id, status, name, quality, item_level, class_id,
                     subclass_id, sell_price, buy_price, vendor_stack_count, bonding,
                     max_stack, required_skill, required_skill_rank)
                VALUES (%s, %s, 'ok', 'Paper Test Supply', 1, 1, 0, 0, 100, 1, 1, 0, 20, NULL, NULL)
                """,
                (export_id, item_id),
            )

    try:
        paper.create_run(
            DB_URL,
            name=run_name,
            house=house_key,
            start=1_800_000_000,
            capital_gold=20,
            strategies=["paper_test"],
            weights=[1],
            client_build=build_name,
        )
        custom_build = paper.build
        monkeypatch.setattr(paper, "build", registered_build)
        with pytest.raises(ValueError, match="unknown strategy"):
            paper.create_run(
                DB_URL,
                name=f"{run_name}-unknown",
                house=house_key,
                start=1_800_000_000,
                strategies=["not-a-strategy"],
                client_build=build_name,
            )
        monkeypatch.setattr(paper, "build", custom_build)
        with pytest.raises(paper.PaperError, match="already exists"):
            paper.create_run(
                DB_URL,
                name=run_name,
                house=house_key,
                start=1_800_000_000,
                strategies=["paper_test"],
                client_build=build_name,
            )
        with pytest.raises(paper.PaperError, match="build"):
            paper.create_run(
                DB_URL,
                name=f"{run_name}-bad-build",
                house=house_key,
                start=1_800_000_000,
                strategies=["paper_test"],
                client_build="1.60.1.99999",
            )
        assert "steps_added=1" in paper.step_run(DB_URL, run_name)
        assert "steps_added=0" in paper.step_run(DB_URL, run_name)
        status = paper.status_run(DB_URL, run_name)
        assert "latest_t=1800000000" in status
        assert "pending (outcome not final):" in status
        assert "pending intent strategy=paper_test ordinal=0" in status
        with psycopg.connect(DB_URL) as conn:
            before_steps = conn.execute(
                """
                SELECT step_t, sweep_key, equity, realized, cash
                FROM paper_steps
                WHERE run_id = (SELECT id FROM paper_runs WHERE name = %s)
                ORDER BY step_t
                """,
                (run_name,),
            ).fetchall()
            before_intents = conn.execute(
                """
                SELECT step_t, strategy, ordinal, intent, outcome, detail
                FROM paper_intents
                WHERE run_id = (SELECT id FROM paper_runs WHERE name = %s)
                ORDER BY step_t, strategy, ordinal
                """,
                (run_name,),
            ).fetchall()
            pending = conn.execute(
                """
                SELECT step_t, sweep_key, intents
                FROM paper_pending
                WHERE run_id = (SELECT id FROM paper_runs WHERE name = %s)
                """,
                (run_name,),
            ).fetchone()
        assert len(before_steps) == 1
        assert all(row[4] != "wind_down" for row in before_intents)
        assert pending[0] == 1_800_000_900
        assert pending[2]["paper_test"][0]["type"] == "Buy"
        assert "outcome" not in pending[2]["paper_test"][0]

        with psycopg.connect(DB_URL) as conn:
            with conn.transaction():
                insert_sweep(conn, 3, 1_800_001_800)

        original_write_records = paper._write_records

        def fail_after_write(conn, run_id, records, existing):
            original_write_records(conn, run_id, records, existing)
            raise RuntimeError("test failure after paper write")

        monkeypatch.setattr(paper, "_write_records", fail_after_write)
        with pytest.raises(RuntimeError, match="test failure"):
            paper.step_run(DB_URL, run_name)
        monkeypatch.setattr(paper, "_write_records", original_write_records)
        with psycopg.connect(DB_URL) as conn:
            assert conn.execute(
                "SELECT count(*) FROM paper_steps WHERE run_id = (SELECT id FROM paper_runs WHERE name = %s)",
                (run_name,),
            ).fetchone()[0] == len(before_steps)

        assert "steps_added=1" in paper.step_run(DB_URL, run_name)
        with psycopg.connect(DB_URL) as conn:
            after_steps = conn.execute(
                """
                SELECT step_t, sweep_key, equity, realized, cash
                FROM paper_steps
                WHERE run_id = (SELECT id FROM paper_runs WHERE name = %s)
                ORDER BY step_t
                """,
                (run_name,),
            ).fetchall()
            after_intents = conn.execute(
                """
                SELECT step_t, strategy, ordinal, intent, outcome, detail
                FROM paper_intents
                WHERE run_id = (SELECT id FROM paper_runs WHERE name = %s)
                ORDER BY step_t, strategy, ordinal
                """,
                (run_name,),
            ).fetchall()
        assert after_steps[: len(before_steps)] == before_steps
        assert after_intents[: len(before_intents)] == before_intents
        assert len(after_steps) == 2
        assert all(row[4] != "wind_down" for row in after_intents)
        # The promoted step's AH Buy depends on the next sweep: it must now be final and filled,
        # not merely accompanied by an always-executable VendorBuy.
        promoted_buys = [row for row in after_intents if row[0] == 1_800_000_900 and row[3]["type"] == "Buy"]
        assert len(promoted_buys) == 1
        assert promoted_buys[0][4] == "executed"
        assert promoted_buys[0][5]["filled"] == 1

        with psycopg.connect(DB_URL) as conn:
            conn.execute(
                """
                UPDATE paper_steps
                SET equity = jsonb_set(equity, '{total}', '0'::jsonb)
                WHERE run_id = (SELECT id FROM paper_runs WHERE name = %s)
                  AND step_t = %s
                """,
                (run_name, 1_800_000_000),
            )
            conn.commit()
        with pytest.raises(paper.PaperError, match="diverged at step"):
            paper.step_run(DB_URL, run_name)

        monkeypatch.setattr(paper, "engine_digest", lambda: "0" * 64)
        with pytest.raises(paper.PaperError, match="code changed"):
            paper.step_run(DB_URL, run_name)
        monkeypatch.setattr(paper, "engine_digest", paper._source_digest)

        with psycopg.connect(DB_URL) as conn:
            with conn.transaction():
                insert_sweep(
                    conn,
                    4,
                    1_800_002_700,
                    build="1.60.1.99999",
                    started_at=1_799_999_999,
                )
        with pytest.raises(paper.PaperError, match="client build changed"):
            paper.step_run(DB_URL, run_name)
    finally:
        with psycopg.connect(DB_URL) as conn:
            with conn.transaction():
                conn.execute("DELETE FROM paper_runs WHERE name = %s", (run_name,))
                conn.execute("DELETE FROM market_sweeps WHERE id = ANY(%s)", (sweep_ids,))
                conn.execute("DELETE FROM client_data_exports WHERE export_key = %s", (export_key,))
                conn.execute("DELETE FROM market_plans WHERE plan_hash = %s", (plan_hash,))
                conn.execute("DELETE FROM houses WHERE id = %s", (house_id,))
