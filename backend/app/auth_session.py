import os
import time
import json
import base64
import hashlib
from urllib import parse, request as urllib_req
from urllib.error import HTTPError, URLError
from threading import Lock
from typing import Any

_lock = Lock()
_session: dict[str, Any] = {
    "access_token": None,
    "refresh_token": None,
    "scope": None,
    "token_type": None,
    "expires_at": None,
}


def _token_fingerprint(token: str | None) -> str | None:
    if not token:
        return None
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


def _refresh_access_token(refresh_token: str) -> dict[str, Any] | None:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    payload = parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
    ).encode("utf-8")
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    token_request = urllib_req.Request(
        "https://accounts.spotify.com/api/token",
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic}",
        },
        method="POST",
    )

    try:
        with urllib_req.urlopen(token_request, timeout=15) as response:
            raw = response.read().decode("utf-8")
    except (HTTPError, URLError):
        return None

    try:
        token_data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(token_data, dict) or "access_token" not in token_data:
        return None
    if "refresh_token" not in token_data:
        token_data["refresh_token"] = refresh_token
    return token_data


def set_token_response(token_data: dict[str, Any]) -> None:
    access_token = token_data.get("access_token")
    if not access_token:
        return

    expires_at = None
    expires_in = token_data.get("expires_in")
    if isinstance(expires_in, int):
        # Keep a small safety window before actual expiry.
        expires_at = int(time.time()) + max(expires_in - 30, 0)

    with _lock:
        existing_refresh = _session.get("refresh_token")
        _session["access_token"] = access_token
        _session["refresh_token"] = token_data.get("refresh_token") or existing_refresh
        _session["scope"] = token_data.get("scope")
        _session["token_type"] = token_data.get("token_type")
        _session["expires_at"] = expires_at

    # Keep compatibility with existing code paths that read from env.
    os.environ["SPOTIFY_ACCESS_TOKEN"] = access_token
    if token_data.get("refresh_token"):
        os.environ["SPOTIFY_REFRESH_TOKEN"] = str(token_data["refresh_token"])


def get_access_token() -> str | None:
    with _lock:
        access_token = _session.get("access_token")
        expires_at = _session.get("expires_at")
        refresh_token = _session.get("refresh_token")

    if isinstance(access_token, str) and access_token:
        if not isinstance(expires_at, int) or time.time() < expires_at:
            return access_token

    if isinstance(refresh_token, str) and refresh_token:
        refreshed = _refresh_access_token(refresh_token)
        if refreshed:
            set_token_response(refreshed)
            return refreshed.get("access_token")

    allow_env_fallback = os.getenv("SPOTIFY_ALLOW_ENV_TOKEN_FALLBACK", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if allow_env_fallback:
        env_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
        if env_token:
            return env_token

    return None


def get_session_status() -> dict[str, Any]:
    with _lock:
        has_runtime_token = bool(_session.get("access_token"))
        has_runtime_refresh_token = bool(_session.get("refresh_token"))
        scope = _session.get("scope")
        expires_at = _session.get("expires_at")
        runtime_token_fingerprint = _token_fingerprint(_session.get("access_token"))

    allow_env_fallback = os.getenv("SPOTIFY_ALLOW_ENV_TOKEN_FALLBACK", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    env_token = os.getenv("SPOTIFY_ACCESS_TOKEN")

    return {
        "has_runtime_token": has_runtime_token,
        "has_runtime_refresh_token": has_runtime_refresh_token,
        "runtime_token_fingerprint": runtime_token_fingerprint,
        "has_env_token": bool(env_token),
        "env_token_fingerprint": _token_fingerprint(env_token),
        "allow_env_token_fallback": allow_env_fallback,
        "scope": scope,
        "expires_at_unix": expires_at,
    }
