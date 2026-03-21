import requests

from src.data.config import TELEGRAM_BOT_TOKEN
from src.delivery.subscribers import load_subscribers


def send_message(text: str) -> bool:
    """텔레그램 봇으로 등록된 모든 구독자에게 메시지를 전송한다."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    subscribers = load_subscribers()
    if not subscribers:
        print("등록된 구독자가 없습니다.")
        return False
    success = True
    for chat_id, name in subscribers.items():
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"텔레그램 전송 실패 ({name}): {e}")
            success = False
    return success
