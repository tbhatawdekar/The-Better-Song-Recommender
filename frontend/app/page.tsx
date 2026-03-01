export default function Home() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="page-glow page-glow-left" />
      <div className="page-glow page-glow-right" />

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-5 py-8 sm:px-8 sm:py-10 lg:py-14">
        <header className="fade-in-up rounded-2xl border border-white/35 bg-white/60 p-5 backdrop-blur sm:p-6">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-black/90 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-white">
            <span className="h-2 w-2 rounded-full bg-[#ffc24b]" />
            The Better Song Recommender
          </div>
          <h1 className="font-display text-4xl font-bold leading-tight sm:text-5xl lg:max-w-4xl lg:text-6xl">
            Build playlists from mood, vibe, and intent.
          </h1>
          <p className="mt-4 max-w-2xl text-sm text-slate-700 sm:text-base">
            This is your starter frontend shell. Hook this form to your backend
            and iterate from here.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <a
              href="/api/auth/spotify/login"
              className="inline-flex items-center rounded-full bg-[#1db954] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#159a46]"
            >
              Connect Spotify
            </a>
            <span className="text-xs text-slate-600">
              Redirects to Spotify OAuth sign-in.
            </span>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="fade-in-up rounded-2xl border border-white/45 bg-white/65 p-5 shadow-lg backdrop-blur [animation-delay:120ms] sm:p-6">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Find your next song</h2>
              <span className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-600">
                UI starter
              </span>
            </div>

            <form className="space-y-5">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">
                  Describe your vibe
                </span>
                <textarea
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-900"
                  rows={4}
                  placeholder="Example: upbeat indie-pop for a late-night drive with friends"
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">
                    Energy
                  </span>
                  <input type="range" min="0" max="100" defaultValue="70" />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">
                    Danceability
                  </span>
                  <input type="range" min="0" max="100" defaultValue="62" />
                </label>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">
                    Genre
                  </span>
                  <select className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-slate-900">
                    <option>Any genre</option>
                    <option>Pop</option>
                    <option>Hip-hop</option>
                    <option>Indie</option>
                    <option>R&B</option>
                    <option>EDM</option>
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">
                    Language
                  </span>
                  <select className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-slate-900">
                    <option>Any language</option>
                    <option>English</option>
                    <option>Spanish</option>
                    <option>Korean</option>
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">
                    Max duration
                  </span>
                  <select className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-slate-900">
                    <option>Any length</option>
                    <option>Under 3 min</option>
                    <option>Under 4 min</option>
                    <option>Under 5 min</option>
                  </select>
                </label>
              </div>

              <div className="flex flex-wrap gap-3 pt-1">
                <button
                  type="button"
                  className="rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
                >
                  Generate recommendations
                </button>
                <button
                  type="button"
                  className="rounded-full border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-900 hover:text-slate-900"
                >
                  Clear inputs
                </button>
              </div>
            </form>
          </article>

          <aside className="fade-in-up rounded-2xl border border-white/45 bg-slate-950 p-5 text-white shadow-xl [animation-delay:240ms] sm:p-6">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Starter results panel</h2>
              <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-medium text-slate-200">
                Preview
              </span>
            </div>

            <div className="space-y-3">
              {[
                ["Midnight City", "M83", "Synth-pop"],
                ["Sunflower", "Rex Orange County", "Bedroom pop"],
                ["Blinding Lights", "The Weeknd", "Electro-pop"],
              ].map(([title, artist, tag]) => (
                <div
                  key={title}
                  className="rounded-xl border border-white/15 bg-white/5 p-4 transition hover:-translate-y-0.5 hover:bg-white/10"
                >
                  <p className="font-semibold">{title}</p>
                  <p className="mt-1 text-sm text-slate-300">{artist}</p>
                  <p className="mt-3 inline-flex rounded-full border border-white/20 px-2.5 py-1 text-xs text-slate-200">
                    {tag}
                  </p>
                </div>
              ))}
            </div>

            <p className="mt-5 text-xs text-slate-300">
              Swap these placeholders with live data from your recommendation
              endpoint.
            </p>
          </aside>
        </section>
      </main>
    </div>
  );
}
