from dataclasses import FrozenInstanceError

import pytest

from app.domain import Connection, Station, VehicleType


def test_station_stores_identifier_name_and_coordinates():
    station = Station("stop-1", "Central", -19.9167, -43.9345)

    assert station.station_id == "stop-1"
    assert station.name == "Central"
    assert station.latitude == -19.9167
    assert station.longitude == -43.9345


def test_station_identity_depends_only_on_identifier():
    station = Station("stop-1", "Central", -19.9167, -43.9345)
    updated_station = Station("stop-1", "Central Station", -19.917, -43.935)
    other_station = Station("stop-2", "Central", -19.9167, -43.9345)

    assert station == updated_station
    assert hash(station) == hash(updated_station)
    assert station != other_station
    assert station != "stop-1"
    assert {station: "connections"}[updated_station] == "connections"
    assert len({station, updated_station, other_station}) == 2


def test_station_identity_cannot_change_after_use_as_dictionary_key():
    station = Station("stop-1", "Central", -19.9167, -43.9345)

    with pytest.raises(FrozenInstanceError):
        station.station_id = "stop-2"


@pytest.mark.parametrize("vehicle_type", list(VehicleType))
def test_connection_stores_destination_mode_and_trip_details(vehicle_type):
    destination = Station("stop-2", "Lagoinha", -19.910, -43.940)
    connection = Connection(
        route_id="route-1",
        destination=destination,
        vehicle_type=vehicle_type,
        travel_time=12.5,
        distance=3.2,
        departure_time=25 * 60 + 15,
    )

    assert connection.route_id == "route-1"
    assert connection.destination is destination
    assert connection.vehicle_type is vehicle_type
    assert connection.travel_time == 12.5
    assert connection.distance == 3.2
    assert connection.departure_time == 1515


def test_vehicle_type_contains_the_supported_modes():
    assert {mode.name for mode in VehicleType} == {"BUS", "SUBWAY", "WALK"}


def test_station_and_connection_use_slots_without_instance_dict():
    station = Station("stop-1", "Central", -19.9167, -43.9345)
    connection = Connection(
        route_id="route-1",
        destination=station,
        vehicle_type=VehicleType.BUS,
        travel_time=10.0,
        distance=2.5,
        departure_time=480.0,
    )

    assert hasattr(Station, "__slots__")
    assert hasattr(Connection, "__slots__")
    assert not hasattr(station, "__dict__")
    assert not hasattr(connection, "__dict__")

    with pytest.raises((AttributeError, TypeError)):
        station.extra_attribute = "not allowed"

    with pytest.raises((AttributeError, TypeError)):
        connection.extra_attribute = "not allowed"
