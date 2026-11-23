from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.domain import Station, TemporaryVertex
from app.graph import TransportGraph
from app.main import create_app
from app.network import RouteNetwork, get_network


@pytest.fixture
def snap_network():
    graph = TransportGraph()
    stations = {
        "near": Station("near", "Near", 0.0, 0.001),
        "far": Station("far", "Far", 0.0, 0.004),
        "outside": Station("outside", "Outside", 0.0, 0.03),
    }
    for station in stations.values():
        graph.add_station(station)
    graph.add_station(TemporaryVertex("temporary", "Temporary", 0.0, 0.0, "origin"))
    return RouteNetwork(graph, stations, 1.0, date(2026, 11, 17))


@pytest.fixture
def snap_client(snap_network):
    app = create_app()
    app.dependency_overrides[get_network] = lambda: snap_network
    with TestClient(app) as client:
        yield client


def test_snap_candidates_are_sorted_and_exclude_temporary_vertices(snap_client):
    response = snap_client.post(
        "/snap/candidates",
        json={"latitude": 0.0, "longitude": 0.0, "max_walk_meters": 800},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["count"] == 2
    assert result["minimum_distance_meters"] == 111
    assert [item["station"]["station_id"] for item in result["candidates"]] == [
        "near",
        "far",
    ]
    assert [item["distance_meters"] for item in result["candidates"]] == [111, 445]


def test_snap_candidates_report_minimum_distance_when_limit_is_too_small(snap_client):
    response = snap_client.post(
        "/snap/candidates",
        json={"latitude": 0.0, "longitude": 0.0, "max_walk_meters": 100},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "no_station_within_limit",
            "minimum_distance_meters": 111,
        }
    }


def test_snap_candidates_accept_any_whole_metre_inside_supported_interval(snap_client):
    response = snap_client.post(
        "/snap/candidates",
        json={"latitude": 0.0, "longitude": 0.0, "max_walk_meters": 151},
    )

    assert response.status_code == 200
    assert response.json()["minimum_distance_meters"] == 111


@pytest.mark.parametrize("max_walk_meters", [0, 99, 2001])
def test_snap_candidates_reject_limit_outside_supported_interval(
    snap_client, max_walk_meters
):
    response = snap_client.post(
        "/snap/candidates",
        json={
            "latitude": 0.0,
            "longitude": 0.0,
            "max_walk_meters": max_walk_meters,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": {"code": "snap_distance_out_of_range"}
    }


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(91, 0), (-91, 0), (0, 181), (0, -181)],
)
def test_snap_candidates_reject_invalid_coordinates(
    snap_client, latitude, longitude
):
    response = snap_client.post(
        "/snap/candidates",
        json={
            "latitude": latitude,
            "longitude": longitude,
            "max_walk_meters": 800,
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "invalid_coordinates"}}


def test_snap_candidates_report_no_reachable_station_inside_global_maximum(
    snap_client,
):
    response = snap_client.post(
        "/snap/candidates",
        json={"latitude": 1.0, "longitude": 1.0, "max_walk_meters": 800},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "no_station_within_limit",
            "minimum_distance_meters": None,
        }
    }


def test_snap_candidates_require_a_loaded_network():
    with TestClient(create_app()) as client:
        response = client.post(
            "/snap/candidates",
            json={"latitude": 0.0, "longitude": 0.0, "max_walk_meters": 800},
        )

    assert response.status_code == 503
