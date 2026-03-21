"""Samsung Electronics stock analysis agent — entry point.

This is the daily orchestration script. It fetches data, runs analysis,
and sends reports via Telegram. The agent will evolve this file over time,
adding analysis capabilities and improving reports.
"""

from src.data.database import init_db


def main():
    """일일 실행 진입점. 에이전트가 진화하며 확장할 영역."""
    init_db()
    print("Database initialized. Ready for evolution.")


if __name__ == "__main__":
    main()
