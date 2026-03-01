from typing import Any

import requests

BASE = "https://api.spotify.com/v1"


class SpotifyAPIError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: dict[str, Any] | None = None,
        operation: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        self.operation = operation


def _h(token: str):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _error_message(payload: Any, fallback_status: int) -> tuple[int, str]:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            status = int(error.get("status", fallback_status))
            message = error.get("message", "Spotify API request failed.")
            return status, str(message)
        if isinstance(error, str):
            return fallback_status, error
    return fallback_status, "Spotify API request failed."


def _request(method: str, path: str, token: str, **kwargs):
    if not token:
        raise SpotifyAPIError(401, "Missing Spotify access token.", operation=f"{method} {path}")

    try:
        resp = requests.request(method, f"{BASE}{path}", headers=_h(token), timeout=20, **kwargs)
    except requests.RequestException as exc:
        raise SpotifyAPIError(502, f"Could not reach Spotify: {exc}", operation=f"{method} {path}") from exc

    raw_text = resp.text or ""
    try:
        payload = resp.json() if raw_text else {}
    except ValueError:
        payload = {"raw_error_body": raw_text[:500]} if raw_text else {}

    if resp.status_code >= 400:
        status, message = _error_message(payload, resp.status_code)
        details = payload if isinstance(payload, dict) else {}
        details["http_status"] = resp.status_code
        msg_lower = message.lower()
        if message == "Spotify API request failed." and details.get("raw_error_body"):
            message = "Spotify returned a non-JSON error body."
        requires_playlist_scope = (method == "POST" and path == "/me/playlists") or (
            method == "POST" and path.startswith("/playlists/") and path.endswith("/items")
        )
        if status == 403 and ("scope" in msg_lower or requires_playlist_scope):
            message = (
                f"{message}. Re-authorize Spotify with scopes: "
                "user-read-private playlist-modify-private playlist-modify-public. "
                "If your app is still in Development mode, make sure this Spotify account is a registered user."
            )
        raise SpotifyAPIError(status, message, details, operation=f"{method} {path}")

    return payload


def me(token: str):
    payload = _request("GET", "/me", token)
    if not isinstance(payload, dict) or "id" not in payload:
        raise SpotifyAPIError(502, "Spotify /me response did not include a user id.", payload if isinstance(payload, dict) else {})
    return payload


def search_tracks(token: str, q: str, limit: int = 10):
    r = _request("GET", "/search", token, params={"q": q, "type": "track", "limit": str(limit)})
    tracks = r.get("tracks", {}) if isinstance(r, dict) else {}
    items = tracks.get("items", []) if isinstance(tracks, dict) else []
    if not isinstance(items, list):
        raise SpotifyAPIError(502, "Spotify search response was malformed.", r if isinstance(r, dict) else {})
    return [
        {
            "uri": t.get("uri"),
            "name": t.get("name"),
            "artists": [a.get("name") for a in t.get("artists", []) if isinstance(a, dict)],
        }
        for t in items
        if isinstance(t, dict)
    ]


def create_playlist(token: str, user_id: str, name: str, public: bool = False, description: str = ""):
    # Spotify Web API February 2026 migration: create playlist via /me/playlists.
    # Keep `user_id` arg for backward compatibility with existing call sites.
    _ = user_id
    p = _request(
        "POST",
        "/me/playlists",
        token,
        json={"name": name, "public": public, "description": description},
    )
    if not isinstance(p, dict):
        raise SpotifyAPIError(502, "Spotify create-playlist response was malformed.")
    playlist_id = p.get("id")
    url = p.get("external_urls", {}).get("spotify") if isinstance(p.get("external_urls"), dict) else None
    if not playlist_id or not url:
        raise SpotifyAPIError(502, "Spotify create-playlist response was missing required fields.", p)
    return {"id": playlist_id, "url": url}


def add_tracks(token: str, playlist_id: str, uris: list[str]):
    # Spotify Web API February 2026 migration: add playlist items via /items.
    payload = _request("POST", f"/playlists/{playlist_id}/items", token, json={"uris": uris})
    return payload if isinstance(payload, dict) else {"status": "ok"}
