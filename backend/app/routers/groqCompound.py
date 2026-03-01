import json
import os
from groq import Groq

from .spotifyAPI import me, search_tracks, create_playlist, add_tracks

MODEL = os.getenv("GROQ_MODEL", "groq/compound-mini")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "spotify_search_tracks",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_create_playlist",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "public": {"type": "boolean"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_add_tracks",
            "parameters": {
                "type": "object",
                "properties": {"playlist_id": {"type": "string"}, "uris": {"type": "array", "items": {"type": "string"}}},
                "required": ["playlist_id", "uris"],
            },
        },
    },
]


class PlaylistGenerationError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 502,
        details: dict | None = None,
        operation: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.operation = operation


def _groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise PlaylistGenerationError(
            "Missing GROQ_API_KEY.",
            status_code=500,
            operation="groq client init",
        )
    return Groq(api_key=api_key)


def _is_tool_calling_unsupported_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "tool calling" in msg and "not supported" in msg


def _extract_json_object(text: str) -> dict:
    if not text:
        return {}

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    snippet = text[start : end + 1]
    try:
        parsed = json.loads(snippet)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _generate_playlist_without_tools(client: Groq, prompt: str, token: str, user_id: str, reason: str):
    planning_messages = [
        {
            "role": "system",
            "content": (
                "You are a playlist planning assistant. "
                "Respond with valid JSON only using this schema: "
                '{"playlist_name":"string","description":"string","search_queries":["string"],"public":false}. '
                "Return 4-8 concise search queries."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=planning_messages,
        )
    except Exception as exc:
        raise PlaylistGenerationError(
            "Groq request failed.",
            status_code=502,
            details={"error": str(exc)},
            operation="groq fallback planning",
        ) from exc

    content = resp.choices[0].message.content or ""
    plan = _extract_json_object(content)
    queries = plan.get("search_queries")
    if not isinstance(queries, list) or not queries:
        queries = [prompt]

    playlist_name = plan.get("playlist_name")
    if not isinstance(playlist_name, str) or not playlist_name.strip():
        trimmed = " ".join(prompt.split())[:40]
        playlist_name = f"Playlist - {trimmed}" if trimmed else "AI Playlist"

    description = plan.get("description")
    if not isinstance(description, str):
        description = f"Generated from prompt: {prompt[:120]}"

    public = bool(plan.get("public")) if isinstance(plan, dict) else False

    uris: list[str] = []
    seen: set[str] = set()
    for q in queries[:8]:
        if not isinstance(q, str) or not q.strip():
            continue
        tracks = search_tracks(token, q, limit=5)
        for t in tracks:
            uri = t.get("uri") if isinstance(t, dict) else None
            if isinstance(uri, str) and uri and uri not in seen:
                seen.add(uri)
                uris.append(uri)
            if len(uris) >= 30:
                break
        if len(uris) >= 30:
            break

    if not uris:
        raise PlaylistGenerationError(
            "Could not find tracks for the prompt.",
            status_code=502,
            details={"prompt": prompt, "queries": queries[:8]},
            operation="spotify search fallback",
        )

    playlist = create_playlist(token, user_id, playlist_name, public, description)
    add_tracks(token, playlist["id"], uris[:30])
    return {
        "playlist": playlist,
        "text": f"Created playlist using fallback mode ({reason}).",
        "mode": "fallback_no_tools",
        "track_count": len(uris[:30]),
    }


def generate_playlist(prompt: str, token: str):
    client = _groq_client()
    user_id = me(token)["id"]
    playlist = None

    messages = [
        {"role": "system", "content": "Create a Spotify playlist from the prompt using tools. Return the playlist URL."},
        {"role": "user", "content": prompt},
    ]

    for _ in range(8):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as exc:
            if _is_tool_calling_unsupported_error(exc):
                return _generate_playlist_without_tools(
                    client,
                    prompt,
                    token,
                    user_id,
                    reason="tool calling unsupported for model",
                )
            raise PlaylistGenerationError(
                "Groq request failed.",
                status_code=502,
                details={"error": str(exc)},
                operation="groq chat.completions.create",
            ) from exc
        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            if playlist is None:
                return _generate_playlist_without_tools(
                    client,
                    prompt,
                    token,
                    user_id,
                    reason="model returned no tool calls",
                )
            return {"playlist": playlist, "text": msg.content}

        messages.append({"role": "assistant", "content": msg.content, "tool_calls": tool_calls})

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                raise PlaylistGenerationError(
                    "Model returned invalid tool arguments.",
                    status_code=502,
                    details={"tool_name": name, "raw_arguments": tc.function.arguments},
                    operation="parse tool arguments",
                ) from exc

            if name == "spotify_search_tracks":
                query = args.get("query")
                if not isinstance(query, str) or not query.strip():
                    raise PlaylistGenerationError(
                        "Model did not provide a valid search query.",
                        status_code=502,
                        details={"tool_name": name, "args": args},
                        operation="spotify_search_tracks args",
                    )
                result = {"tracks": search_tracks(token, query, args.get("limit", 10))}
            elif name == "spotify_create_playlist":
                playlist_name = args.get("name")
                if not isinstance(playlist_name, str) or not playlist_name.strip():
                    raise PlaylistGenerationError(
                        "Model did not provide a valid playlist name.",
                        status_code=502,
                        details={"tool_name": name, "args": args},
                        operation="spotify_create_playlist args",
                    )
                playlist = create_playlist(
                    token,
                    user_id,
                    playlist_name,
                    args.get("public", False),
                    args.get("description", ""),
                )
                result = {"playlist": playlist}
            elif name == "spotify_add_tracks":
                playlist_id = args.get("playlist_id")
                uris = args.get("uris")
                if not isinstance(playlist_id, str) or not playlist_id.strip() or not isinstance(uris, list):
                    raise PlaylistGenerationError(
                        "Model did not provide valid playlist track arguments.",
                        status_code=502,
                        details={"tool_name": name, "args": args},
                        operation="spotify_add_tracks args",
                    )
                result = add_tracks(token, playlist_id, uris)
            else:
                result = {"error": "unknown tool"}

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

    raise PlaylistGenerationError(
        "Playlist generation exceeded maximum tool steps.",
        status_code=502,
        operation="tool loop limit",
    )
