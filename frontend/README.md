# Frontend

Next.js frontend for The Better Song Recommender.

## Run locally

```bash
npm install
npm run dev
```

App runs at `http://localhost:3000`.

## Spotify login kickoff

This repo now includes the first step of Spotify auth:
- A homepage `Connect Spotify` button
- `GET /api/auth/spotify/login` to redirect users to Spotify OAuth
- A callback page at `/auth/spotify/callback`

### Setup

1. Copy `.env.example` to `.env.local` in the `frontend` folder.
2. Set `SPOTIFY_CLIENT_ID` from your Spotify app settings.
3. In Spotify Developer Dashboard, add this redirect URI:
   `http://localhost:3000/auth/spotify/callback`

After that, click `Connect Spotify` in the UI.
