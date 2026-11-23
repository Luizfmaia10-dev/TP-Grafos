"""Domain itinerary costs, instructions and serialization."""

import json

import pytest
from app.domain import Connection, Station, VehicleType
from app.itinerary import Itinerary


def stations():
    return [Station(str(i), name, 0, i / 100) for i, name in enumerate(
        ("Origem", "Estação Central", "Destino")
    )]


def test_transfer_totals_and_instructions():
    a, b, c = stations()
    path = [
        (a, Connection(
            "internal-bus", b, VehicleType.BUS, 5.5, 2, 480.5,
            route_short_name="10",
        )),
        (b, Connection(
            "internal-metro", c, VehicleType.SUBWAY, 4.25, 3, 487.5,
            route_short_name="M1",
        )),
    ]
    itinerary = Itinerary(a, 480, path)
    assert itinerary.total_seconds == 705
    assert itinerary.waiting_seconds == 120
    assert itinerary.travel_seconds == 585
    assert itinerary.distance_km == 5
    assert itinerary.arrival_time == "08:11:45"
    assert itinerary.destination == c
    assert len(itinerary.instructions) == 4
    assert "Aguarde" in itinerary.instructions[0]
    assert "ônibus" in itinerary.instructions[1]
    assert "10" in itinerary.instructions[1]
    assert "Estação Central" in itinerary.instructions[1]
    assert "metrô" in itinerary.instructions[3]
    assert not hasattr(itinerary, "__dict__")
    assert not hasattr(itinerary.steps[0], "__dict__")


def test_public_route_name_replaces_internal_gtfs_id_in_instructions():
    a, b, _ = stations()
    connection = Connection(
        "561865", b, VehicleType.BUS, 5, 2, 480, route_short_name="510"
    )

    itinerary = Itinerary(a, 480, [(a, connection)])

    assert itinerary.steps[0].route_id == "561865"
    assert itinerary.steps[0].route_short_name == "510"
    assert "ônibus 510" in itinerary.instructions[0]
    assert "561865" not in itinerary.instructions[0]


def test_missing_public_route_name_does_not_expose_internal_gtfs_id():
    a, b, _ = stations()
    connection = Connection("561865", b, VehicleType.BUS, 5, 2, 480)

    itinerary = Itinerary(a, 480, [(a, connection)])

    assert itinerary.steps[0].route_short_name == "Linha não informada"
    assert "ônibus Linha não informada" in itinerary.instructions[0]
    assert "561865" not in itinerary.instructions[0]


def test_walk_departs_immediately_and_preserves_service_day():
    a, b, c = stations()
    itinerary = Itinerary(a, 1440.25, [
        (a, Connection("walk", b, VehicleType.WALK, .5, .04, 0)),
        (b, Connection("10", c, VehicleType.BUS, 1, .5, 1441)),
    ])
    assert itinerary.arrival_time == "24:02:00"
    assert itinerary.waiting_seconds == 15
    assert itinerary.total_seconds == 105
    assert itinerary.steps[0].departure_time == "24:00:15"
    assert itinerary.instructions[0] == (
        "Caminhe de Origem até Estação Central às 24:00:15; chegada às 24:00:45."
    )


def test_empty_path_stays_at_origin():
    a, _, _ = stations()
    itinerary = Itinerary(a, 480, [])
    assert itinerary.destination == a
    assert itinerary.arrival_time == "08:00:00"
    assert itinerary.total_seconds == itinerary.waiting_seconds == itinerary.travel_seconds == 0
    assert itinerary.distance_km == 0
    assert itinerary.steps == ()
    assert itinerary.instructions == ()


def test_rounding_absolute_timestamps_keeps_durations_additive():
    a, b, _ = stations()
    itinerary = Itinerary(a, .4 / 60, [
        (a, Connection("10", b, VehicleType.BUS, .2 / 60, 1, .6 / 60)),
    ])
    assert itinerary.total_seconds == 1
    assert itinerary.waiting_seconds == 1
    assert itinerary.travel_seconds == 0


def test_same_second_transfer_has_no_extra_wait_instruction():
    a, b, c = stations()
    itinerary = Itinerary(a, 416 + 42 / 60, [
        (a, Connection("10", b, VehicleType.BUS, 5 / 60, 1, 416 + 42 / 60)),
        (b, Connection("M1", c, VehicleType.SUBWAY, 1, 1, 416 + 47 / 60)),
    ])
    assert itinerary.steps[1].waiting_seconds == 0
    assert len(itinerary.instructions) == 2


@pytest.mark.parametrize("disconnected", [False, True])
def test_rejects_invalid_path(disconnected):
    a, b, _ = stations()
    path = [(b if disconnected else a, Connection("10", b, VehicleType.BUS, 1, 1, 479))]
    with pytest.raises(ValueError):
        Itinerary(a, 480, path)


def test_serialization_is_json_compatible_and_independent():
    a, b, _ = stations()
    itinerary = Itinerary(a, 480, [(a, Connection("10", b, VehicleType.BUS, 5, 2, 480))])
    result = itinerary.to_dict()
    assert json.loads(itinerary.to_json()) == result
    assert result["origin"]["station_id"] == a.station_id
    assert result["destination"]["name"] == b.name
    assert result["steps"][0]["vehicle_type"] == "BUS"
    assert result["instructions"] == list(itinerary.instructions)
    assert "Estação Central" in itinerary.to_json()
    result["steps"][0]["distance_km"] = 99
    assert itinerary.to_dict()["steps"][0]["distance_km"] == 2


def test_itinerary_snapshots_connections_without_changing_router_output():
    a, b, _ = stations()
    connection = Connection("10", b, VehicleType.BUS, 5, 2, 480)
    path = [(a, connection)]
    itinerary = Itinerary(a, 480, path)
    connection.distance = 99
    path.clear()
    assert itinerary.distance_km == 2
    assert itinerary.to_dict()["steps"][0]["distance_km"] == 2
