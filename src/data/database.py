"""삼성전자 OHLCV 데이터를 SQLite에 저장/조회하는 모듈."""

import sqlite3

from src.data.config import DB_FILE


def get_connection() -> sqlite3.Connection:
    """DB 연결을 반환한다."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """모든 테이블을 생성한다."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            date    TEXT PRIMARY KEY,
            open    REAL NOT NULL,
            high    REAL NOT NULL,
            low     REAL NOT NULL,
            close   REAL NOT NULL,
            volume  INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS foreign_trading (
            date            TEXT PRIMARY KEY,
            institution     INTEGER NOT NULL,
            foreign_total   INTEGER NOT NULL,
            individual      INTEGER NOT NULL,
            other_corp      INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rate (
            date    TEXT PRIMARY KEY,
            open    REAL NOT NULL,
            high    REAL NOT NULL,
            low     REAL NOT NULL,
            close   REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS foreign_ownership (
            date             TEXT PRIMARY KEY,
            listed_shares    INTEGER NOT NULL,
            foreign_shares   INTEGER NOT NULL,
            ownership_pct    REAL NOT NULL,
            limit_shares     INTEGER NOT NULL,
            exhaustion_pct   REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_history (
            date              TEXT PRIMARY KEY,
            score             REAL NOT NULL,
            grade             TEXT NOT NULL,
            technical_score   REAL NOT NULL,
            supply_score      REAL NOT NULL,
            exchange_score    REAL NOT NULL,
            price             REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def upsert_daily(date: str, open: float, high: float, low: float,
                 close: float, volume: int) -> None:
    """단일 행을 삽입하거나 갱신한다."""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO daily_prices (date, open, high, low, close, volume) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (date, open, high, low, close, volume),
    )
    conn.commit()
    conn.close()


def upsert_bulk(rows: list[dict]) -> None:
    """다건 삽입/갱신 (백필용)."""
    if not rows:
        return
    conn = get_connection()
    conn.executemany(
        "INSERT OR REPLACE INTO daily_prices (date, open, high, low, close, volume) "
        "VALUES (:date, :open, :high, :low, :close, :volume)",
        rows,
    )
    conn.commit()
    conn.close()


def get_latest_date() -> str | None:
    """마지막 저장 날짜를 반환한다. 데이터가 없으면 None."""
    conn = get_connection()
    cur = conn.execute("SELECT MAX(date) FROM daily_prices")
    result = cur.fetchone()[0]
    conn.close()
    return result


def get_prices(days: int) -> list[dict]:
    """최근 N일 데이터를 날짜 오름차순으로 반환한다."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT date, open, high, low, close, volume FROM daily_prices "
        "ORDER BY date DESC LIMIT ?",
        (days,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    rows.reverse()
    return rows


def get_all_prices() -> list[dict]:
    """전체 데이터를 날짜 오름차순으로 반환한다."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT date, open, high, low, close, volume FROM daily_prices ORDER BY date"
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


# ── foreign_trading ──────────────────────────────────────────────

def upsert_foreign_trading_bulk(rows: list[dict]) -> None:
    """외국인 매매 다건 삽입/갱신."""
    if not rows:
        return
    conn = get_connection()
    conn.executemany(
        "INSERT OR REPLACE INTO foreign_trading "
        "(date, institution, foreign_total, individual, other_corp) "
        "VALUES (:date, :institution, :foreign_total, :individual, :other_corp)",
        rows,
    )
    conn.commit()
    conn.close()


def get_latest_foreign_trading_date() -> str | None:
    """foreign_trading 마지막 날짜를 반환한다."""
    conn = get_connection()
    cur = conn.execute("SELECT MAX(date) FROM foreign_trading")
    result = cur.fetchone()[0]
    conn.close()
    return result


def get_foreign_trading(days: int) -> list[dict]:
    """최근 N일 외국인 매매를 날짜 오름차순으로 반환한다."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT date, institution, foreign_total, individual, other_corp "
        "FROM foreign_trading ORDER BY date DESC LIMIT ?",
        (days,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    rows.reverse()
    return rows


# ── exchange_rate ────────────────────────────────────────────────

def upsert_exchange_rate_bulk(rows: list[dict]) -> None:
    """환율 다건 삽입/갱신."""
    if not rows:
        return
    conn = get_connection()
    conn.executemany(
        "INSERT OR REPLACE INTO exchange_rate (date, open, high, low, close) "
        "VALUES (:date, :open, :high, :low, :close)",
        rows,
    )
    conn.commit()
    conn.close()


def get_latest_exchange_rate_date() -> str | None:
    """exchange_rate 마지막 날짜를 반환한다."""
    conn = get_connection()
    cur = conn.execute("SELECT MAX(date) FROM exchange_rate")
    result = cur.fetchone()[0]
    conn.close()
    return result


def get_exchange_rates(days: int) -> list[dict]:
    """최근 N일 환율을 날짜 오름차순으로 반환한다."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT date, open, high, low, close "
        "FROM exchange_rate ORDER BY date DESC LIMIT ?",
        (days,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    rows.reverse()
    return rows


# ── foreign_ownership ────────────────────────────────────────────

def upsert_foreign_ownership(data: dict) -> None:
    """외국인 보유비율 단건 삽입/갱신."""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO foreign_ownership "
        "(date, listed_shares, foreign_shares, ownership_pct, limit_shares, exhaustion_pct) "
        "VALUES (:date, :listed_shares, :foreign_shares, :ownership_pct, "
        ":limit_shares, :exhaustion_pct)",
        data,
    )
    conn.commit()
    conn.close()


def get_latest_foreign_ownership_date() -> str | None:
    """foreign_ownership 마지막 날짜를 반환한다."""
    conn = get_connection()
    cur = conn.execute("SELECT MAX(date) FROM foreign_ownership")
    result = cur.fetchone()[0]
    conn.close()
    return result


def get_foreign_ownership(days: int) -> list[dict]:
    """최근 N일 외국인 보유비율을 날짜 오름차순으로 반환한다."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT date, listed_shares, foreign_shares, ownership_pct, "
        "limit_shares, exhaustion_pct "
        "FROM foreign_ownership ORDER BY date DESC LIMIT ?",
        (days,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    rows.reverse()
    return rows


# ── signal_history ──────────────────────────────────────────────

def upsert_signal_history(
    date: str,
    score: float,
    grade: str,
    technical_score: float,
    supply_score: float,
    exchange_score: float,
    price: float,
) -> None:
    """시그널 이력 단건 삽입/갱신."""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO signal_history "
        "(date, score, grade, technical_score, supply_score, exchange_score, price) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (date, score, grade, technical_score, supply_score, exchange_score, price),
    )
    conn.commit()
    conn.close()


def get_signal_history(days: int) -> list[dict]:
    """최근 N일 시그널 이력을 날짜 오름차순으로 반환한다."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT date, score, grade, technical_score, supply_score, "
        "exchange_score, price FROM signal_history "
        "ORDER BY date DESC LIMIT ?",
        (days,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    rows.reverse()
    return rows
