from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="TP-Grafos")

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
