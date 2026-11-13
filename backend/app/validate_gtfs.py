"""Validate a loaded GTFS graph and report process-level resource measurements."""

import argparse
import hashlib
import json
import platform
import resource
import sys
from math import isfinite
from pathlib import Path
from time import perf_counter

from app.data_loader import DataLoader
from app.graph import TransportGraph


def validate_graph(graph: TransportGraph) -> dict:
    """Inspect every edge without constructing a second copy of the graph."""
    stations = set(graph.iter_stations())
    connection_count = 0
    unused_origins = 0
    sorted_departures = known_destinations = valid_weights = True
    for station in stations:
        neighbors = graph.get_neighbors(station)
        unused_origins += not neighbors
        previous_departure = -float('inf')
        for connection in neighbors:
            connection_count += 1
            if connection.departure_time < previous_departure:
                sorted_departures = False
            previous_departure = connection.departure_time
            if connection.destination not in stations:
                known_destinations = False
            if not all(isfinite(value) and value >= 0 for value in (
                connection.departure_time, connection.travel_time, connection.distance
            )):
                valid_weights = False
            if connection.travel_time == 0 and connection.destination != station:
                valid_weights = False
    return {
        'stations': len(stations),
        'connections': connection_count,
        'stations_without_outgoing_connections': unused_origins,
        'sorted_departures': sorted_departures,
        'known_destinations': known_destinations,
        'valid_weights': valid_weights,
    }


def validate_dataset(data_directory: str | Path, audit_path: str | Path | None = None) -> dict:
    """Load a feed, verify graph invariants, and optionally compare its audit."""
    data_directory = Path(data_directory)
    start = perf_counter()
    loader = DataLoader(data_directory)
    graph = loader.build_graph()
    load_seconds = perf_counter() - start
    start = perf_counter()
    graph_result = validate_graph(graph)
    report = loader.report.to_dict()
    checks = {
        'balanced_record_counts': all(
            stats['read'] == stats['accepted'] + stats['rejected']
            for stats in report['files'].values()
        ),
        'station_count_matches': graph_result['stations'] == report['files']['stops.txt']['accepted'],
        'connection_count_matches': graph_result['connections'] == report['connections'],
        'trip_edge_count_matches': report['connections'] == (
            report['files']['stop_times.txt']['accepted'] - report['loaded_trips']
        ),
        **{key: graph_result[key] for key in (
            'sorted_departures', 'known_destinations', 'valid_weights'
        )},
    }
    audit_result = None
    hashes = {}
    for name in report['files']:
        with (data_directory / name).open('rb') as source:
            hashes[name] = hashlib.file_digest(source, 'sha256').hexdigest()
    if audit_path is not None:
        audit = json.loads(Path(audit_path).read_text(encoding='utf-8'))
        comparisons = {}
        for name, stats in report['files'].items():
            original = audit[Path(name).stem]
            expected_rows = original.get('rows', original.get('counts', {}).get('rows'))
            comparisons[name] = {
                'hash_matches': hashes[name] == original['sha256'],
                'row_count_matches': stats['read'] == expected_rows,
            }
        quarantine_count = sum(
            reason == 'zero_travel_time' for reason in report['rejected_trips'].values()
        )
        expected_quarantine = audit['additional_checks']['zero_time_affected_trips']
        audit_result = {
            'files': comparisons,
            'zero_time_quarantine_matches': quarantine_count == expected_quarantine,
            'expected_zero_time_trips': expected_quarantine,
            'actual_zero_time_trips': quarantine_count,
        }
        checks['audit_matches'] = (
            all(all(values.values()) for values in comparisons.values())
            and audit_result['zero_time_quarantine_matches']
        )
    validation_seconds = perf_counter() - start
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_mib = peak_rss / (1024 * 1024 if sys.platform == 'darwin' else 1024)
    return {
        'passed': all(checks.values()),
        'checks': checks,
        'graph': graph_result,
        'metrics': {
            'load_seconds': round(load_seconds, 3),
            'validation_seconds': round(validation_seconds, 3),
            'process_peak_rss_mib': round(peak_rss_mib, 3),
            'python': platform.python_version(),
            'platform': platform.platform(),
        },
        'source_sha256': hashes,
        'load_report': report,
        'audit': audit_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Carrega e valida os arquivos GTFS.')
    parser.add_argument('data_directory', type=Path)
    parser.add_argument('--audit', type=Path, help='JSON da auditoria para comparação')
    parser.add_argument('--output', type=Path, help='Arquivo JSON para salvar o resultado')
    arguments = parser.parse_args()
    print('Carregando GTFS; aguarde a carga e a verificação de todas as conexões...', file=sys.stderr)
    result = validate_dataset(arguments.data_directory, arguments.audit)
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if arguments.output:
        arguments.output.write_text(serialized, encoding='utf-8')
        print(f'Relatório salvo em {arguments.output}', file=sys.stderr)
    else:
        print(serialized, end='')
    print('Validação aprovada.' if result['passed'] else 'Validação reprovada.', file=sys.stderr)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
