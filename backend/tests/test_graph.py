import pytest

from app.domain import Connection, Station, VehicleType
from app.graph import TransportGraph


def test_added_station_has_no_neighbors():
    transport_graph = TransportGraph()
    station = Station("stop-1", "Central", -19.9167, -43.9345)

    transport_graph.add_station(station)

    assert transport_graph.get_neighbors(station) == []


def test_connection_is_added_only_to_origin_neighbors():
    transport_graph = TransportGraph()
    origin = Station("stop-1", "Central", -19.9167, -43.9345)
    destination = Station("stop-2", "Lagoinha", -19.9100, -43.9400)
    connection = Connection(
        route_id="route-1",
        destination=destination,
        vehicle_type=VehicleType.BUS,
        travel_time=12.0,
        distance=3.2,
        departure_time=480.0,
    )
    transport_graph.add_station(origin)
    transport_graph.add_station(destination)

    transport_graph.add_connection(origin, connection)

    assert transport_graph.get_neighbors(origin) == [connection]
    assert transport_graph.get_neighbors(destination) == []


def test_connection_to_unknown_destination_is_rejected():
    transport_graph = TransportGraph()
    origin = Station("stop-1", "Central", -19.9167, -43.9345)
    unknown_destination = Station("stop-2", "Lagoinha", -19.9100, -43.9400)
    connection = Connection(
        route_id="route-1",
        destination=unknown_destination,
        vehicle_type=VehicleType.BUS,
        travel_time=12.0,
        distance=3.2,
        departure_time=480.0,
    )
    transport_graph.add_station(origin)

    with pytest.raises(KeyError):
        transport_graph.add_connection(origin, connection)

    assert transport_graph.get_neighbors(origin) == []


def test_connection_from_unknown_origin_is_rejected():
    transport_graph = TransportGraph()
    unknown_origin = Station("stop-1", "Central", -19.9167, -43.9345)
    destination = Station("stop-2", "Lagoinha", -19.9100, -43.9400)
    connection = Connection(
        route_id="route-1",
        destination=destination,
        vehicle_type=VehicleType.BUS,
        travel_time=12.0,
        distance=3.2,
        departure_time=480.0,
    )
    transport_graph.add_station(destination)

    with pytest.raises(KeyError):
        transport_graph.add_connection(unknown_origin, connection)

    assert transport_graph.get_neighbors(destination) == []


def test_adding_existing_station_does_not_erase_its_connections():
    transport_graph = TransportGraph()
    origin = Station("stop-1", "Central", -19.9167, -43.9345)
    same_origin = Station("stop-1", "Central updated", -19.9170, -43.9350)
    destination = Station("stop-2", "Lagoinha", -19.9100, -43.9400)
    connection = Connection(
        "route-1", destination, VehicleType.BUS, 12.0, 3.2, 480.0
    )
    transport_graph.add_station(origin)
    transport_graph.add_station(destination)
    transport_graph.add_connection(origin, connection)

    transport_graph.add_station(same_origin)

    assert transport_graph.get_neighbors(origin) == [connection]
