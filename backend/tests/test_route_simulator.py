import random
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


def test_calculate_route_reconstructs_two_leg_path_in_chronological_order():
    graph = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    station_b = Station("B", "Station B", 0.0, 0.1)
    station_c = Station("C", "Station C", 0.0, 0.2)
    for station in (station_a, station_b, station_c):
        graph.add_station(station)

    conn_ab = Connection("line-1", station_b, VehicleType.BUS, 15.0, 5.0, 480.0)
    conn_bc = Connection("line-2", station_c, VehicleType.SUBWAY, 10.0, 6.0, 500.0)
    graph.add_connection(station_a, conn_ab)
    graph.add_connection(station_b, conn_bc)

    simulator = RouteSimulator(graph, max_speed=1.0)
    route = simulator.calculate_route(station_a, station_c, departure_time=450.0)

    assert route == [(station_a, conn_ab), (station_b, conn_bc)]


def test_calculate_route_transfer_respects_chronological_arrival_at_intermediate_station():
    graph = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    station_b = Station("B", "Station B", 0.0, 0.1)
    station_c = Station("C", "Station C", 0.0, 0.2)
    for station in (station_a, station_b, station_c):
        graph.add_station(station)

    # Arrives at B at 480 + 15 = 495.0
    conn_ab = Connection("line-1", station_b, VehicleType.BUS, 15.0, 5.0, 480.0)
    # Departs B at 490.0 (too early!)
    conn_bc_early = Connection("line-2", station_c, VehicleType.BUS, 10.0, 5.0, 490.0)
    # Departs B at 505.0 (can board!)
    conn_bc_valid = Connection("line-2", station_c, VehicleType.BUS, 10.0, 5.0, 505.0)
    graph.add_connection(station_a, conn_ab)
    graph.add_connection(station_b, conn_bc_early)
    graph.add_connection(station_b, conn_bc_valid)

    simulator = RouteSimulator(graph, max_speed=1.0)
    route = simulator.calculate_route(station_a, station_c, departure_time=450.0)

    assert route == [(station_a, conn_ab), (station_b, conn_bc_valid)]


def test_calculate_route_walk_connection_departs_immediately_without_waiting():
    graph = TransportGraph()
    origin = Station("A", "Station A", 0.0, 0.0)
    destination = Station("B", "Station B", 0.0, 0.005)
    graph.add_station(origin)
    graph.add_station(destination)

    # Walk connections have departure_time == 0.0
    conn_walk = Connection("walk", destination, VehicleType.WALK, 6.0, 0.5, 0.0)
    graph.add_connection(origin, conn_walk)

    simulator = RouteSimulator(graph, max_speed=1.0)
    # Query at t = 500.0; walk departs at 500.0 and arrives at 506.0
    route = simulator.calculate_route(origin, destination, departure_time=500.0)

    assert route == [(origin, conn_walk)]


def test_calculate_route_integrates_with_snap_to_network():
    graph = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    station_b = Station("B", "Station B", 0.0, 0.1)
    graph.add_station(station_a)
    graph.add_station(station_b)

    # BUS departs A at 500.0, arrives at B at 520.0
    conn_bus = Connection("line-1", station_b, VehicleType.BUS, 20.0, 10.0, 500.0)
    graph.add_connection(station_a, conn_bus)

    simulator = RouteSimulator(graph, max_speed=1.0)
    # Click near station A (lat=0.001, lon=0.0)
    with simulator.snap_to_network(0.001, 0.0, "origin") as origin_temp:
        route = simulator.calculate_route(origin_temp, station_b, departure_time=480.0)

        assert route is not None
        assert len(route) == 2
        assert route[0][0] == origin_temp
        assert route[0][1].vehicle_type is VehicleType.WALK
        assert route[0][1].destination == station_a
        assert route[1] == (station_a, conn_bus)


def test_calculate_route_faster_line_departing_later_is_chosen_over_slower_earlier_line():
    graph = TransportGraph()
    origin = Station("A", "Station A", 0.0, 0.0)
    destination = Station("B", "Station B", 0.0, 0.1)
    graph.add_station(origin)
    graph.add_station(destination)

    # Departs 480.0, duration 60.0 -> arrives 540.0
    conn_slow = Connection("slow", destination, VehicleType.BUS, 60.0, 10.0, 480.0)
    # Departs 490.0, duration 20.0 -> arrives 510.0 (faster arrival!)
    conn_fast = Connection("fast", destination, VehicleType.BUS, 20.0, 10.0, 490.0)
    graph.add_connection(origin, conn_slow)
    graph.add_connection(origin, conn_fast)

    simulator = RouteSimulator(graph, max_speed=1.0)
    route = simulator.calculate_route(origin, destination, departure_time=450.0)

    assert route == [(origin, conn_fast)]


def test_calculate_route_two_leg_faster_route_chosen_over_slower_direct_route():
    graph = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    station_b = Station("B", "Station B", 0.0, 0.1)
    station_c = Station("C", "Station C", 0.0, 0.2)
    for station in (station_a, station_b, station_c):
        graph.add_station(station)

    # Direct line A -> C departs 480.0, duration 120.0 -> arrives 600.0
    conn_direct = Connection("direct", station_c, VehicleType.BUS, 120.0, 20.0, 480.0)
    # Transfer route A -> B -> C:
    # A -> B departs 480.0, duration 30.0 -> arrives 510.0
    conn_ab = Connection("transfer-1", station_b, VehicleType.BUS, 30.0, 10.0, 480.0)
    # B -> C departs 520.0, duration 40.0 -> arrives 560.0 (earlier than 600.0!)
    conn_bc = Connection("transfer-2", station_c, VehicleType.SUBWAY, 40.0, 10.0, 520.0)
    graph.add_connection(station_a, conn_direct)
    graph.add_connection(station_a, conn_ab)
    graph.add_connection(station_b, conn_bc)

    simulator = RouteSimulator(graph, max_speed=1.0)
    route = simulator.calculate_route(station_a, station_c, departure_time=480.0)

    assert route == [(station_a, conn_ab), (station_b, conn_bc)]


def test_calculate_route_unreachable_destination_returns_none():
    graph = TransportGraph()
    station_a = Station("A", "Station A", 0.0, 0.0)
    station_b = Station("B", "Station B", 0.0, 0.1)
    isolated_c = Station("C", "Isolated C", 1.0, 1.0)
    for station in (station_a, station_b, isolated_c):
        graph.add_station(station)

    conn_ab = Connection("line-1", station_b, VehicleType.BUS, 15.0, 5.0, 480.0)
    graph.add_connection(station_a, conn_ab)

    simulator = RouteSimulator(graph, max_speed=1.0)
    assert simulator.calculate_route(station_a, isolated_c, departure_time=480.0) is None


def test_astar_finds_same_earliest_arrival_as_time_dependent_dijkstra():
    rng = random.Random(42)
    graph = TransportGraph()
    stations = [
        Station(
            f"station-{i}",
            f"Station {i}",
            -19.92 + rng.uniform(-0.05, 0.05),
            -43.94 + rng.uniform(-0.05, 0.05),
        )
        for i in range(30)
    ]
    for station in stations:
        graph.add_station(station)

    for i in range(300):
        origin = rng.choice(stations)
        destination = rng.choice(stations)
        if origin == destination:
            continue
        dist = haversine(
            origin.latitude, origin.longitude, destination.latitude, destination.longitude
        )
        dist = max(dist, 0.2)
        vehicle_type = rng.choice([VehicleType.BUS, VehicleType.SUBWAY, VehicleType.WALK])
        if vehicle_type is VehicleType.WALK:
            dep_time = 0.0
            travel_time = dist / (5.0 / 60.0)
        else:
            speed_km_min = rng.uniform(20.0, 60.0) / 60.0
            travel_time = dist / speed_km_min
            dep_time = rng.uniform(360.0, 1200.0)
        conn = Connection(f"route-{i}", destination, vehicle_type, travel_time, dist, dep_time)
        graph.add_connection(origin, conn)

    max_speed = RouteSimulator.max_speed_of(graph)
    astar_sim = RouteSimulator(graph, max_speed=max_speed)
    dijkstra_sim = RouteSimulator(graph, max_speed=float("inf"))

    for _ in range(50):
        origin = rng.choice(stations)
        destination = rng.choice(stations)
        dep_time = rng.uniform(360.0, 1100.0)

        astar_route = astar_sim.calculate_route(origin, destination, dep_time)
        dijkstra_route = dijkstra_sim.calculate_route(origin, destination, dep_time)

        if astar_route is None:
            assert dijkstra_route is None
            continue

        assert dijkstra_route is not None

        def get_arrival_and_validate(route, start_time):
            current_time = start_time
            for station, connection in route:
                if connection.vehicle_type is VehicleType.WALK:
                    current_time += connection.travel_time
                else:
                    assert connection.departure_time >= current_time - 1e-9
                    current_time = connection.departure_time + connection.travel_time
            return current_time

        astar_arrival = get_arrival_and_validate(astar_route, dep_time)
        dijkstra_arrival = get_arrival_and_validate(dijkstra_route, dep_time)

        assert astar_arrival == pytest.approx(dijkstra_arrival, abs=1e-5)




