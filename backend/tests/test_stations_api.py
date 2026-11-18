"""Station autocomplete uses the loaded catalog without changing the graph."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.domain import Station
from app.graph import TransportGraph
from app.main import create_app
from app.network import RouteNetwork, get_network


@pytest.fixture(autouse=True)
def clear_gtfs_environment(monkeypatch):
    monkeypatch.delenv("GTFS_SERVICE_DATE", raising=False)
    monkeypatch.delenv("GTFS_DIR", raising=False)


@pytest.fixture
def station_client():
    graph = TransportGraph()
    stations = [
        Station("001", "Estação São Gabriel", -19.8801, -43.9282),
        Station("002", "Praça Sete", -19.9191, -43.9386),
        Station("003", "São Gabriel - Plataforma B", -19.8802, -43.9283),
        Station("004", "Praça Sete", -19.9192, -43.9387),
    ]
    for station in stations:
        graph.add_station(station)
    network = RouteNetwork(graph, {s.station_id: s for s in stations}, 1.0, date(2026, 11, 17))
    app = create_app()
    app.dependency_overrides[get_network] = lambda: network
    with TestClient(app) as client:
        yield client


def test_lists_stations_with_string_ids_and_coordinates(station_client):
    response = station_client.get("/stations")

    assert response.status_code == 200
    assert response.json() == [
        {"station_id": "001", "name": "Estação São Gabriel", "latitude": -19.8801, "longitude": -43.9282},
        {"station_id": "002", "name": "Praça Sete", "latitude": -19.9191, "longitude": -43.9386},
        {"station_id": "003", "name": "São Gabriel - Plataforma B", "latitude": -19.8802, "longitude": -43.9283},
        {"station_id": "004", "name": "Praça Sete", "latitude": -19.9192, "longitude": -43.9387},
    ]


@pytest.mark.parametrize("query", ["sao gabriel", " SÃO GABRIEL ", "São Gabriel", "gabriel"])
def test_matches_name_ignoring_case_accents_and_outer_whitespace(station_client, query):
    response = station_client.get("/stations", params={"query": query})

    assert response.status_code == 200
    assert [station["station_id"] for station in response.json()] == ["001", "003"]


def test_matches_station_id_without_losing_leading_zeroes(station_client):
    response = station_client.get("/stations", params={"query": "002"})

    assert response.status_code == 200
    assert [station["station_id"] for station in response.json()] == ["002"]


def test_preserves_distinct_stations_with_the_same_name(station_client):
    response = station_client.get("/stations", params={"query": "praca"})

    assert [station["station_id"] for station in response.json()] == ["002", "004"]


def test_no_matches_returns_an_empty_list(station_client):
    response = station_client.get("/stations", params={"query": "unknown"})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("query", ["", "   "])
def test_blank_query_lists_first_stations_up_to_limit(station_client, query):
    response = station_client.get("/stations", params={"query": query, "limit": 2})

    assert response.status_code == 200
    assert [station["station_id"] for station in response.json()] == ["001", "002"]


def test_limit_is_applied_after_filtering(station_client):
    response = station_client.get("/stations", params={"query": "praca", "limit": 1})

    assert response.status_code == 200
    assert [station["station_id"] for station in response.json()] == ["002"]


@pytest.mark.parametrize("limit", [0, -1, 101, "invalid", "1.5"])
def test_invalid_limit_returns_validation_error(station_client, limit):
    response = station_client.get("/stations", params={"limit": limit})

    assert response.status_code == 422


def test_default_and_maximum_limits():
    graph = TransportGraph()
    stations = {str(i): Station(str(i), f"Station {i}", 0, 0) for i in range(110)}
    for station in stations.values():
        graph.add_station(station)
    network = RouteNetwork(graph, stations, 1.0, date(2026, 11, 17))
    app = create_app()
    app.dependency_overrides[get_network] = lambda: network

    with TestClient(app) as client:
        assert len(client.get("/stations").json()) == 20
        assert len(client.get("/stations?limit=100").json()) == 100


def test_empty_catalog_returns_an_empty_list():
    app = create_app()
    network = RouteNetwork(TransportGraph(), {}, 1.0, date(2026, 11, 17))
    app.dependency_overrides[get_network] = lambda: network

    with TestClient(app) as client:
        response = client.get("/stations")
        assert response.status_code == 200
        assert response.json() == []


def test_unconfigured_network_returns_service_unavailable():
    with TestClient(create_app()) as client:
        response = client.get("/stations")

    assert response.status_code == 503
    assert response.json() == {"detail": "Transport network is not configured"}
