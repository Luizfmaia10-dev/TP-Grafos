"""The API loads one service-day network for the application's lifetime."""

from datetime import date

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.main import create_app
from app.network import RouteNetwork, get_network


@pytest.fixture(autouse=True)
def clear_gtfs_environment(monkeypatch):
    monkeypatch.delenv("GTFS_SERVICE_DATE", raising=False)
    monkeypatch.delenv("GTFS_DIR", raising=False)


def add_network_probe(app):
    @app.get("/network-probe")
    def probe(network: RouteNetwork = Depends(get_network)):
        return {"service_date": network.service_date.isoformat()}

    # Register the probe before the static frontend mount.
    app.router.routes.insert(-1, app.router.routes.pop())


def test_demo_starts_without_loading_gtfs():
    app = create_app()
    add_network_probe(app)

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/").status_code == 200
        response = client.get("/network-probe")
        assert response.status_code == 503
        assert response.json() == {"detail": "Transport network is not configured"}


def test_network_is_loaded_once_and_shared_between_requests(monkeypatch, tmp_path):
    from app.domain import Connection, Station, VehicleType
    from app.graph import TransportGraph

    graph = TransportGraph()
    origin = Station("001", "Central", -19.9, -43.9)
    destination = Station("002", "Terminal", -19.91, -43.91)
    graph.add_station(origin)
    graph.add_station(destination)
    graph.add_connection(origin, Connection("r", destination, VehicleType.BUS, 10, 2, 480))
    loads = []

    class FakeLoader:
        def __init__(self, data_directory, *, service_date):
            loads.append((data_directory, service_date))

        def build_graph(self):
            return graph

    monkeypatch.setattr("app.network.DataLoader", FakeLoader)
    app = create_app(data_directory=tmp_path, service_date=date(2026, 11, 17))
    add_network_probe(app)

    with TestClient(app) as client:
        network = app.state.network
        assert network.graph is graph
        assert network.stations == {"001": origin, "002": destination}
        assert network.max_speed == pytest.approx(0.2)
        for _ in range(2):
            assert client.get("/network-probe").json() == {"service_date": "2026-11-17"}
            assert app.state.network is network
        assert loads == [(tmp_path, date(2026, 11, 17))]

    assert app.state.network is None


def test_environment_selects_directory_and_service_date(monkeypatch, tmp_path):
    from app.graph import TransportGraph

    loads = []

    class FakeLoader:
        def __init__(self, data_directory, *, service_date):
            loads.append((data_directory, service_date))

        def build_graph(self):
            return TransportGraph()

    monkeypatch.setattr("app.network.DataLoader", FakeLoader)
    monkeypatch.setenv("GTFS_DIR", str(tmp_path))
    monkeypatch.setenv("GTFS_SERVICE_DATE", "2026-11-17")

    with TestClient(create_app()):
        assert loads == [(tmp_path, date(2026, 11, 17))]


@pytest.mark.parametrize("value", ["invalid", "2026-02-30", "20261117", "2026-W47-2"])
def test_invalid_service_date_stops_startup(monkeypatch, value):
    monkeypatch.setenv("GTFS_SERVICE_DATE", value)

    with pytest.raises(ValueError, match="GTFS_SERVICE_DATE"):
        with TestClient(create_app()):
            pass


def test_configured_feed_failure_stops_startup(tmp_path):
    with pytest.raises(FileNotFoundError):
        with TestClient(create_app(data_directory=tmp_path, service_date=date(2026, 11, 17))):
            pass
