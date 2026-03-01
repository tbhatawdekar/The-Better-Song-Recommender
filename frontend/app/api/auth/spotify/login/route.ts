import { NextRequest, NextResponse } from "next/server";

const DEFAULT_SCOPES = ["user-read-email", "user-read-private"];

export async function GET(request: NextRequest) {
  const clientId =
    process.env.SPOTIFY_CLIENT_ID ?? process.env.NEXT_PUBLIC_SPOTIFY_CLIENT_ID;

  if (!clientId) {
    return NextResponse.json(
      {
        error:
          "Missing SPOTIFY_CLIENT_ID. Set it in your frontend environment to enable Spotify login.",
      },
      { status: 500 },
    );
  }

  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? request.nextUrl.origin;
  const redirectUri =
    process.env.SPOTIFY_REDIRECT_URI ?? `${appUrl}/auth/spotify/callback`;
  const scope =
    process.env.SPOTIFY_SCOPE?.trim() || DEFAULT_SCOPES.join(" ");
  const state = crypto.randomUUID();

  const spotifyAuthUrl = new URL("https://accounts.spotify.com/authorize");
  spotifyAuthUrl.searchParams.set("client_id", clientId);
  spotifyAuthUrl.searchParams.set("response_type", "code");
  spotifyAuthUrl.searchParams.set("redirect_uri", redirectUri);
  spotifyAuthUrl.searchParams.set("scope", scope);
  spotifyAuthUrl.searchParams.set("state", state);
  spotifyAuthUrl.searchParams.set("show_dialog", "true");

  const response = NextResponse.redirect(spotifyAuthUrl);
  response.cookies.set("spotify_oauth_state", state, {
    httpOnly: true,
    secure: request.nextUrl.protocol === "https:",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 10,
  });

  return response;
}
