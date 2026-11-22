"""Select distinct scheduled queries deterministically from the actual feed."""
import argparse
from datetime import date
import json
from pathlib import Path
import random

from app.data_loader import DataLoader
from app.route_simulator import RouteSimulator, haversine
from benchmarks.run import digest, validate_path

GTFS_FILES = ('stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt',
              'calendar.txt', 'calendar_dates.txt')


def select_queries(graph, seed=42, max_candidates=10000):
    """Keep one reachable pair per fixed distance band/time and two unreachable pairs."""
    stations = sorted(graph.iter_stations(), key=lambda station: station.station_id)
    rng = random.Random(seed)
    engine = RouteSimulator(graph, RouteSimulator.max_speed_of(graph))
    selected, seen = {}, set()
    missing = {(band, departure) for band in ('short', 'medium', 'long')
               for departure in ('07:00:00', '14:00:00')}
    unreachable = []
    attempts = 0
    while len(seen) < min(max_candidates, len(stations) * (len(stations) - 1)):
        origin, destination = rng.sample(stations, 2)
        pair = origin.station_id, destination.station_id
        if pair in seen:
            continue
        seen.add(pair)
        attempts += 1
        distance = haversine(origin.latitude, origin.longitude,
                             destination.latitude, destination.longitude)
        band = 'short' if distance < 2 else 'medium' if distance < 8 else 'long'
        for departure, minutes in (('07:00:00', 420), ('14:00:00', 840)):
            if (band, departure) not in missing and len(unreachable) == 2:
                continue
            path = engine.calculate_route(origin, destination, minutes)
            answer = validate_path(origin, destination, minutes, path)
            entry = {'origin': pair[0], 'destination': pair[1], 'departure': departure,
                     'distance_km': distance, 'distance_band': band,
                     'expected_arrival': answer['arrival'], 'candidate_index': attempts}
            if answer['arrival'] is not None and (band, departure) in missing:
                entry['id'] = f'{band}-{departure[:2]}'
                selected[(band, departure)] = entry
                missing.remove((band, departure))
                break
            if answer['arrival'] is None and len(unreachable) < 2:
                entry['id'] = f'no-route-{len(unreachable) + 1}'
                unreachable.append(entry)
                break
        if not missing and len(unreachable) == 2:
            return [selected[key] for key in sorted(selected)] + unreachable
    raise ValueError(f'Insufficient reachable/unreachable strata after {attempts} distinct pairs; '
                     f'missing={sorted(missing)}, no_route={len(unreachable)}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--service-date', required=True, type=date.fromisoformat)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--check', action='store_true', help='Regenerate and compare without writing')
    args = parser.parse_args(argv)
    for name in GTFS_FILES:
        path = args.data_dir / name
        if path.exists():
            with path.open('rb') as stream:
                if stream.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError(f'{path} is an LFS pointer; run git lfs pull')
    loader = DataLoader(args.data_dir, service_date=args.service_date)
    graph = loader.build_graph()
    manifest = {'schema_version': 1, 'selection': {
        'seed': 42, 'max_candidates': 10000,
        'method': 'distinct_ordered_pairs_sampled_from_sorted_station_ids',
        'short_km': '[0, 2)', 'medium_km': '[2, 8)', 'long_km': '[8, infinity)',
        'service_date': args.service_date.isoformat(),
        'stations': sum(1 for _ in graph.iter_stations()),
        'active_service_ids': loader.report.active_service_ids,
        'input_sha256': {name: digest(args.data_dir / name)
                         for name in GTFS_FILES if (args.data_dir / name).exists()},
        'reachability_engine': 'native_astar_full_graph',
        'limitation': 'Selection is descriptive, not a representative statistical sample; '
                      'NetworkX equivalence is checked separately by the campaign.',
    }, 'queries': select_queries(graph)}
    if args.check:
        if manifest != json.loads(args.output.read_text(encoding='utf-8')):
            raise ValueError('Manifest differs from deterministic regeneration')
        print(f'Validated: {args.output}')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        print(f'Generated: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
