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


# ── signal_history 9축 확장 ─────────────────────────────────────

def test_upsert_signal_history_9axes(temp_db):
    """9축 점수 전체를 저장하고 조회할 수 있다."""
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-01",
        score=42.0,
        grade="매수우세",
        technical_score=50.0,
        supply_score=40.0,
        exchange_score=10.0,
        price=58000.0,
        fundamentals_score=30.0,
        news_score=20.0,
        consensus_score=60.0,
        semiconductor_score=45.0,
        volatility_score=-15.0,
        candlestick_score=25.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    r = rows[0]
    assert r["fundamentals_score"] == 30.0
    assert r["news_score"] == 20.0
    assert r["consensus_score"] == 60.0
    assert r["semiconductor_score"] == 45.0
    assert r["volatility_score"] == -15.0
    assert r["candlestick_score"] == 25.0


def test_upsert_signal_history_partial_axes(temp_db):
    """일부 축만 전달하면 나머지는 NULL로 저장된다."""
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-01",
        score=20.0,
        grade="중립",
        technical_score=10.0,
        supply_score=15.0,
        exchange_score=5.0,
        price=56000.0,
        fundamentals_score=30.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    r = rows[0]
    assert r["fundamentals_score"] == 30.0
    assert r["news_score"] is None
    assert r["consensus_score"] is None


def test_signal_history_backward_compat(temp_db):
    """기존 3축만 전달해도 정상 동작한다 (하위호환)."""
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-01",
        score=10.0,
        grade="중립",
        technical_score=5.0,
        supply_score=5.0,
        exchange_score=0.0,
        price=55000.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    r = rows[0]
    assert r["technical_score"] == 5.0
    assert r["fundamentals_score"] is None
    assert r["candlestick_score"] is None


def test_migrate_adds_columns(temp_db):
    """기존 테이블에 새 컬럼이 없어도 init_db() 마이그레이션으로 추가된다."""
    db_path, db = temp_db
    # 먼저 구형 스키마로 테이블 생성
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE signal_history (
            date              TEXT PRIMARY KEY,
            score             REAL NOT NULL,
            grade             TEXT NOT NULL,
            technical_score   REAL NOT NULL,
            supply_score      REAL NOT NULL,
            exchange_score    REAL NOT NULL,
            price             REAL NOT NULL
        )
    """)
    conn.execute(
        "INSERT INTO signal_history VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("2026-03-30", 10.0, "중립", 5.0, 5.0, 0.0, 55000.0),
    )
    conn.commit()
    conn.close()
    # init_db()가 마이그레이션 수행
    db.init_db()
    # 새 컬럼으로 저장 가능
    db.upsert_signal_history(
        date="2026-04-01", score=20.0, grade="매수우세",
        technical_score=10.0, supply_score=10.0, exchange_score=0.0,
        price=56000.0, fundamentals_score=30.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 2
    # 기존 행은 새 컬럼이 NULL
    assert rows[0]["fundamentals_score"] is None
    # 새 행은 값이 있음
    assert rows[1]["fundamentals_score"] == 30.0


# ── signal_history 10축 (global_macro_score) ──────────────────

def test_upsert_signal_history_10axes(temp_db):
    """10축 점수 전체를 저장하고 조회할 수 있다."""
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-08",
        score=45.0,
        grade="매수우세",
        technical_score=50.0,
        supply_score=40.0,
        exchange_score=10.0,
        price=58000.0,
        fundamentals_score=30.0,
        news_score=20.0,
        consensus_score=60.0,
        semiconductor_score=45.0,
        volatility_score=-15.0,
        candlestick_score=25.0,
        global_macro_score=35.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    r = rows[0]
    assert r["global_macro_score"] == 35.0


def test_upsert_signal_history_global_macro_none(temp_db):
    """global_macro_score를 전달하지 않으면 NULL로 저장된다."""
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-08",
        score=20.0,
        grade="중립",
        technical_score=10.0,
        supply_score=15.0,
        exchange_score=5.0,
        price=56000.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    assert rows[0]["global_macro_score"] is None


def test_migrate_adds_global_macro_score(temp_db):
    """기존 9축 테이블에 global_macro_score 컬럼이 마이그레이션으로 추가된다."""
    db_path, db = temp_db
    # 9축 스키마로 테이블 생성
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE signal_history (
            date              TEXT PRIMARY KEY,
            score             REAL NOT NULL,
            grade             TEXT NOT NULL,
            technical_score   REAL NOT NULL,
            supply_score      REAL NOT NULL,
            exchange_score    REAL NOT NULL,
            price             REAL NOT NULL,
            fundamentals_score  REAL DEFAULT NULL,
            news_score          REAL DEFAULT NULL,
            consensus_score     REAL DEFAULT NULL,
            semiconductor_score REAL DEFAULT NULL,
            volatility_score    REAL DEFAULT NULL,
            candlestick_score   REAL DEFAULT NULL
        )
    """)
    conn.execute(
        "INSERT INTO signal_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("2026-04-07", 10.0, "중립", 5.0, 5.0, 0.0, 55000.0,
         None, None, None, None, None, None),
    )
    conn.commit()
    conn.close()
    # init_db()가 마이그레이션 수행
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-08", score=20.0, grade="매수우세",
        technical_score=10.0, supply_score=10.0, exchange_score=0.0,
        price=56000.0, global_macro_score=35.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 2
    assert rows[0]["global_macro_score"] is None
    assert rows[1]["global_macro_score"] == 35.0


# ── signal_history 11축 (rs_score) ──────────────────────────────

def test_upsert_signal_history_11axes(temp_db):
    """11축 점수 전체를 저장하고 조회할 수 있다."""
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-17",
        score=48.0,
        grade="매수우세",
        technical_score=50.0,
        supply_score=40.0,
        exchange_score=10.0,
        price=58000.0,
        fundamentals_score=30.0,
        news_score=20.0,
        consensus_score=60.0,
        semiconductor_score=45.0,
        volatility_score=-15.0,
        candlestick_score=25.0,
        global_macro_score=35.0,
        rs_score=22.5,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    r = rows[0]
    assert r["rs_score"] == 22.5
    assert r["global_macro_score"] == 35.0


def test_upsert_signal_history_rs_score_none(temp_db):
    """rs_score를 전달하지 않으면 NULL로 저장된다."""
    db_path, db = temp_db
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-17",
        score=20.0,
        grade="중립",
        technical_score=10.0,
        supply_score=15.0,
        exchange_score=5.0,
        price=56000.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 1
    assert rows[0]["rs_score"] is None


def test_migrate_adds_rs_score(temp_db):
    """기존 10축 테이블에 rs_score 컬럼이 마이그레이션으로 추가된다."""
    db_path, db = temp_db
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE signal_history (
            date              TEXT PRIMARY KEY,
            score             REAL NOT NULL,
            grade             TEXT NOT NULL,
            technical_score   REAL NOT NULL,
            supply_score      REAL NOT NULL,
            exchange_score    REAL NOT NULL,
            price             REAL NOT NULL,
            fundamentals_score  REAL DEFAULT NULL,
            news_score          REAL DEFAULT NULL,
            consensus_score     REAL DEFAULT NULL,
            semiconductor_score REAL DEFAULT NULL,
            volatility_score    REAL DEFAULT NULL,
            candlestick_score   REAL DEFAULT NULL,
            global_macro_score  REAL DEFAULT NULL
        )
    """)
    conn.execute(
        "INSERT INTO signal_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("2026-04-16", 10.0, "중립", 5.0, 5.0, 0.0, 55000.0,
         None, None, None, None, None, None, None),
    )
    conn.commit()
    conn.close()
    db.init_db()
    db.upsert_signal_history(
        date="2026-04-17", score=20.0, grade="매수우세",
        technical_score=10.0, supply_score=10.0, exchange_score=0.0,
        price=56000.0, rs_score=18.0,
    )
    rows = db.get_signal_history(10)
    assert len(rows) == 2
    assert rows[0]["rs_score"] is None
    assert rows[1]["rs_score"] == 18.0
