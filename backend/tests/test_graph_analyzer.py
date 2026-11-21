import pytest

from app.domain import Connection, Station, TemporaryVertex, VehicleType
from app.graph import TransportGraph
from app.graph_analyzer import GraphAnalyzer


def build_graph(station_ids, edges):
    graph = TransportGraph()
    stations = {
        station_id: Station(station_id, station_id, 0.0, 0.0)
        for station_id in station_ids
    }
    for station in stations.values():
        graph.add_station(station)
    for origin, destination in edges:
        graph.add_connection(
            stations[origin],
            Connection("route", stations[destination], VehicleType.BUS, 1.0, 1.0, 0.0),
        )
    return graph, stations


@pytest.mark.parametrize(
    "station_ids, edges, expected_scores, expected_components",
    [
        ("", [], {}, []),
        ("A", [], {"A": 0}, [{"A"}]),
        (
            "ABCD",
            [("A", "B"), ("B", "C"), ("C", "D")],
            {"A": 0, "B": 1, "C": 1, "D": 0},
            [{"A"}, {"B"}, {"C"}, {"D"}],
        ),
        (
            "ABC",
            [("A", "B"), ("B", "C"), ("C", "A")],
            {"A": 0, "B": 0, "C": 0},
            [{"A", "B", "C"}],
        ),
        (
            "ABCDEFG",
            [("A", "B"), ("B", "C"), ("D", "E"), ("E", "F"), ("F", "D")],
            {"A": 0, "B": 1, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0},
            [{"A"}, {"B"}, {"C"}, {"D", "E", "F"}, {"G"}],
        ),
        (
            "ABCDEF",
            [
                ("A", "B"), ("B", "A"), ("B", "C"),
                ("C", "D"), ("D", "C"), ("D", "E"), ("E", "E"),
            ],
            {"A": 0, "B": 1, "C": 1, "D": 1, "E": 0, "F": 0},
            [{"A", "B"}, {"C", "D"}, {"E"}, {"F"}],
        ),
        (
            "ABC",
            [
                ("A", "B"), ("A", "B"), ("B", "A"),
                ("B", "C"), ("B", "C"), ("C", "B"), ("B", "B"),
            ],
            {"A": 0, "B": 1, "C": 0},
            [{"A", "B", "C"}],
        ),
        (
            "ABCD",
            [("A", "B"), ("A", "C"), ("A", "D")],
            {"A": 2, "B": 0, "C": 0, "D": 0},
            [{"A"}, {"B"}, {"C"}, {"D"}],
        ),
        (
            "ABCDE",
            [("A", "B"), ("B", "C"), ("C", "D"), ("D", "B"), ("B", "E")],
            {"A": 0, "B": 2, "C": 0, "D": 0, "E": 0},
            [{"A"}, {"B", "C", "D"}, {"E"}],
        ),
        (
            "ABC",
            [("A", "B"), ("B", "A"), ("A", "C"), ("C", "B")],
            {"A": 0, "B": 0, "C": 0},
            [{"A", "B", "C"}],
        ),
        (
            "ABC",
            [("B", "A"), ("C", "B")],
            {"A": 0, "B": 1, "C": 0},
            [{"A"}, {"B"}, {"C"}],
        ),
    ],
    ids=[
        "empty", "isolated", "chain", "cycle", "disconnected", "multiple-sccs",
        "parallel-and-self-edges", "dfs-root", "nonroot-branches", "active-cross-edge",
        "edge-to-finished-component",
    ],
)
def test_topology(station_ids, edges, expected_scores, expected_components):
    graph, stations = build_graph(station_ids, edges)
    analyzer = GraphAnalyzer(graph)

    assert analyzer.criticality_scores() == {
        stations[station_id]: score for station_id, score in expected_scores.items()
    }
    assert analyzer.find_articulation_points() == {
        stations[station_id] for station_id, score in expected_scores.items() if score > 0
    }
    assert {
        frozenset(station.station_id for station in component)
        for component in analyzer.find_strongly_connected_components()
    } == {frozenset(component) for component in expected_components}


def test_temporary_vertices_and_their_edges_are_excluded_without_mutating_graph():
    graph, stations = build_graph("ABC", [("A", "B"), ("B", "C")])
    temporary = TemporaryVertex("temporary", "Temporary", 0.0, 0.0, "origin")
    graph.add_station(temporary)
    for origin, destination in [
        (stations["C"], temporary), (temporary, stations["A"]),
        (temporary, stations["B"]),
    ]:
        graph.add_connection(
            origin, Connection("walk", destination, VehicleType.WALK, 1.0, 1.0, 0.0)
        )
    analyzer = GraphAnalyzer(graph)

    assert analyzer.find_articulation_points() == {stations["B"]}
    assert analyzer.criticality_scores() == {
        stations["A"]: 0, stations["B"]: 1, stations["C"]: 0,
    }
    assert analyzer.get_critical_stations(10) == [stations["B"]]
    assert {frozenset(component) for component in analyzer.find_strongly_connected_components()} == {
        frozenset({stations["A"]}), frozenset({stations["B"]}),
        frozenset({stations["C"]}),
    }
    assert list(graph.iter_stations()) == [*stations.values(), temporary]
    assert len(graph.get_neighbors(temporary)) == 2
    assert graph.get_neighbors(stations["C"])[0].destination is temporary


def test_graph_with_only_temporary_vertices_has_no_analyzed_stations():
    graph = TransportGraph()
    graph.add_station(TemporaryVertex("temporary", "Temporary", 0.0, 0.0, "origin"))
    analyzer = GraphAnalyzer(graph)

    assert analyzer.find_articulation_points() == set()
    assert analyzer.find_strongly_connected_components() == []
    assert analyzer.criticality_scores() == {}
    assert analyzer.get_critical_stations(10) == []


def test_critical_stations_are_ranked_by_score_simple_degree_then_id():
    station_ids = ["Z", "B", "C", "A"]
    edges = []
    for hub, leaf_count in [("Z", 4), ("B", 4), ("C", 4), ("A", 3)]:
        leaves = [f"{hub}{index}" for index in range(leaf_count)]
        station_ids.extend(leaves)
        edges.extend((hub, leaf) for leaf in leaves)
        if hub in {"B", "C"}:
            edges.append((leaves[2], leaves[3]))
    edges.extend([("A", "A0")] * 10 + [("A", "A")])
    graph, stations = build_graph(station_ids, edges)
    analyzer = GraphAnalyzer(graph)

    assert analyzer.get_critical_stations(3) == [stations["Z"], stations["B"], stations["C"]]
    assert analyzer.get_critical_stations(100) == [
        stations["Z"], stations["B"], stations["C"], stations["A"],
    ]


def test_zero_top_n_returns_no_stations():
    graph, _ = build_graph("ABC", [("A", "B"), ("B", "C")])

    assert GraphAnalyzer(graph).get_critical_stations(0) == []


def test_negative_top_n_is_rejected():
    with pytest.raises(ValueError):
        GraphAnalyzer(TransportGraph()).get_critical_stations(-1)


def test_long_chain_is_analyzed_without_recursion():
    station_ids = [str(index) for index in range(2000)]
    graph, stations = build_graph(station_ids, zip(station_ids, station_ids[1:]))
    analyzer = GraphAnalyzer(graph)

    assert analyzer.find_articulation_points() == {
        stations[station_id] for station_id in station_ids[1:-1]
    }
    components = analyzer.find_strongly_connected_components()
    assert len(components) == 2000
    assert all(len(component) == 1 for component in components)
    assert set().union(*components) == set(stations.values())
