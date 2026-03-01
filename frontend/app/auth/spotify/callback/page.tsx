"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

export default function SpotifyCallbackPage() {
  const searchParams = useSearchParams();
  const code = useMemo(() => searchParams.get("code"), [searchParams]);
  const state = useMemo(() => searchParams.get("state"), [searchParams]);
  const error = useMemo(() => searchParams.get("error"), [searchParams]);

  const [exchangeStatus, setExchangeStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [exchangeMessage, setExchangeMessage] = useState<string>("");

  useEffect(() => {
    if (!code || error) return;

    let cancelled = false;
    async function runExchange() {
      setExchangeStatus("loading");
      setExchangeMessage("Exchanging code with backend...");

      const params = new URLSearchParams({ code });
      if (state) params.set("state", state);

      try {
        const res = await fetch(`/api/auth/spotify/exchange?${params.toString()}`, {
          method: "GET",
          cache: "no-store",
        });
        const data = await res.json();
        if (cancelled) return;

        if (!res.ok) {
          const detail =
            typeof data?.detail === "string"
              ? data.detail
              : "Backend token exchange failed.";
          setExchangeStatus("error");
          setExchangeMessage(detail);
          return;
        }

        setExchangeStatus("success");
        setExchangeMessage("Backend token exchange succeeded.");
      } catch {
        if (cancelled) return;
        setExchangeStatus("error");
        setExchangeMessage("Could not reach backend token exchange endpoint.");
      }
    }

    void runExchange();
    return () => {
      cancelled = true;
    };
  }, [code, error, state]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl items-center px-5 py-12">
      <section className="w-full rounded-2xl border border-white/45 bg-white/70 p-6 shadow-lg backdrop-blur sm:p-8">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          Spotify Callback
        </p>
        <h1 className="font-display text-3xl font-bold text-slate-900">
          {error
            ? "Spotify sign-in was canceled"
            : code
              ? "Spotify sign-in successful"
              : "Waiting for Spotify response"}
        </h1>
        <p className="mt-3 text-sm text-slate-700">
          {error
            ? "Spotify returned an authorization error."
            : code
              ? "Authorization code received. Exchanging with backend now."
              : "No code found in the callback URL yet."}
        </p>
        {code && !error ? (
          <div className="mt-3 text-sm text-slate-700">
            <span className="font-semibold">Exchange status:</span>{" "}
            {exchangeStatus === "loading" && "running"}
            {exchangeStatus === "success" && "complete"}
            {exchangeStatus === "error" && "failed"}
            {exchangeStatus === "idle" && "idle"}
            {exchangeMessage ? ` - ${exchangeMessage}` : ""}
          </div>
        ) : null}
        <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600">
          <p>
            <span className="font-semibold">code:</span> {code ?? "none"}
          </p>
          <p className="mt-2">
            <span className="font-semibold">state:</span> {state ?? "none"}
          </p>
          <p className="mt-2">
            <span className="font-semibold">error:</span> {error ?? "none"}
          </p>
        </div>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-full border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-900 hover:text-slate-900"
        >
          Back to home
        </Link>
      </section>
    </main>
  );
}
