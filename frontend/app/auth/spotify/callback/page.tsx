"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

export default function SpotifyCallbackPage() {
  const searchParams = useSearchParams();
  const code = searchParams.get("code");
  const error = searchParams.get("error");

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
              ? "Authorization code received. You can exchange it for tokens in your backend next."
              : "No code found in the callback URL yet."}
        </p>
        <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600">
          <p>
            <span className="font-semibold">code:</span> {code ?? "none"}
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
