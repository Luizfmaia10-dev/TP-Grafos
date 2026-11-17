import pytest

from app.domain import Station, TemporaryVertex, VehicleType
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


def test_snap_origin_connects_to_nearest_real_station_and_cleans_up():
    graph = TransportGraph()
    nearest = Station("nearest", "Nearest", 0.0, 0.0)
    farther = Station("farther", "Farther", 0.0, 0.006)
    existing_temporary = TemporaryVertex(
        "existing-temporary", "Existing temporary", 0.0, 0.001, "origin"
    )
    for station in (nearest, farther, existing_temporary):
        graph.add_station(station)
    simulator = RouteSimulator(graph, max_speed=1.0)

    with simulator.snap_to_network(0.0, 0.001, "origin") as vertex:
        connection = graph.get_neighbors(vertex)[0]

        assert isinstance(vertex, TemporaryVertex)
        assert vertex.marker_type == "origin"
        assert vertex.station_id != existing_temporary.station_id
        assert connection.route_id == "temporary-walk"
        assert connection.destination == nearest
        assert connection.vehicle_type is VehicleType.WALK
        assert connection.distance == pytest.approx(0.111195, abs=0.000001)
        assert connection.travel_time == pytest.approx(1.33434, abs=0.00001)
        assert connection.departure_time == 0.0

    assert list(graph.iter_stations()) == [nearest, farther, existing_temporary]
    assert graph.get_neighbors(nearest) == []
    assert graph.get_neighbors(farther) == []


def test_snap_destination_connects_nearest_station_to_temporary_vertex():
    graph = TransportGraph()
    nearest = Station("nearest", "Nearest", 0.0, 0.0)
    graph.add_station(nearest)
    simulator = RouteSimulator(graph, max_speed=1.0)

    with simulator.snap_to_network(0.0, 0.001, "destination") as vertex:
        connection = graph.get_neighbors(nearest)[0]

        assert connection.destination == vertex
        assert connection.vehicle_type is VehicleType.WALK
        assert graph.get_neighbors(vertex) == []

    assert list(graph.iter_stations()) == [nearest]
    assert graph.get_neighbors(nearest) == []


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        (91.0, 0.0),
        (-91.0, 0.0),
        (0.0, 181.0),
        (0.0, -181.0),
        (float("nan"), 0.0),
    ],
)
def test_snap_rejects_invalid_coordinates(latitude, longitude):
    graph = TransportGraph()
    station = Station("station", "Station", 0.0, 0.0)
    graph.add_station(station)
    simulator = RouteSimulator(graph, max_speed=1.0)

    with pytest.raises(ValueError):
        with simulator.snap_to_network(latitude, longitude, "origin"):
            pass

    assert list(graph.iter_stations()) == [station]


def test_snap_rejects_unknown_marker_type_without_changing_graph():
    graph = TransportGraph()
    station = Station("station", "Station", 0.0, 0.0)
    graph.add_station(station)
    simulator = RouteSimulator(graph, max_speed=1.0)

    with pytest.raises(ValueError):
        with simulator.snap_to_network(0.0, 0.001, "waypoint"):
            pass

    assert list(graph.iter_stations()) == [station]
    assert graph.get_neighbors(station) == []


def test_snap_rejects_station_farther_than_800_metres():
    graph = TransportGraph()
    station = Station("station", "Station", 0.0, 0.0)
    graph.add_station(station)
    simulator = RouteSimulator(graph, max_speed=1.0)

    with pytest.raises(ValueError):
        with simulator.snap_to_network(0.0, 0.008, "origin"):
            pass

    assert list(graph.iter_stations()) == [station]
    assert graph.get_neighbors(station) == []


def test_snap_rejects_graph_without_real_stations_and_leaves_it_empty():
    graph = TransportGraph()
    simulator = RouteSimulator(graph, max_speed=1.0)

    with pytest.raises(ValueError):
        with simulator.snap_to_network(0.0, 0.0, "origin"):
            pass

    assert list(graph.iter_stations()) == []


def test_snap_cleans_up_when_route_search_raises():
    graph = TransportGraph()
    station = Station("station", "Station", 0.0, 0.0)
    graph.add_station(station)
    simulator = RouteSimulator(graph, max_speed=1.0)

    with pytest.raises(RuntimeError, match="search failed"):
        with simulator.snap_to_network(0.0, 0.001, "destination"):
            raise RuntimeError("search failed")

    assert list(graph.iter_stations()) == [station]
    assert graph.get_neighbors(station) == []
