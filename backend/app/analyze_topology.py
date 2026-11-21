"""Generate a reproducible structural report for one GTFS service date."""

import argparse
import hashlib
import json
import os
import platform
import sys
import tempfile
from datetime import date
from pathlib import Path
from time import perf_counter

from app.data_loader import DataLoader
from app.graph_analyzer import GraphAnalyzer
from app.validate_gtfs import _get_process_peak_rss_mib


def analyze_dataset(data_directory: str | Path, *, service_date: date) -> dict:
    """Load a dated feed and separate deterministic results from process metrics."""
    data_directory = Path(data_directory)
    start = perf_counter()
    loader = DataLoader(data_directory, service_date=service_date)
    graph = loader.build_graph()
    load_seconds = perf_counter() - start

    start = perf_counter()
    analyzer = GraphAnalyzer(graph)
    scores = analyzer.criticality_scores()
    articulation_ids = sorted(station.station_id for station, score in scores.items() if score > 0)
    component_sizes = sorted(
        (len(component) for component in analyzer.find_strongly_connected_components()),
        reverse=True,
    )
    critical_stations = [
        {'rank': rank, 'station_id': station.station_id, 'name': station.name,
         'score': scores[station]}
        for rank, station in enumerate(analyzer.get_critical_stations(20), start=1)
    ]
    graph_counts = {
        'real_stations': len(scores),
        'connections': sum(len(graph.get_neighbors(station)) for station in graph.iter_stations()),
    }
    analysis_seconds = perf_counter() - start

    source_files = set(loader.report.files)
    source_files.update(name for name in ('calendar.txt', 'calendar_dates.txt')
                        if (data_directory / name).is_file())
    hashes = {}
    for name in sorted(source_files):
        with (data_directory / name).open('rb') as source:
            hashes[name] = hashlib.file_digest(source, 'sha256').hexdigest()

    return {
        'metadata': {
            'service_date': service_date.isoformat(),
            'active_service_ids': loader.report.active_service_ids,
            'python': platform.python_version(),
            'platform': platform.platform(),
            'source_sha256': hashes,
            'loaded_trips': loader.report.loaded_trips,
            'rejected_trips': len(loader.report.rejected_trips),
            'rejected_records': dict(sorted(loader.report.reasons.items())),
        },
        'graph': graph_counts,
        'articulation_points': {'count': len(articulation_ids), 'station_ids': articulation_ids},
        'strongly_connected_components': {'count': len(component_sizes), 'sizes': component_sizes},
        'critical_stations': critical_stations,
        'metrics': {
            'load_seconds': round(load_seconds, 6),
            'analysis_seconds': round(analysis_seconds, 6),
            'process_peak_rss_mib': round(_get_process_peak_rss_mib(), 3),
        },
        'limitations': [
            'Structural analysis uses accepted connections for the selected service date; '
            'departure times, travel times and temporal journey feasibility are ignored.',
            'Articulation points use a simple undirected projection: parallel edges '
            'are deduplicated and self-loops are ignored. Temporary vertices are excluded.',
            'Strongly connected components use directed connections and iterative Tarjan.',
            'Criticality is max(0, components(G-v) - components(G)) in the undirected projection; '
            'positive scores are ranked by descending score, descending simple degree, '
            'then ascending station ID. At most 20 stations are reported.',
            'All accepted stops are included, including isolated stops without active trips. '
            'DataLoader sanitization and trip quarantine affect the resulting topology.',
            'Scores do not measure demand, passenger impact, geographic isolation or '
            'the resilience of other service dates.',
            'Load and analysis timings exclude source hashing and JSON serialization. '
            'RSS is the process lifetime peak, not incremental graph memory; '
            'zero indicates an unavailable RSS measurement.',
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Analyze topology for a GTFS service date.')
    parser.add_argument('data_directory', type=Path)
    parser.add_argument('--date', dest='service_date', type=date.fromisoformat, required=True,
                        help='service date in YYYY-MM-DD format')
    parser.add_argument('--output', type=Path, help='UTF-8 JSON destination (default: stdout)')
    arguments = parser.parse_args()
    print('Loading GTFS and analyzing topology...', file=sys.stderr)
    try:
        result = analyze_dataset(arguments.data_directory, service_date=arguments.service_date)
        serialized = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if arguments.output is not None:
            resolved_output = arguments.output.resolve()
            for filename in result['metadata']['source_sha256']:
                source = arguments.data_directory / filename
                if resolved_output == source.resolve() or (
                    arguments.output.exists() and arguments.output.samefile(source)
                ):
                    raise ValueError(f'--output identifies GTFS input: {source}')
            descriptor, name = tempfile.mkstemp(dir=arguments.output.parent,
                                               prefix=f'.{arguments.output.name}.', suffix='.tmp')
            temporary = Path(name)
            try:
                os.close(descriptor)
                temporary.write_text(serialized, encoding='utf-8')
                temporary.replace(arguments.output)
            finally:
                temporary.unlink(missing_ok=True)
            print(f'Report saved to {arguments.output}', file=sys.stderr)
        else:
            sys.stdout.reconfigure(encoding='utf-8')
            print(serialized, end='')
    except (OSError, ValueError) as error:
        print(f'Topology analysis failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
