import base64
import json
import os
import secrets
from pathlib import Path
from urllib import parse, request as urllib_req
from urllib.error import HTTPError, URLError

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from ..auth_session import get_session_status, set_token_response

router = APIRouter(prefix="/auth", tags=["auth"])
DEFAULT_SCOPES = [
    "user-read-email",
    "user-read-private",
    "playlist-modify-private",
    "playlist-modify-public",
]


def _load_local_env_fallback() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and (key not in os.environ or not os.environ.get(key)):
            os.environ[key] = value


@router.get("/login")
def spotify_login(request: Request):
    _load_local_env_fallback()

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="Missing SPOTIFY_CLIENT_ID in backend environment.",
        )

    env_redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    callback_redirect_uri = str(request.url).replace("/login", "/callback")
    redirect_uri = env_redirect_uri or callback_redirect_uri
    scope = os.getenv("SPOTIFY_SCOPE", " ".join(DEFAULT_SCOPES)).strip()
    state = secrets.token_urlsafe(16)

    url = parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "show_dialog": "true",
        }
    )
    return RedirectResponse(url=f"https://accounts.spotify.com/authorize?{url}", status_code=302)


@router.get("/callback")
def spotify_callback(
    request: Request,
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    state: str | None = Query(default=None),
):
    _load_local_env_fallback()

    if error:
        raise HTTPException(status_code=400, detail=f"Spotify auth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing Spotify authorization code.")

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    env_redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    callback_redirect_uri = str(request.url).split("?", 1)[0]
    redirect_uri = env_redirect_uri or callback_redirect_uri

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=500,
            detail=(
                "Missing Spotify env vars. Required: SPOTIFY_CLIENT_ID, "
                "SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI. "
                "Tip: run uvicorn with --env-file backend/.env"
            ),
        )

    payload = parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
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
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=502, detail=f"Spotify token exchange failed: {body}") from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Spotify token exchange network error: {exc}") from exc

    token_data = json.loads(raw)
    if "access_token" not in token_data:
        raise HTTPException(status_code=502, detail=f"Unexpected Spotify response: {token_data}")

    set_token_response(token_data)
    granted_scope = token_data.get("scope") or ""
    granted = set(str(granted_scope).split())
    required = set(DEFAULT_SCOPES)
    missing = sorted(required - granted)

    return {
        "message": "Spotify authorization successful.",
        "state": state,
        "token_type": token_data.get("token_type"),
        "scope": token_data.get("scope"),
        "missing_required_scopes": missing,
        "expires_in": token_data.get("expires_in"),
        "token_saved": True,
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
    }


@router.get("/session")
def spotify_session_status():
    return get_session_status()
