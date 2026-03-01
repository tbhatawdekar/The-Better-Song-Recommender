import { NextRequest, NextResponse } from "next/server";

function jsonFromText(text: string): unknown {
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const error = request.nextUrl.searchParams.get("error");
  const state = request.nextUrl.searchParams.get("state");

  if (error) {
    return NextResponse.json({ detail: `Spotify auth error: ${error}` }, { status: 400 });
  }

  if (!code) {
    return NextResponse.json({ detail: "Missing Spotify authorization code." }, { status: 400 });
  }

  const backendBase =
    process.env.BACKEND_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL ??
    "http://127.0.0.1:8000";

  let backendUrl: URL;
  try {
    backendUrl = new URL("/auth/callback", backendBase);
  } catch {
    return NextResponse.json(
      { detail: "Invalid BACKEND_URL or NEXT_PUBLIC_BACKEND_URL." },
      { status: 500 },
    );
  }

  backendUrl.searchParams.set("code", code);
  if (state) {
    backendUrl.searchParams.set("state", state);
  }

  const response = await fetch(backendUrl.toString(), {
    method: "GET",
    cache: "no-store",
  });
  const raw = await response.text();
  const payload = jsonFromText(raw);

  return NextResponse.json(payload, { status: response.status });
}
