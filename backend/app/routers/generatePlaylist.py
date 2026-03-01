from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..auth_session import get_access_token, get_session_status
from .groqCompound import PlaylistGenerationError, generate_playlist
from .spotifyAPI import SpotifyAPIError

router = APIRouter()


class Req(BaseModel):
    prompt: str


@router.post(
    "/playlist/from-prompt",
    responses={
        400: {"description": "Missing Spotify access token."},
        403: {"description": "Spotify token does not have required permissions."},
        500: {"description": "Internal server error."},
        502: {"description": "Upstream (Groq/Spotify) request failure."},
    },
)
def from_prompt(req: Req):
    token = get_access_token()
    if not token:
        raise HTTPException(
            status_code=400,
            detail=(
                "Spotify access token is missing. Re-authorize via /auth/login. "
                "Env-token fallback is disabled by default; set "
                "SPOTIFY_ALLOW_ENV_TOKEN_FALLBACK=true to use SPOTIFY_ACCESS_TOKEN."
            ),
        )

    session = get_session_status()
    scope = session.get("scope")
    if isinstance(scope, str) and scope.strip():
        granted = set(scope.split())
        required = {"playlist-modify-private", "playlist-modify-public"}
        missing = sorted(required - granted)
        if missing:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": (
                        "Spotify token is missing required playlist scopes. "
                        "Re-authorize via /auth/login and approve all requested permissions."
                    ),
                    "operation": "scope precheck",
                    "missing_scopes": missing,
                    "granted_scopes": sorted(granted),
                    "status_code": 403,
                },
            )

    try:
        return generate_playlist(req.prompt, token)
    except SpotifyAPIError as exc:
        detail = {"message": exc.message}
        if exc.operation:
            detail["operation"] = exc.operation
        if exc.details:
            detail["spotify_error"] = exc.details
        detail["status_code"] = exc.status_code
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc
    except PlaylistGenerationError as exc:
        detail = {"message": exc.message}
        if exc.operation:
            detail["operation"] = exc.operation
        if exc.details:
            detail["generation_error"] = exc.details
        detail["status_code"] = exc.status_code
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Unhandled internal error while generating playlist.",
                "operation": "POST /playlist/from-prompt",
                "error": str(exc),
                "status_code": 500,
            },
        ) from exc
