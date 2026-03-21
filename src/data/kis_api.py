"""한국투자증권 Open API 클라이언트.

토큰 관리 및 공통 요청 헬퍼를 제공한다.
토큰은 파일에 캐싱하여 프로세스 간 재사용한다 (유효기간 24시간, 발급 1분당 1회 제한).
"""

import json
import os
import time

import requests

from src.data.config import KIS_APP_KEY, KIS_APP_SECRET, KIS_BASE_URL

_TOKEN_CACHE = os.path.join(os.path.dirname(__file__), ".kis_token.json")


def _load_cached_token() -> str | None:
    """파일에 캐싱된 토큰을 반환한다. 만료되었거나 없으면 None."""
    try:
        with open(_TOKEN_CACHE) as f:
            cache = json.load(f)
        if cache.get("expires", 0) > time.time() and cache.get("token"):
            return cache["token"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None


def _save_token(token: str, expires_at: float) -> None:
    """토큰을 파일에 캐싱한다."""
    with open(_TOKEN_CACHE, "w") as f:
        json.dump({"token": token, "expires": expires_at}, f)


def _ensure_token() -> str:
    """액세스 토큰을 발급하거나 캐시된 토큰을 반환한다."""
    cached = _load_cached_token()
    if cached:
        return cached

    if not KIS_APP_KEY or not KIS_APP_SECRET:
        raise RuntimeError(
            "KIS API 키가 설정되지 않았습니다. "
            "KIS_APP_KEY, KIS_APP_SECRET 환경 변수를 설정하세요."
        )

    resp = requests.post(
        f"{KIS_BASE_URL}/oauth2/tokenP",
        json={
            "grant_type": "client_credentials",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
        },
        timeout=10,
    )

    if resp.status_code == 403:
        body = resp.json()
        raise RuntimeError(
            f"토큰 발급 제한: {body.get('error_description', resp.text)} "
            "(1분당 1회 제한, 잠시 후 재시도)"
        )
    resp.raise_for_status()
    data = resp.json()

    token = data["access_token"]
    expires_at = time.time() + 23 * 3600  # 만료 1시간 전 여유
    _save_token(token, expires_at)
    return token


def kis_get(path: str, tr_id: str, params: dict) -> dict:
    """KIS REST API GET 요청을 수행하고 응답 JSON을 반환한다."""
    token = _ensure_token()
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "Content-Type": "application/json; charset=utf-8",
    }
    resp = requests.get(
        f"{KIS_BASE_URL}{path}",
        headers=headers,
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("rt_cd") != "0":
        raise RuntimeError(f"KIS API 오류 [{tr_id}]: {data.get('msg1', data)}")

    return data
