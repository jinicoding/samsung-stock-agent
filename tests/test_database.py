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
