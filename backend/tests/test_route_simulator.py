import pytest

from app.domain import Station
from app.graph import TransportGraph
from app.route_simulator import RouteSimulator, haversine


def test_haversine_same_point_is_zero():
    assert haversine(-19.9167, -43.9345, -19.9167, -43.9345) == 0


def test_haversine_one_degree_of_latitude_is_about_111_km():
    assert haversine(0, 0, 1, 0) == pytest.approx(111.19, abs=0.01)


def test_haversine_is_symmetric():
    assert haversine(-19.92, -43.94, -19.85, -43.97) == pytest.approx(
        haversine(-19.85, -43.97, -19.92, -43.94)
    )


def test_heuristic_divides_distance_by_max_speed():
    origin = Station("A", "A", 0, 0)
    target = Station("B", "B", 1, 0)
    simulator = RouteSimulator(TransportGraph(), max_speed=1.0)  # km/min

    assert simulator.heuristic(origin, target) == pytest.approx(111.19, abs=0.01)