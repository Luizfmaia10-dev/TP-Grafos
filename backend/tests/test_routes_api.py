"""Route searches validate input and expose the time-dependent engine over HTTP."""

import csv
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.domain import Connection, Station, VehicleType
from app.graph import TransportGraph
from app.main import create_app
from app.network import RouteNetwork, get_network
from app.route_simulator import RouteSimulator


QUERY = {"origin_id": "001", "destination_id": "003", "departure_time": "07:59"}


@pytest.fixture(autouse=True)
def clear_gtfs_environment(monkeypatch):
    monkeypatch.delenv("GTFS_SERVICE_DATE", raising=False)
    monkeypatch.delenv("GTFS_DIR", raising=False)


@pytest.fixture
def network():
    graph = TransportGraph()
    stations = {
        "001": Station("001", "Central", -19.9, -43.9),
        "002": Station("002", "Transfer", -19.901, -43.901),
        "003": Station("003", "Terminal", -19.902, -43.902),
        "004": Station("004", "Isolated", -19.903, -43.903),
    }
    for station in stations.values():
        graph.add_station(station)
    graph.add_connection(stations["001"], Connection("bus", stations["002"], VehicleType.BUS, 5.5, 1, 480))
    graph.add_connection(stations["002"], Connection("metro", stations["003"], VehicleType.SUBWAY, 4.25, 2, 487))
    # The direct connection arrives later than the transfer route.
    graph.add_connection(stations["001"], Connection("slow", stations["003"], VehicleType.BUS, 30, 3, 480))
    return RouteNetwork(graph, stations, RouteSimulator.max_speed_of(graph), date(2026, 11, 17))


@pytest.fixture
def client(network):
    app = create_app()
    app.dependency_overrides[get_network] = lambda: network
    with TestClient(app) as client:
        yield client


def test_search_returns_fastest_route_with_transfer_and_exact_costs(client):
    response = client.post("/routes/search", json=QUERY)

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "found"
    assert result["service_date"] == "2026-11-17"
    assert result["departure_time"] == "07:59"
    assert result["origin"]["station_id"] == "001"
    assert result["destination"]["station_id"] == "003"
    route = result["route"]
    assert route["arrival_time"] == "08:11:15"
    assert route["total_seconds"] == 735
    assert route["waiting_seconds"] == 150
    assert route["travel_seconds"] == 585
    assert route["distance_km"] == pytest.approx(3)
    first, second = route["steps"]
    assert first == {
        "origin": result["origin"],
        "destination": {"station_id": "002", "name": "Transfer", "latitude": -19.901, "longitude": -43.901},
        "route_id": "bus", "vehicle_type": "BUS", "departure_time": "08:00:00",
        "arrival_time": "08:05:30", "waiting_seconds": 60, "travel_seconds": 330, "distance_km": 1,
    }
    assert second["origin"] == first["destination"]
    assert second["destination"] == result["destination"]
    assert second["route_id"] == "metro"
    assert second["vehicle_type"] == "SUBWAY"
    assert second["departure_time"] == "08:07:00"
    assert second["arrival_time"] == "08:11:15"
    assert second["waiting_seconds"] == 90
    assert second["travel_seconds"] == 255
    assert route["instructions"] == [
        "Aguarde em Central até 08:00:00.",
        "Pegue o ônibus bus de Central até Transfer às 08:00:00; chegada às 08:05:30.",
        "Aguarde em Transfer até 08:07:00.",
        "Pegue o metrô metro de Transfer até Terminal às 08:07:00; chegada às 08:11:15.",
    ]


def test_direct_route_departing_exactly_at_requested_time(client):
    response = client.post("/routes/search", json={**QUERY, "destination_id": "002", "departure_time": "08:00"})

    assert response.status_code == 200
    route = response.json()["route"]
    assert route["waiting_seconds"] == 0
    assert route["total_seconds"] == 330
    assert len(route["steps"]) == 1


@pytest.mark.parametrize("changes", [
    {"destination_id": "004"},
    {"departure_time": "08:01"},
    {"origin_id": "003", "destination_id": "001"},
])
def test_unreachable_or_missed_departure_returns_no_route(client, changes):
    response = client.post("/routes/search", json=QUERY | changes)

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "no-route"
    assert result["route"] is None
    assert result["service_date"] == "2026-11-17"


def test_walk_departs_immediately_and_does_not_modify_shared_connections(client, network):
    walk = Connection("walk", network.stations["003"], VehicleType.WALK, 2.25, 0.2, 0)
    network.graph.add_connection(network.stations["002"], walk)

    for _ in range(2):
        response = client.post("/routes/search", json=QUERY)
        assert response.status_code == 200
        route = response.json()["route"]
        assert route["arrival_time"] == "08:07:45"
        assert route["total_seconds"] == 525
        assert route["waiting_seconds"] == 60
        assert route["travel_seconds"] == 465
        step = route["steps"][1]
        assert step["vehicle_type"] == "WALK"
        assert step["departure_time"] == "08:05:30"
        assert step["waiting_seconds"] == 0
    assert walk.departure_time == 0
    assert len(list(network.graph.iter_stations())) == 4


def test_times_above_24_hours_stay_in_the_loaded_service_day(client, network):
    network.graph.add_connection(network.stations["001"], Connection(
        "night", network.stations["003"], VehicleType.BUS, 1.25, 1, 1500.5,
    ))
    response = client.post("/routes/search", json={**QUERY, "departure_time": "25:00"})

    assert response.status_code == 200
    result = response.json()
    assert result["service_date"] == "2026-11-17"
    assert result["route"]["arrival_time"] == "25:01:45"
    assert result["route"]["total_seconds"] == 105
    assert result["route"]["waiting_seconds"] == 30


def test_fractional_seconds_round_absolute_times_consistently(client, network):
    network.graph.add_connection(network.stations["001"], Connection(
        "fractional", network.stations["003"], VehicleType.BUS, 0.6 / 60, 0, 480 + 0.6 / 60,
    ))
    response = client.post("/routes/search", json={**QUERY, "departure_time": "08:00"})

    assert response.status_code == 200
    route = response.json()["route"]
    step = route["steps"][0]
    assert step["departure_time"] == "08:00:01"
    assert step["arrival_time"] == "08:00:01"
    assert route["total_seconds"] == 1
    assert route["waiting_seconds"] == 1
    assert route["travel_seconds"] == 0


@pytest.mark.parametrize("field", ["origin_id", "destination_id"])
def test_unknown_station_returns_404(client, field):
    response = client.post("/routes/search", json={**QUERY, field: "unknown"})

    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "unknown_station", "field": field}}


@pytest.mark.parametrize("changes", [
    {"origin_id": "003"}, {"origin_id": ""}, {"destination_id": "   "},
    {"origin_id": 1}, {"destination_id": None},
    {"departure_time": "08:00:00"}, {"departure_time": "8:00"},
    {"departure_time": "08:60"}, {"departure_time": "08:00:60"},
    {"departure_time": "-01:00"}, {"departure_time": "08:00\n"},
    {"departure_time": 480}, {"service_date": "2026-11-18"},
    {"departure_time": "9" * 400 + ":00"},
])
def test_invalid_search_returns_422(client, changes):
    response = client.post("/routes/search", json=QUERY | changes)

    assert response.status_code == 422


@pytest.mark.parametrize("field", ["origin_id", "destination_id", "departure_time"])
def test_missing_required_field_returns_422(client, field):
    response = client.post("/routes/search", json={key: value for key, value in QUERY.items() if key != field})

    assert response.status_code == 422


def test_unconfigured_network_returns_503():
    with TestClient(create_app()) as client:
        response = client.post("/routes/search", json=QUERY)

    assert response.status_code == 503


def test_synthetic_gtfs_startup_and_search_respect_service_calendar(tmp_path):
    tables = {
        "stops.txt": [("stop_id", "stop_name", "stop_lat", "stop_lon"),
                      ("001", "Central", -19.9, -43.9), ("003", "Terminal", -19.901, -43.901)],
        "routes.txt": [("route_id", "route_type"), ("bus", "3")],
        "trips.txt": [("route_id", "service_id", "trip_id"),
                      ("bus", "weekday", "active"), ("bus", "weekend", "inactive")],
        "stop_times.txt": [("trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time"),
                           ("active", "001", 1, "08:00:00", "08:00:00"),
                           ("active", "003", 2, "08:10:00", "08:10:00"),
                           ("inactive", "001", 1, "07:59:30", "07:59:30"),
                           ("inactive", "003", 2, "08:01:00", "08:01:00")],
        "calendar.txt": [("service_id", "monday", "tuesday", "wednesday", "thursday", "friday",
                          "saturday", "sunday", "start_date", "end_date"),
                         ("weekday", 1, 1, 1, 1, 1, 0, 0, "20260101", "20261231"),
                         ("weekend", 0, 0, 0, 0, 0, 1, 1, "20260101", "20261231")],
    }
    for filename, rows in tables.items():
        with (tmp_path / filename).open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerows(rows)

    with TestClient(create_app(data_directory=tmp_path, service_date=date(2026, 11, 17))) as client:
        assert len(client.get("/stations").json()) == 2
        response = client.post("/routes/search", json=QUERY)
        assert response.status_code == 200
        assert response.json()["route"]["arrival_time"] == "08:10:00"
        assert response.json()["route"]["total_seconds"] == 660

    with TestClient(create_app(data_directory=tmp_path, service_date=date(2027, 1, 1))) as client:
        response = client.post("/routes/search", json=QUERY)
        assert response.status_code == 200
        assert response.json()["status"] == "no-route"
