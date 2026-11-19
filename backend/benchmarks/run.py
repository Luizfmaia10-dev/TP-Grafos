"""Run reproducible scheduled-routing benchmarks in isolated processes."""
import argparse
import csv
import gc
import hashlib
import json
import math
import random
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from datetime import date, datetime, timezone
from time import perf_counter_ns

import psutil

from app.data_loader import DataLoader
from app.graph import TransportGraph
from app.route_simulator import RouteSimulator
from app.time_utils import TimeUtils
from benchmarks.metrics import SAMPLE_INTERVAL_SECONDS, execute_process, memory

TOLERANCE_MINUTES = 1e-7


def validate_path(origin, destination, departure, path):
    """Validate continuity and schedule feasibility without rounding timestamps."""
    if path is None:
        return {'arrival': None, 'legs': None, 'path': None}
    current, time = origin, departure
    description = []
    for station, connection in path:
        if station != current:
            raise ValueError('Noncontiguous path')
        if connection.departure_time < time or connection.travel_time < 0:
            raise ValueError('Invalid departure or travel duration')
        time = connection.departure_time + connection.travel_time
        current = connection.destination
        description.append([station.station_id, current.station_id,
                            connection.route_id, connection.departure_time, time])
    if current != destination:
        raise ValueError('Path does not reach destination')
    return {'arrival': time, 'legs': len(path), 'path': description}


def compare_results(left, right):
    """Equal arrival times allow different optimal paths."""
    a, b = left['arrival'], right['arrival']
    if (a is None) != (b is None) or (
        a is not None and not math.isclose(a, b, rel_tol=0, abs_tol=TOLERANCE_MINUTES)
    ):
        raise ValueError(f'Arrival mismatch: {left!r} versus {right!r}')


def load_queries(path):
    queries = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(queries, list) or not queries:
        raise ValueError('Queries must be a nonempty JSON list')
    ids = set()
    for query in queries:
        if not isinstance(query['id'], str) or query['id'] in ids:
            raise ValueError('Query IDs must be unique strings')
        ids.add(query['id'])
        for key in ('origin', 'destination'):
            if not isinstance(query[key], str):
                raise ValueError(f'{key} must be a station ID string')
        query['departure_minutes'] = TimeUtils.time_to_minutes(query['departure'])
    return queries


def select_graph(graph, queries, limit, seed):
    """Build nested induced subsets while retaining all query endpoints."""
    if limit is None:
        return graph
    stations = {s.station_id: s for s in graph.iter_stations()}
    required = {q[key] for q in queries for key in ('origin', 'destination')}
    if len(required) > limit:
        raise ValueError('Station limit must include all query endpoints')
    remaining = sorted(stations.keys() - required)
    random.Random(seed).shuffle(remaining)
    selected = required | set(remaining[:max(0, limit - len(required))])
    subset = TransportGraph()
    for key in sorted(selected):
        subset.add_station(stations[key])
    for station in subset.iter_stations():
        for connection in graph.get_neighbors(station):
            if connection.destination.station_id in selected:
                subset.add_connection(station, connection)
    return subset


def worker(config):
    """Load one independent network; stdout is a machine-readable result only."""
    # Subset selection always uses the entire manifest, including in memory jobs.
    queries = config['queries']
    baseline = memory()
    start = perf_counter_ns()
    loader = DataLoader(config['data_dir'], service_date=date.fromisoformat(config['service_date']))
    graph = loader.build_graph()
    loaded = perf_counter_ns()
    loaded_memory = memory()
    stations = {station.station_id: station for station in graph.iter_stations()}
    for query in queries:
        for key in ('origin', 'destination'):
            if query[key] not in stations:
                raise ValueError(f"Unknown {key} station: {query[key]}")
    select_start = perf_counter_ns()
    graph = select_graph(graph, config['all_queries'], config['station_limit'], config['seed'])
    selection_ns = perf_counter_ns() - select_start
    stations = {station.station_id: station for station in graph.iter_stations()}
    result = {
        'engine': config['engine'], 'mode': config['mode'],
        'load_ns': loaded - start, 'selection_ns': selection_ns, 'stations': len(stations),
        'connections': sum(len(graph.get_neighbors(s)) for s in graph.iter_stations()),
        'active_service_ids': loader.report.active_service_ids,
        'baseline': baseline, 'after_load': loaded_memory,
        'after_selection': memory(), 'samples': [],
    }
    del loader
    gc.collect()
    result['before_prepare'] = memory()
    start = perf_counter_ns()
    if config['engine'] == 'native_astar':
        engine = RouteSimulator(graph, RouteSimulator.max_speed_of(graph))
    else:
        # Keep third-party imports out of the native worker's baseline and graph engine.
        from benchmarks.networkx_adapter import NetworkXAdapter
        engine = NetworkXAdapter(graph)
        result['expanded_nodes'] = engine.graph.number_of_nodes()
        result['expanded_edges'] = engine.graph.number_of_edges()
    result['prepare_ns'] = perf_counter_ns() - start
    result['after_prepare'] = memory()
    del graph
    gc.collect()
    result['prepared_memory'] = memory()
    repeats = 1 if config['mode'] == 'memory' else config['repetitions']
    warmups = 0 if config['mode'] == 'memory' else config['warmups']
    for query in queries:
        origin, destination = stations[query['origin']], stations[query['destination']]
        for iteration in range(-warmups, repeats):
            start = perf_counter_ns()
            path = engine.calculate_route(origin, destination, query['departure_minutes'])
            elapsed = perf_counter_ns() - start
            timings = (dict(engine.last_timings) if config['engine'] == 'networkx_dijkstra'
                       else {'query_prepare_ns': 0, 'search_ns': elapsed,
                             'cleanup_ns': 0, 'query_total_ns': elapsed})
            # Validation, memory snapshots and output are outside the search timer.
            snapshot = memory()
            answer = validate_path(origin, destination, query['departure_minutes'], path)
            if iteration >= 0:
                result['samples'].append({
                    'case': query['id'], 'repetition': iteration, **timings,
                    **answer, **snapshot,
                })
            del path
    result.update(memory())
    return result


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def git_output(*args):
    process = subprocess.run(['git', *args], capture_output=True, text=True,
                             cwd=Path(__file__).resolve().parents[2])
    return process.stdout.strip() if process.returncode == 0 else None


def metadata(args):
    from importlib.metadata import version
    names = ('stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt',
             'calendar.txt', 'calendar_dates.txt')
    data = Path(args.data_dir)
    for name in names:
        path = data / name
        if path.exists():
            with path.open('rb') as stream:
                if stream.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError(f'{path} is an LFS pointer; run git lfs pull')
    return {
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'networkx': version('networkx'), 'psutil': version('psutil'),
        'platform': platform.platform(), 'cpu': platform.processor() or platform.machine(),
        'logical_cpu_count': psutil.cpu_count(),
        'memory_info': dict(psutil.virtual_memory()._asdict()),
        'memory_method': 'psutil_rss_snapshots_and_external_sampling',
        'sample_interval_seconds': SAMPLE_INTERVAL_SECONDS,
        'memory_limit_kind': 'sampled_worker_rss',
        'commit': git_output('rev-parse', 'HEAD'),
        'dirty': bool(git_output('status', '--porcelain')),
        'input_sha256': {name: digest(data / name) for name in names if (data / name).exists()},
        'queries_sha256': digest(Path(args.queries)),
        'service_date': args.service_date, 'data_dir': str(data.resolve()),
        'repetitions': args.repetitions, 'warmups': args.warmups,
        'timeout_seconds': args.timeout, 'memory_limit_mib': args.memory_limit_mib,
        'station_limit': args.station_limit, 'seed': args.seed,
        'tolerance_minutes': TOLERANCE_MINUTES,
    }


def summarize(runs):
    groups = {}
    for run in runs:
        if run['mode'] != 'timing':
            continue
        for sample in run['samples']:
            for phase in ('query_total', 'search'):
                groups.setdefault((run['engine'], sample['case'], phase), []).append(
                    sample[f'{phase}_ns'])
    summary = []
    for (engine, case, phase), values in groups.items():
        quartiles = statistics.quantiles(values, n=4, method='inclusive') if len(values) > 1 else [values[0]] * 3
        summary.append({'engine': engine, 'case': case, 'phase': phase,
                        'count': len(values), 'median_ns': statistics.median(values),
                        'min_ns': min(values), 'max_ns': max(values),
                        'iqr_ns': quartiles[2] - quartiles[0]})
    return summary


def export(output, report):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'results.json').write_text(
        json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    with (output / 'measurements.csv').open('w', newline='', encoding='utf-8') as stream:
        fields = ['engine', 'mode', 'case', 'repetition', 'phase', 'duration_ns',
                  'rss_bytes', 'sampled_peak_rss_bytes', 'arrival', 'legs']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for run in report['runs']:
            base = {'engine': run['engine'], 'mode': run['mode'],
                    'sampled_peak_rss_bytes': run['sampled_peak_rss_bytes']}
            for phase, snapshot in (('load', run['after_load']), ('selection', run['after_selection']),
                                    ('prepare', run['after_prepare'])):
                writer.writerow({**base, 'phase': phase, 'duration_ns': run[f'{phase}_ns'], **snapshot})
            for sample in run['samples']:
                for phase in ('query_prepare', 'search', 'cleanup', 'query_total'):
                    writer.writerow({**base, 'case': sample['case'],
                                     'repetition': sample['repetition'], 'phase': phase,
                                     'duration_ns': sample[f'{phase}_ns'],
                                     **{key: sample[key] for key in ('rss_bytes', 'arrival', 'legs')}})


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--service-date', required=True, type=date.fromisoformat)
    parser.add_argument('--queries', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--repetitions', type=positive, default=5)
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--timeout', type=positive, default=600)
    parser.add_argument('--memory-limit-mib', type=positive,
                        help='Terminate workers whose sampled RSS exceeds this limit (not a hard cap)')
    parser.add_argument('--station-limit', type=positive)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args(argv)
    if args.warmups < 0:
        parser.error('warmups must be nonnegative')
    args.service_date = args.service_date.isoformat()
    report = {'schema_version': 2, 'status': 'incomplete', 'runs': [], 'errors': [], 'summary': []}
    try:
        queries = load_queries(args.queries)
        report['queries'] = queries
        report['metadata'] = metadata(args)
        config = vars(args).copy()
        config['all_queries'] = queries
        config['data_dir'] = str(Path(args.data_dir).resolve())
        jobs = [(engine, mode, cases)
                for engine in ('native_astar', 'networkx_dijkstra')
                for mode, cases in [('timing', queries), *[('memory', [q]) for q in queries]]]
        for engine, mode, cases in jobs:
            job = {**config, 'engine': engine, 'mode': mode, 'queries': cases}
            try:
                process, peak, count = execute_process(
                    [sys.executable, '-m', 'benchmarks.run', '--worker'],
                    input=json.dumps(job), sample_memory=mode == 'memory',
                    cwd=Path(__file__).resolve().parents[1], timeout=args.timeout,
                    memory_limit_bytes=(args.memory_limit_mib * 1024 * 1024
                                        if args.memory_limit_mib is not None else None),
                )
                if process.returncode:
                    raise RuntimeError(f'worker exit {process.returncode}: {process.stderr[-4000:]}')
                result = json.loads(process.stdout)
                result.update(sampled_peak_rss_bytes=peak, memory_sample_count=count)
                report['runs'].append(result)
            except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError, psutil.Error) as error:
                report['errors'].append({'engine': engine, 'mode': mode,
                                         'cases': [q['id'] for q in cases], 'error': str(error)})
                break
        if not report['errors']:
            expected = {}
            for run in report['runs']:
                for sample in run['samples']:
                    key = sample['case']
                    if key in expected:
                        compare_results(expected[key], sample)
                    else:
                        expected[key] = sample
            report['status'] = 'valid'
            report['summary'] = summarize(report['runs'])
    except (ValueError, KeyError, OSError) as error:
        report['errors'].append({'error': str(error)})
    export(Path(args.output), report)
    print(f"{report['status']}: {Path(args.output) / 'results.json'}")
    return 0 if report['status'] == 'valid' else 1


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']:
        config = json.load(sys.stdin)
        print(json.dumps(worker(config), allow_nan=False))
    else:
        raise SystemExit(main())
