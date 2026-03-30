"""split_message() 테스트 — 텔레그램 4096자 제한 대응."""

from src.delivery.telegram_bot import split_message


def test_short_message_no_split():
    """4096자 이하 메시지는 분할하지 않는다."""
    text = "짧은 메시지"
    parts = split_message(text)
    assert parts == [text]


def test_empty_message():
    assert split_message("") == [""]


def test_split_on_double_newline():
    """섹션 경계(\\n\\n) 기준으로 분할한다."""
    sections = [f"섹션{i}: " + "가" * 2000 for i in range(3)]
    text = "\n\n".join(sections)
    assert len(text) > 4096
    parts = split_message(text, limit=4096)
    for p in parts:
        assert len(p) <= 4096
    # 재조합하면 원본과 동일해야 한다
    assert "\n\n".join(parts) == text


def test_split_on_single_newline():
    """\\n\\n 없이 \\n만 있는 긴 텍스트도 분할된다."""
    lines = ["라인" + "나" * 80 for _ in range(60)]
    text = "\n".join(lines)
    assert len(text) > 4096
    parts = split_message(text, limit=4096)
    for p in parts:
        assert len(p) <= 4096
    assert "\n".join(parts) == text


def test_exact_boundary():
    """정확히 4096자인 메시지는 분할하지 않는다."""
    text = "X" * 4096
    parts = split_message(text, limit=4096)
    assert parts == [text]


def test_single_chunk_exceeds_limit():
    """개행 없이 4096자를 초과하는 단일 덩어리는 강제 절단한다."""
    text = "A" * 5000
    parts = split_message(text, limit=4096)
    for p in parts:
        assert len(p) <= 4096
    assert "".join(parts) == text


def test_many_sections():
    """15개 이상 섹션이 포함된 실제 리포트급 메시지."""
    sections = [f"<b>섹션 {i}</b>\n데이터 " + "다" * 300 for i in range(20)]
    text = "\n\n".join(sections)
    parts = split_message(text, limit=4096)
    for p in parts:
        assert len(p) <= 4096
    assert "\n\n".join(parts) == text
