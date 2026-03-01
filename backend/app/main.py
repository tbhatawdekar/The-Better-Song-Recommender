from pathlib import Path

from fastapi import FastAPI
from .routers.auth import router as auth_router
from .routers.generatePlaylist import router as playlist_router

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Load repo-level .env when running from backend/
if load_dotenv is not None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

app = FastAPI()

app.include_router(auth_router)
app.include_router(playlist_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
