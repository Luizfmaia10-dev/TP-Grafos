from app.domain import Station
from app.graph import TransportGraph


def test_added_station_has_no_neighbors():
    transport_graph = TransportGraph()
    station = Station("stop-1", "Central", -19.9167, -43.9345)

    transport_graph.add_station(station)

    assert transport_graph.get_neighbors(station) == []
