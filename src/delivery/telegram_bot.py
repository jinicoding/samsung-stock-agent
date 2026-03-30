import requests

from src.data.config import TELEGRAM_BOT_TOKEN
from src.delivery.subscribers import load_subscribers


def split_message(text: str, limit: int = 4096) -> list[str]:
    """텔레그램 4096자 제한에 맞춰 메시지를 분할한다.

    분할 우선순위: \\n\\n (섹션 경계) → \\n (줄 경계) → 강제 절단.
    """
    if len(text) <= limit:
        return [text]

    parts: list[str] = []

    # 1차: \n\n 기준 분할 시도
    separator = "\n\n"
    chunks = text.split(separator)

    buf = chunks[0]
    for chunk in chunks[1:]:
        candidate = buf + separator + chunk
        if len(candidate) <= limit:
            buf = candidate
        else:
            # buf 자체가 limit 초과일 수 있으므로 재분할
            parts.extend(_split_by_line(buf, limit))
            buf = chunk
    parts.extend(_split_by_line(buf, limit))

    return parts


def _split_by_line(text: str, limit: int) -> list[str]:
    """\\n 기준으로 분할. 그래도 넘으면 강제 절단."""
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    lines = text.split("\n")
    buf = lines[0]
    for line in lines[1:]:
        candidate = buf + "\n" + line
        if len(candidate) <= limit:
            buf = candidate
        else:
            parts.extend(_hard_split(buf, limit))
            buf = line
    parts.extend(_hard_split(buf, limit))
    return parts


def _hard_split(text: str, limit: int) -> list[str]:
    """개행 없이 limit를 초과하는 텍스트를 강제로 자른다."""
    if len(text) <= limit:
        return [text]
    return [text[i:i + limit] for i in range(0, len(text), limit)]


def send_message(text: str) -> bool:
    """텔레그램 봇으로 등록된 모든 구독자에게 메시지를 전송한다."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    subscribers = load_subscribers()
    if not subscribers:
        print("등록된 구독자가 없습니다.")
        return False
    parts = split_message(text)
    success = True
    for chat_id, name in subscribers.items():
        for part in parts:
            payload = {
                "chat_id": chat_id,
                "text": part,
                "parse_mode": "HTML",
            }
            try:
                resp = requests.post(url, json=payload, timeout=10)
                resp.raise_for_status()
            except Exception as e:
                print(f"텔레그램 전송 실패 ({name}): {e}")
                success = False
    return success
