"""Selection and campaign contracts using small scheduled graphs."""
import ast
import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest

from app.domain import Connection, Station, VehicleType
from app.graph import TransportGraph
from app.route_simulator import haversine
from benchmarks import run
from tests.test_benchmark import small_feed


def selection_graph():
    graph = TransportGraph()
    stations = [Station(str(i), str(i), 0, i * .01) for i in range(12)]
    for station in stations:
        graph.add_station(station)
    # All forward pairs can be reached at both requested times; reverse pairs cannot.
    for origin in stations:
        for destination in stations[int(origin.station_id) + 1:]:
            distance = haversine(0, origin.longitude, 0, destination.longitude)
            for departure in (421, 841):
                graph.add_connection(origin, Connection(
                    'r', destination, VehicleType.BUS, distance, distance, departure))
    return graph


def test_selection_stratifies_distinct_pairs_and_records_actual_reachability():
    from benchmarks.queries import select_queries
    graph = selection_graph()
    queries = select_queries(graph, seed=42)
    assert queries == select_queries(graph, seed=42)
    assert len(queries) == 8
    assert len({(q['origin'], q['destination']) for q in queries}) == 8
    reachable = [q for q in queries if q['expected_arrival'] is not None]
    assert {(q['distance_band'], q['departure']) for q in reachable} == {
        (band, departure) for band in ('short', 'medium', 'long')
        for departure in ('07:00:00', '14:00:00')}
    assert len(reachable) == 6
    assert all(int(q['origin']) < int(q['destination']) for q in reachable)
    assert all(int(q['origin']) > int(q['destination'])
               for q in queries if q['expected_arrival'] is None)
    for query in queries:
        if query['expected_arrival'] is not None:
            departure = 421 if query['departure'] == '07:00:00' else 841
            assert query['expected_arrival'] == pytest.approx(departure + query['distance_km'])


def test_selection_fails_explicitly_when_required_strata_do_not_exist():
    from benchmarks.queries import select_queries
    graph = TransportGraph()
    graph.add_station(Station('only', 'only', 0, 0))
    with pytest.raises(ValueError, match='strata'):
        select_queries(graph, seed=42)


def test_load_queries_accepts_manifest_with_selection_provenance(tmp_path):
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps({'selection': {'seed': 42}, 'queries': [
        {'id': 'one', 'origin': 'A', 'destination': 'B', 'departure': '07:00:00',
         'expected_arrival': None}]}), encoding='utf-8')
    queries = run.load_queries(path)
    assert queries[0]['departure_minutes'] == 420
    assert queries[0]['expected_arrival'] is None


def test_production_modules_do_not_import_networkx():
    for path in (Path(__file__).resolve().parents[1] / 'app').rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.Import):
                assert all(alias.name.split('.')[0] != 'networkx' for alias in node.names), path
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or '').split('.')[0] != 'networkx', path


def campaign_cli(data, queries, output, *extra):
    return subprocess.run([
        sys.executable, '-m', 'benchmarks.campaign', '--data-dir', str(data),
        '--service-date', '2026-11-19', '--queries', str(queries),
        '--output', str(output), *extra,
    ], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)


def test_campaign_runs_all_sizes_with_prescribed_defaults(small_feed):
    from benchmarks.queries import GTFS_FILES
    data, queries, output = small_feed
    selection = {'service_date': '2026-11-19', 'seed': 42,
                 'input_sha256': {name: run.digest(data / name)
                                  for name in GTFS_FILES if (data / name).exists()}}
    queries.write_text(json.dumps({'selection': selection, 'queries': json.loads(queries.read_text())}))
    process = campaign_cli(data, queries, output)
    assert process.returncode == 0, process.stderr
    campaign = json.loads((output / 'campaign.json').read_text())
    assert campaign['status'] == 'valid'
    assert [item['station_limit'] for item in campaign['sizes']] == [100, 1000, None]
    for size in ('100', '1000', 'full'):
        report = json.loads((output / size / 'results.json').read_text())
        assert report['metadata']['repetitions'] == 7
        assert report['metadata']['warmups'] == 2
        assert report['metadata']['memory_limit_mib'] == 4096
        assert report['metadata']['timeout_seconds'] == 600
        assert report['metadata']['seed'] == 42
        assert report['selection'] == selection
        assert report['equivalence']['status'] == 'verified'
        assert report['equivalence']['cases'] == ['direct', 'missed']
        for engine in ('native_astar', 'networkx_dijkstra'):
            timing = next(r for r in report['runs'] if r['mode'] == 'timing' and r['engine'] == engine)
            assert len(timing['samples']) == 14
        assert (output / size / 'measurements.csv').exists()


def test_campaign_preserves_memory_failures_and_continues_all_sizes(small_feed):
    data, queries, output = small_feed
    process = campaign_cli(data, queries, output, '--memory-limit-mib', '1')
    assert process.returncode == 1
    campaign = json.loads((output / 'campaign.json').read_text())
    assert campaign['status'] == 'incomplete'
    assert len(campaign['sizes']) == 3
    for item in campaign['sizes']:
        report = json.loads((output / item['directory'] / 'results.json').read_text())
        assert report['status'] == 'incomplete'
        assert report['metadata']['station_limit'] == item['station_limit']
        assert report['errors'][0]['cause'] == 'memory_limit'
        assert report['errors'][0]['sampled_peak_rss_bytes'] > 0
        assert report['errors'][0]['memory_sample_count'] > 0
        assert report['equivalence']['status'] == 'incomplete'


def test_timeout_exports_samples_completed_before_interruption(small_feed):
    from tests.test_benchmark import run_cli
    data, queries, output = small_feed
    process = run_cli(data, queries, output, '--timeout', '2', '--repetitions', '100000')
    assert process.returncode == 1
    report = json.loads((output / 'results.json').read_text())
    assert report['errors'][0]['cause'] == 'timeout'
    partial = report['runs'][0]
    assert partial['status'] == 'incomplete'
    assert 0 < len(partial['samples']) < 100000
    assert partial['stage'] == 'queries'
    assert 'direct' in (output / 'measurements.csv').read_text()
    assert report['summary'] == []


def test_equivalence_requires_both_engines_and_rejects_mismatched_arrival():
    from benchmarks.run import verify_equivalence
    queries = [{'id': 'one'}]
    runs = [{'engine': 'native_astar', 'samples': [{'case': 'one', 'arrival': None}]}]
    assert verify_equivalence(runs, queries)['status'] == 'incomplete'
    runs.append({'engine': 'networkx_dijkstra', 'samples': [{'case': 'one', 'arrival': 10}]})
    with pytest.raises(ValueError, match='mismatch'):
        verify_equivalence(runs, queries)


def test_failed_rerun_does_not_reuse_a_previous_worker_checkpoint(small_feed, monkeypatch):
    data, queries, output = small_feed
    stale = output / 'checkpoints' / 'worker-000.json'
    stale.parent.mkdir(parents=True)
    stale.write_text(json.dumps({'engine': 'native_astar', 'mode': 'timing',
                                'samples': [{'case': 'stale', 'arrival': 123, 'legs': 1,
                                             'rss_bytes': 10, 'repetition': 0,
                                             'query_prepare_ns': 0, 'search_ns': 1,
                                             'cleanup_ns': 0, 'query_total_ns': 1}]}))
    def fail_before_start(*args, **kwargs):
        raise RuntimeError('could not start worker')
    monkeypatch.setattr(run, 'execute_process', fail_before_start)
    assert run.main(['--data-dir', str(data), '--service-date', '2026-11-19',
                     '--queries', str(queries), '--output', str(output)]) == 1
    report = json.loads((output / 'results.json').read_text())
    assert report['runs'] == []


def test_campaign_continues_to_larger_sizes_after_timeout(small_feed, monkeypatch):
    from benchmarks import campaign
    data, queries, output = small_feed
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('worker', 600)
    monkeypatch.setattr(run, 'execute_process', timeout)
    assert campaign.main(['--data-dir', str(data), '--service-date', '2026-11-19',
                          '--queries', str(queries), '--output', str(output)]) == 1
    for size in ('100', '1000', 'full'):
        report = json.loads((output / size / 'results.json').read_text())
        assert report['status'] == 'incomplete'
        assert report['errors'][0]['cause'] == 'timeout'


def test_export_writes_summary_csv_with_median_and_iqr(tmp_path):
    summary = {'engine': 'native_astar', 'case': 'one', 'phase': 'query_total',
               'count': 2, 'median_ns': 15.0, 'min_ns': 10, 'max_ns': 20, 'iqr_ns': 5.0}
    run.export(tmp_path, {'runs': [], 'summary': [summary]})
    assert (tmp_path / 'summary.csv').exists()
    with (tmp_path / 'summary.csv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [{'engine': 'native_astar', 'case': 'one', 'phase': 'query_total',
                     'count': '2', 'median_ns': '15.0', 'min_ns': '10', 'max_ns': '20',
                     'iqr_ns': '5.0'}]


def test_late_worker_divergence_invalidates_previous_verified_equivalence(small_feed, monkeypatch):
    data, queries, output = small_feed
    execute = run.execute_process
    def corrupted_worker(command, **kwargs):
        process, peak, count = execute(command, **kwargs)
        job = json.loads(kwargs['input'])
        if job['engine'] == 'networkx_dijkstra' and job['mode'] == 'memory':
            result = json.loads(process.stdout)
            result['samples'][0]['arrival'] += 1
            process.stdout = json.dumps(result)
        return process, peak, count
    monkeypatch.setattr(run, 'execute_process', corrupted_worker)
    assert run.main(['--data-dir', str(data), '--service-date', '2026-11-19',
                     '--queries', str(queries), '--output', str(output)]) == 1
    report = json.loads((output / 'results.json').read_text())
    assert report['status'] == 'incomplete'
    assert report['equivalence']['status'] == 'failed'
    assert report['summary'] == []
    assert 'mismatch' in report['errors'][0]['error']


@pytest.mark.parametrize('field', ['service_date', 'seed', 'input_sha256'])
def test_campaign_rejects_manifest_provenance_mismatch(small_feed, monkeypatch, field):
    from benchmarks.queries import GTFS_FILES
    data, queries, output = small_feed
    selection = {'service_date': '2026-11-19', 'seed': 42,
                 'input_sha256': {name: run.digest(data / name)
                                  for name in GTFS_FILES if (data / name).exists()}}
    selection[field] = {'service_date': '2026-11-18', 'seed': 43,
                        'input_sha256': {'stops.txt': 'outdated'}}[field]
    queries.write_text(json.dumps({'selection': selection, 'queries': json.loads(queries.read_text())}))
    def should_not_start(*args, **kwargs):
        raise AssertionError('Workers must not start with mismatched provenance')
    monkeypatch.setattr(run, 'execute_process', should_not_start)
    assert run.main(['--data-dir', str(data), '--service-date', '2026-11-19',
                     '--queries', str(queries), '--output', str(output)]) == 1
    report = json.loads((output / 'results.json').read_text())
    assert report['status'] == 'incomplete'
    assert report['runs'] == []
    assert field in report['errors'][0]['error']
