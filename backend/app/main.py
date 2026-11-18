from contextlib import asynccontextmanager
from datetime import date
from os import environ
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.stations import router as stations_router
from app.network import RouteNetwork

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"


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

    app.include_router(stations_router)
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
