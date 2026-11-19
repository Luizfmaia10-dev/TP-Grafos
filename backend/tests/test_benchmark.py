"""Correctness and measurement contracts for the offline benchmark."""
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

from app.domain import Connection, Station, VehicleType
from app.graph import TransportGraph
from app.route_simulator import RouteSimulator
from benchmarks.networkx_adapter import NetworkXAdapter
from benchmarks.run import compare_results, validate_path


def make_graph(edges):
    graph = TransportGraph()
    stations = {key: Station(key, key, 0, 0) for key in 'ABCD'}
    for station in stations.values():
        graph.add_station(station)
    for origin, destination, departure, duration in edges:
        graph.add_connection(stations[origin], Connection(
            'line', stations[destination], VehicleType.BUS, duration, 0, departure))
    return graph, stations


@pytest.mark.parametrize('edges,origin,destination,departure,arrival', [
    ([('A', 'B', 10, 5)], 'A', 'B', 8, 15),
    ([('A', 'B', 10, 5)], 'A', 'B', 10, 15),
    ([('A', 'B', 10, 5)], 'A', 'B', 11, None),
    ([('A', 'B', 10, 5), ('B', 'C', 16, 3)], 'A', 'C', 8, 19),
    ([('A', 'B', 10, 50), ('A', 'B', 12, 3)], 'A', 'B', 8, 15),
    ([('A', 'B', 10, 5), ('A', 'B', 10, 5)], 'A', 'B', 8, 15),
    ([('A', 'B', 1500.5, 0), ('B', 'C', 1500.5, 0)], 'A', 'C', 1500, 1500.5),
    ([], 'A', 'A', 8, 8),
    ([], 'A', 'D', 8, None),
    ([('A', 'B', 10, 0), ('B', 'A', 10, 0), ('B', 'C', 10, 2)], 'A', 'C', 10, 12),
])
def test_temporal_equivalence_and_cleanup(edges, origin, destination, departure, arrival):
    graph, stations = make_graph(edges)
    adapter = NetworkXAdapter(graph)
    counts = adapter.graph.number_of_nodes(), adapter.graph.number_of_edges()
    for _ in range(2):
        reference = adapter.calculate_route(stations[origin], stations[destination], departure)
        own = RouteSimulator(graph, RouteSimulator.max_speed_of(graph)).calculate_route(
            stations[origin], stations[destination], departure)
        for path in (reference, own):
            result = validate_path(stations[origin], stations[destination], departure, path)
            assert result['arrival'] == arrival
        assert counts == (adapter.graph.number_of_nodes(), adapter.graph.number_of_edges())


def test_random_temporal_graphs():
    rng = random.Random(42)
    for _ in range(15):
        edges = [(rng.choice('ABC'), rng.choice('ABCD'), rng.randrange(25), rng.randrange(6))
                 for _ in range(25)]
        graph, stations = make_graph(edges)
        adapter = NetworkXAdapter(graph)
        simulator = RouteSimulator(graph, RouteSimulator.max_speed_of(graph))
        for _ in range(10):
            a, b = (stations[rng.choice('ABCD')] for _ in range(2))
            departure = rng.randrange(20)
            left = validate_path(a, b, departure, simulator.calculate_route(a, b, departure))
            right = validate_path(a, b, departure, adapter.calculate_route(a, b, departure))
            compare_results(left, right)


def test_walk_is_rejected():
    graph, stations = make_graph([])
    graph.add_connection(stations['A'], Connection('walk', stations['B'], VehicleType.WALK, 1, 0, 0))
    with pytest.raises(ValueError, match='WALK'):
        NetworkXAdapter(graph)


def test_invalid_path_and_divergence():
    graph, stations = make_graph([('A', 'B', 10, 2)])
    with pytest.raises(ValueError, match='departure'):
        validate_path(stations['A'], stations['B'], 11,
                      [(stations['A'], graph.get_neighbors(stations['A'])[0])])
    with pytest.raises(ValueError, match='mismatch'):
        compare_results({'arrival': 10}, {'arrival': None})


@pytest.fixture
def small_feed(tmp_path):
    data = tmp_path / 'gtfs com espaços'
    data.mkdir()
    files = {
        'stops.txt': 'stop_id,stop_name,stop_lat,stop_lon\nA,A,0,0\nB,B,0,0.001\n',
        'routes.txt': 'route_id,route_type\nr,3\n',
        'trips.txt': 'route_id,service_id,trip_id\nr,s,t\n',
        'stop_times.txt': 'trip_id,arrival_time,departure_time,stop_id,stop_sequence\nt,08:00:00,08:00:00,A,1\nt,08:10:00,08:10:00,B,2\n',
        'calendar_dates.txt': 'service_id,date,exception_type\ns,20261119,1\n',
    }
    for name, content in files.items():
        (data / name).write_text(content)
    queries = tmp_path / 'queries.json'
    queries.write_text(json.dumps([
        {'id': 'direct', 'origin': 'A', 'destination': 'B', 'departure': '07:59:00'},
        {'id': 'missed', 'origin': 'A', 'destination': 'B', 'departure': '09:00:00'},
    ]))
    return data, queries, tmp_path / 'output'


def run_cli(data, queries, output, *extra):
    return subprocess.run([
        sys.executable, '-m', 'benchmarks.run', '--data-dir', str(data),
        '--service-date', '2026-11-19', '--queries', str(queries),
        '--output', str(output), '--repetitions', '2', '--warmups', '1', *extra,
    ], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)


def test_cli_end_to_end(small_feed):
    data, queries, output = small_feed
    process = run_cli(data, queries, output)
    assert process.returncode == 0, process.stderr
    report = json.loads((output / 'results.json').read_text())
    assert report['status'] == 'valid'
    assert report['schema_version'] == 2
    assert report['metadata']['memory_limit_kind'] == 'sampled_worker_rss'
    assert len(report['runs']) == 6  # two timed workers and four fresh memory workers
    assert len(report['summary']) == 4
    for run in report['runs']:
        if run['mode'] == 'memory':
            assert run['sampled_peak_rss_bytes'] > 0
            assert run['memory_sample_count'] > 0
        else:
            assert run['sampled_peak_rss_bytes'] is None
            assert run['memory_sample_count'] == 0
        assert run['load_ns'] >= 0
        assert run['connections'] == 1
    assert 'duration_ns' in (output / 'measurements.csv').read_text()
    assert report['metadata']['input_sha256']['stops.txt']


def test_cli_records_worker_failure(small_feed):
    data, queries, output = small_feed
    queries.write_text('[{"id":"bad","origin":"missing","destination":"B","departure":"08:00:00"}]')
    process = run_cli(data, queries, output)
    assert process.returncode != 0
    report = json.loads((output / 'results.json').read_text())
    assert report['status'] == 'incomplete'
    assert report['errors']
    assert report['summary'] == []


def test_query_nodes_are_cleaned_after_dijkstra_error(monkeypatch):
    import networkx as nx
    graph, stations = make_graph([('A', 'B', 10, 2)])
    adapter = NetworkXAdapter(graph)
    before = set(adapter.graph.nodes), set(adapter.graph.edges)
    def fail(*args, **kwargs):
        raise RuntimeError('search failed')
    monkeypatch.setattr(nx, 'single_source_dijkstra', fail)
    with pytest.raises(RuntimeError, match='search failed'):
        adapter.calculate_route(stations['A'], stations['B'], 8)
    assert before == (set(adapter.graph.nodes), set(adapter.graph.edges))


def test_cli_records_timeout(small_feed, monkeypatch):
    from benchmarks import run
    data, queries, output = small_feed
    def timeout_worker(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 1)
    monkeypatch.setattr(run, 'execute_process', timeout_worker)
    code = run.main(['--data-dir', str(data), '--service-date', '2026-11-19',
                     '--queries', str(queries), '--output', str(output)])
    assert code == 1
    report = json.loads((output / 'results.json').read_text())
    assert report['summary'] == []
    assert 'timed out' in report['errors'][0]['error']


def test_cli_records_rss_limit(small_feed):
    data, queries, output = small_feed
    process = run_cli(data, queries, output, '--memory-limit-mib', '1')
    assert process.returncode == 1
    report = json.loads((output / 'results.json').read_text())
    assert report['status'] == 'incomplete'
    assert report['summary'] == []
    assert 'RSS' in report['errors'][0]['error']


@pytest.mark.parametrize('option,value', [('--repetitions', '0'), ('--warmups', '-1')])
def test_cli_rejects_invalid_counts(small_feed, option, value):
    process = run_cli(*small_feed, option, value)
    assert process.returncode == 2


def test_equal_cost_alternative_paths():
    graph, stations = make_graph([
        ('A', 'B', 10, 2), ('A', 'C', 10, 2),
        ('B', 'D', 12, 3), ('C', 'D', 12, 3),
    ])
    adapter = NetworkXAdapter(graph)
    path = adapter.calculate_route(stations['A'], stations['D'], 8)
    assert validate_path(stations['A'], stations['D'], 8, path)['arrival'] == 15


def test_subsets_are_nested_and_keep_query_endpoints():
    from benchmarks.run import select_graph
    graph, stations = make_graph([('A', 'B', 10, 2), ('B', 'C', 12, 2)])
    queries = [{'origin': 'A', 'destination': 'B'}]
    small = select_graph(graph, queries, 2, 42)
    larger = select_graph(graph, queries, 3, 42)
    assert set(s.station_id for s in small.iter_stations()) == {'A', 'B'}
    assert set(small.iter_stations()) < set(larger.iter_stations())
    assert len(small.get_neighbors(stations['A'])) == 1
    assert small.get_neighbors(stations['B']) == []
    with pytest.raises(ValueError, match='endpoints'):
        select_graph(graph, queries, 1, 42)
