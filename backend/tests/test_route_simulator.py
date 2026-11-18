import pytest

from app.domain import Connection, Station, TemporaryVertex, VehicleType
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


def test_max_speed_of_finds_highest_speed_among_edges_with_positive_travel_time():
    graph = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    station_b = Station("B", "Station B", 0.0, 0.1)
    station_c = Station("C", "Station C", 0.0, 0.2)
    for station in (station_a, station_b, station_c):
        graph.add_station(station)

    # 10 km in 10 min -> 1.0 km/min
    conn_ab = Connection("r1", station_b, VehicleType.BUS, 10.0, 10.0, 480.0)
    # 20 km in 10 min -> 2.0 km/min
    conn_bc = Connection("r2", station_c, VehicleType.SUBWAY, 10.0, 20.0, 495.0)
    graph.add_connection(station_a, conn_ab)
    graph.add_connection(station_b, conn_bc)

    assert RouteSimulator.max_speed_of(graph) == pytest.approx(2.0)


def test_max_speed_of_ignores_edges_with_zero_travel_time():
    graph = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    station_b = Station("B", "Station B", 0.0, 0.1)
    for station in (station_a, station_b):
        graph.add_station(station)

    # Edge with travel_time == 0.0 should not raise ZeroDivisionError
    conn_zero = Connection("r0", station_b, VehicleType.BUS, 0.0, 0.0, 480.0)
    conn_valid = Connection("r1", station_b, VehicleType.BUS, 15.0, 15.0, 500.0)
    graph.add_connection(station_a, conn_zero)
    graph.add_connection(station_a, conn_valid)

    assert RouteSimulator.max_speed_of(graph) == pytest.approx(1.0)


def test_max_speed_of_empty_or_zero_time_graph_returns_default_walking_speed():
    empty_graph = TransportGraph()
    assert RouteSimulator.max_speed_of(empty_graph) == pytest.approx(5.0 / 60.0)

    graph_only_zero = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    graph_only_zero.add_station(station_a)
    graph_only_zero.add_connection(
        station_a, Connection("r0", station_a, VehicleType.BUS, 0.0, 0.0, 480.0)
    )
    assert RouteSimulator.max_speed_of(graph_only_zero) == pytest.approx(5.0 / 60.0)


def test_calculate_route_direct_trip_chooses_first_departure_greater_than_or_equal_to_query_time():
    graph = TransportGraph()
    origin = Station("A", "Station A", 0.0, 0.0)
    destination = Station("B", "Station B", 0.0, 0.1)
    graph.add_station(origin)
    graph.add_station(destination)

    conn_early = Connection("line-1", destination, VehicleType.BUS, 15.0, 5.0, 480.0)
    conn_late = Connection("line-1", destination, VehicleType.BUS, 15.0, 5.0, 510.0)
    graph.add_connection(origin, conn_early)
    graph.add_connection(origin, conn_late)

    simulator = RouteSimulator(graph, max_speed=1.0)
    route = simulator.calculate_route(origin, destination, departure_time=450.0)

    assert route == [(origin, conn_early)]


def test_calculate_route_accepts_departure_exactly_at_query_time():
    graph = TransportGraph()
    origin = Station("A", "Station A", 0.0, 0.0)
    destination = Station("B", "Station B", 0.0, 0.1)
    graph.add_station(origin)
    graph.add_station(destination)

    conn_exact = Connection("line-1", destination, VehicleType.BUS, 15.0, 5.0, 480.0)
    conn_later = Connection("line-1", destination, VehicleType.BUS, 15.0, 5.0, 510.0)
    graph.add_connection(origin, conn_exact)
    graph.add_connection(origin, conn_later)

    simulator = RouteSimulator(graph, max_speed=1.0)
    route = simulator.calculate_route(origin, destination, departure_time=480.0)

    assert route == [(origin, conn_exact)]


def test_calculate_route_ignores_departures_before_query_time():
    graph = TransportGraph()
    origin = Station("A", "Station A", 0.0, 0.0)
    destination = Station("B", "Station B", 0.0, 0.1)
    graph.add_station(origin)
    graph.add_station(destination)

    conn_past = Connection("line-1", destination, VehicleType.BUS, 15.0, 5.0, 480.0)
    conn_future = Connection("line-1", destination, VehicleType.BUS, 15.0, 5.0, 510.0)
    graph.add_connection(origin, conn_past)
    graph.add_connection(origin, conn_future)

    simulator = RouteSimulator(graph, max_speed=1.0)
    route = simulator.calculate_route(origin, destination, departure_time=490.0)

    assert route == [(origin, conn_future)]


def test_calculate_route_same_origin_and_destination_returns_empty_list():
    graph = TransportGraph()
    station = Station("A", "Station A", 0.0, 0.0)
    graph.add_station(station)

    simulator = RouteSimulator(graph, max_speed=1.0)
    assert simulator.calculate_route(station, station, departure_time=480.0) == []


def test_calculate_route_returns_none_when_no_departures_after_query_time():
    graph = TransportGraph()
    origin = Station("A", "Station A", 0.0, 0.0)
    destination = Station("B", "Station B", 0.0, 0.1)
    graph.add_station(origin)
    graph.add_station(destination)

    conn = Connection("line-1", destination, VehicleType.BUS, 15.0, 5.0, 480.0)
    graph.add_connection(origin, conn)

    simulator = RouteSimulator(graph, max_speed=1.0)
    assert simulator.calculate_route(origin, destination, departure_time=500.0) is None


