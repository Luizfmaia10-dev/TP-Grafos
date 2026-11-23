from contextlib import asynccontextmanager
from datetime import date
from os import environ
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as routes_router
from app.api.snap import router as snap_router
from app.api.stations import router as stations_router
from app.network import RouteNetwork

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
LOCAL_ENV_FILE = PROJECT_DIR / ".env.local"


def read_local_setting(name: str) -> str | None:
    """Read one local setting without adding a dotenv dependency."""
    environment_value = environ.get(name)
    if environment_value:
        return environment_value
    if not LOCAL_ENV_FILE.exists():
        return None
    for line in LOCAL_ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == name:
            return value.strip() or None
    return None


def create_app(
    *, data_directory: Path | None = None, service_date: date | None = None
) -> FastAPI:
    """Create the API; optionally load a service-day graph during startup."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        selected_date = service_date
        configured_date = environ.get("GTFS_SERVICE_DATE")
        if selected_date is None and configured_date is not None:
            try:
                selected_date = date.fromisoformat(configured_date)
                if selected_date.isoformat() != configured_date:
                    raise ValueError
            except ValueError:
                raise ValueError("GTFS_SERVICE_DATE must be a valid YYYY-MM-DD date") from None
        directory = data_directory or Path(environ.get("GTFS_DIR", PROJECT_DIR / "data/gtfs"))
        app.state.network = (
            None if selected_date is None else RouteNetwork.load(directory, selected_date)
        )
        try:
            yield
        finally:
            app.state.network = None

    app = FastAPI(title="TP-Grafos", lifespan=lifespan)
    app.state.network = None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/config/geocoding")
    def geocoding_config():
        api_key = read_local_setting("GEOAPIFY_API_KEY")
        return {"api_key": api_key, "available": api_key is not None}

    app.include_router(stations_router)
    app.include_router(snap_router)
    app.include_router(routes_router)
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
