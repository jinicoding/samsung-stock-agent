"""Tests for src/data/database.py — SQLite CRUD operations."""

import os
import sqlite3
import tempfile

import pytest


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database file and patch DB_FILE."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    monkeypatch.setattr("src.data.config.DB_FILE", db_path)
    # Re-import after patching to pick up new DB_FILE
    import importlib
    import src.data.database as db_mod
    importlib.reload(db_mod)
    yield db_path, db_mod
    os.unlink(db_path)


def test_init_db_creates_tables(temp_db):
    db_path, db = temp_db
    db.init_db()
    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {t[0] for t in tables}
    assert "daily_prices" in table_names
    assert "foreign_trading" in table_names
    assert "exchange_rate" in table_names
    assert "foreign_ownership" in table_names
    conn.close()


def test_upsert_and_get_daily(temp_db):
    db_path, db = temp_db
    db.init_db()
    db.upsert_daily("2026-03-20", 55000, 56000, 54000, 55500, 1000000)
    db.upsert_daily("2026-03-21", 55500, 57000, 55000, 56000, 1200000)

    prices = db.get_prices(10)
    assert len(prices) == 2
    assert prices[0]["date"] == "2026-03-20"
    assert prices[1]["date"] == "2026-03-21"
    assert prices[1]["close"] == 56000


def test_upsert_daily_overwrites(temp_db):
    db_path, db = temp_db
    db.init_db()
    db.upsert_daily("2026-03-20", 55000, 56000, 54000, 55500, 1000000)
    db.upsert_daily("2026-03-20", 55000, 56000, 54000, 99999, 1000000)

    prices = db.get_prices(10)
    assert len(prices) == 1
    assert prices[0]["close"] == 99999


def test_upsert_bulk(temp_db):
    db_path, db = temp_db
    db.init_db()
    rows = [
        {"date": "2026-03-18", "open": 54000, "high": 55000, "low": 53000, "close": 54500, "volume": 800000},
        {"date": "2026-03-19", "open": 54500, "high": 55500, "low": 54000, "close": 55000, "volume": 900000},
    ]
    db.upsert_bulk(rows)
    prices = db.get_prices(10)
    assert len(prices) == 2


def test_get_latest_date_empty(temp_db):
    db_path, db = temp_db
    db.init_db()
    assert db.get_latest_date() is None


def test_get_latest_date(temp_db):
    db_path, db = temp_db
    db.init_db()
    db.upsert_daily("2026-03-20", 55000, 56000, 54000, 55500, 1000000)
    db.upsert_daily("2026-03-21", 55500, 57000, 55000, 56000, 1200000)
    assert db.get_latest_date() == "2026-03-21"


def test_exchange_rate_crud(temp_db):
    db_path, db = temp_db
    db.init_db()
    rows = [
        {"date": "2026-03-20", "open": 1350.0, "high": 1355.0, "low": 1345.0, "close": 1350.5},
        {"date": "2026-03-21", "open": 1350.5, "high": 1360.0, "low": 1348.0, "close": 1355.0},
    ]
    db.upsert_exchange_rate_bulk(rows)
    rates = db.get_exchange_rates(10)
    assert len(rates) == 2
    assert rates[0]["date"] == "2026-03-20"
    assert db.get_latest_exchange_rate_date() == "2026-03-21"


def test_foreign_trading_crud(temp_db):
    db_path, db = temp_db
    db.init_db()
    rows = [
        {"date": "2026-03-20", "institution": 100000, "foreign_total": 200000, "individual": -300000, "other_corp": 0},
    ]
    db.upsert_foreign_trading_bulk(rows)
    data = db.get_foreign_trading(10)
    assert len(data) == 1
    assert data[0]["foreign_total"] == 200000


def test_foreign_ownership_crud(temp_db):
    db_path, db = temp_db
    db.init_db()
    db.upsert_foreign_ownership({
        "date": "2026-03-20",
        "listed_shares": 5969783000,
        "foreign_shares": 3000000000,
        "ownership_pct": 50.25,
        "limit_shares": 5969783000,
        "exhaustion_pct": 50.25,
    })
    data = db.get_foreign_ownership(10)
    assert len(data) == 1
    assert data[0]["ownership_pct"] == 50.25


# ── signal_history ──────────────────────────────────────────────

def test_init_db_creates_signal_history(temp_db):
    db_path, db = temp_db
    db.init_db()
    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {t[0] for t in tables}
    assert "signal_history" in table_names
    conn.close()


def test_upsert_signal_history(temp_db):
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-03-24",
        score=35.5,
        grade="매수우세",
        technical_score=40.0,
        supply_score=30.0,
        exchange_score=20.0,
        price=55000.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-03-24"
    assert rows[0]["score"] == 35.5
    assert rows[0]["grade"] == "매수우세"
    assert rows[0]["technical_score"] == 40.0
    assert rows[0]["supply_score"] == 30.0
    assert rows[0]["exchange_score"] == 20.0
    assert rows[0]["price"] == 55000.0


def test_upsert_signal_history_overwrites(temp_db):
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history("2026-03-24", 35.5, "매수우세", 40.0, 30.0, 20.0, 55000.0)
    db.upsert_signal_history("2026-03-24", -10.0, "중립", -5.0, -15.0, 10.0, 54000.0)
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    assert rows[0]["score"] == -10.0
    assert rows[0]["price"] == 54000.0


def test_get_signal_history_order(temp_db):
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history("2026-03-22", 10.0, "중립", 5.0, 10.0, 20.0, 54000.0)
    db.upsert_signal_history("2026-03-24", 35.5, "매수우세", 40.0, 30.0, 20.0, 55000.0)
    db.upsert_signal_history("2026-03-23", -20.0, "매도우세", -30.0, -10.0, -5.0, 53000.0)
    rows = db.get_signal_history(10)
    assert len(rows) == 3
    assert rows[0]["date"] == "2026-03-22"
    assert rows[1]["date"] == "2026-03-23"
    assert rows[2]["date"] == "2026-03-24"


def test_get_signal_history_limits(temp_db):
    db_path, db = temp_db
    db.init_db()
    for i in range(5):
        db.upsert_signal_history(f"2026-03-{20+i}", float(i), "중립", 0.0, 0.0, 0.0, 50000.0)
    rows = db.get_signal_history(3)
    assert len(rows) == 3
    assert rows[0]["date"] == "2026-03-22"
