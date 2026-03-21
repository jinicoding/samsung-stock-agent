"""구독자 목록을 subscribers.json에서 로드한다."""

import json
import os

SUBSCRIBERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subscribers.json")


def load_subscribers() -> dict[str, str]:
    """subscribers.json에서 {chat_id: name} 딕셔너리를 반환한다."""
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    return {}
