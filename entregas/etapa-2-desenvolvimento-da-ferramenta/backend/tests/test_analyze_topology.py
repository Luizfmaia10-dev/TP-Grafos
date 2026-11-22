"""Verify topology reports and the executable CLI on a dated synthetic feed."""

import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest


def write_table(directory, name, rows):
    with (directory / name).open('w', encoding='utf-8', newline='') as source:
        csv.writer(source).writerows(rows)


@pytest.fixture
def feed(tmp_path):
    tables = {
        'stops.txt': [
            ('stop_id', 'stop_name', 'stop_lat', 'stop_lon'),
            *[(station, 'Estação ' + station, '-19.91', '-43.94')
              for station in ('Z', 'F', 'E', 'D', 'C', 'B', 'A')],
        ],
        'routes.txt': [('route_id', 'route_type'), ('r', '3')],
        'trips.txt': [('route_id', 'service_id', 'trip_id'),
                      ('r', 'weekday', 'chain'), ('r', 'weekday', 'reverse'),
                      ('r', 'weekday', 'branch'), ('r', 'weekend', 'inactive')],
        'stop_times.txt': [
            ('trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'),
            *[('chain', f'08:{index * 10:02}:00', f'08:{index * 10:02}:00', station, index + 1)
              for index, station in enumerate('ABCDE')],
            ('reverse', '09:00:00', '09:00:00', 'C', 1),
            ('reverse', '09:10:00', '09:10:00', 'B', 2),
            ('branch', '09:00:00', '09:00:00', 'C', 1),
            ('branch', '09:10:00', '09:10:00', 'F', 2),
            ('inactive', '10:00:00', '10:00:00', 'E', 1),
            ('inactive', '10:10:00', '10:10:00', 'A', 2),
        ],
        'calendar.txt': [
            ('service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
             'saturday', 'sunday', 'start_date', 'end_date'),
            ('weekday', 1, 1, 1, 1, 1, 0, 0, '20260101', '20261231'),
            ('weekend', 0, 0, 0, 0, 0, 1, 1, '20260101', '20261231'),
        ],
        'calendar_dates.txt': [('service_id', 'date', 'exception_type')],
    }
    for name, rows in tables.items():
        write_table(tmp_path, name, rows)
    return tmp_path


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, '-m', 'app.analyze_topology', *map(str, arguments)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True,
        encoding='utf-8', timeout=20,
    )


def test_analysis_reports_dated_structure_and_criticality(feed):
    from app.analyze_topology import analyze_dataset

    result = analyze_dataset(feed, service_date=date(2026, 11, 17))

    assert result['graph'] == {'real_stations': 7, 'connections': 6}
    assert result['articulation_points'] == {'count': 3, 'station_ids': ['B', 'C', 'D']}
    assert result['strongly_connected_components'] == {'count': 6, 'sizes': [2, 1, 1, 1, 1, 1]}
    assert result['critical_stations'] == [
        {'rank': 1, 'station_id': 'C', 'name': 'Estação C', 'score': 2},
        {'rank': 2, 'station_id': 'B', 'name': 'Estação B', 'score': 1},
        {'rank': 3, 'station_id': 'D', 'name': 'Estação D', 'score': 1},
    ]
    assert result['metadata']['service_date'] == '2026-11-17'
    assert result['metadata']['active_service_ids'] == ['weekday']
    assert result['metadata']['python'] == platform.python_version()
    assert result['metadata']['platform'] == platform.platform()
    assert result['metadata']['source_sha256'] == {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in feed.glob('*.txt')
    }
    assert result['metrics']['load_seconds'] >= 0
    assert result['metrics']['analysis_seconds'] >= 0
    assert result['metrics']['process_peak_rss_mib'] > 0
    assert result['limitations']
    assert json.loads(json.dumps(result)) == result


def test_structural_results_are_deterministic(feed):
    from app.analyze_topology import analyze_dataset

    first = analyze_dataset(feed, service_date=date(2026, 11, 17))
    second = analyze_dataset(feed, service_date=date(2026, 11, 17))
    first.pop('metrics')
    second.pop('metrics')
    assert first == second


def test_analysis_limits_ranking_to_twenty_positive_scores(feed):
    from app.analyze_topology import analyze_dataset

    write_table(feed, 'stops.txt', [
        ('stop_id', 'stop_name', 'stop_lat', 'stop_lon'),
        *[(f'S{index:02}', str(index), 0, 0) for index in range(25)],
    ])
    write_table(feed, 'trips.txt', [
        ('route_id', 'service_id', 'trip_id'), ('r', 'weekday', 'chain'),
    ])
    write_table(feed, 'stop_times.txt', [
        ('trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'),
        *[('chain', f'08:{index:02}:00', f'08:{index:02}:00', f'S{index:02}', index + 1)
          for index in range(25)],
    ])
    result = analyze_dataset(feed, service_date=date(2026, 11, 17))
    assert result['articulation_points']['count'] == 23
    assert [item['station_id'] for item in result['critical_stations']] == [
        f'S{index:02}' for index in range(1, 21)
    ]
    assert [item['rank'] for item in result['critical_stations']] == list(range(1, 21))


def test_cli_writes_utf8_json_to_file(feed):
    destination = feed / 'topology.json'
    completed = run_cli(feed, '--date', '2026-11-17', '--output', destination)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ''
    serialized = destination.read_text(encoding='utf-8')
    assert 'Estação C' in serialized
    assert json.loads(serialized)['graph'] == {'real_stations': 7, 'connections': 6}


def test_main_writes_report_and_returns_success(feed, monkeypatch, capsys):
    from app.analyze_topology import main

    destination = feed / 'topology.json'
    monkeypatch.setattr(sys, 'argv', [
        'analyze_topology', str(feed), '--date', '2026-11-17', '--output', str(destination),
    ])

    assert main() == 0
    assert json.loads(destination.read_text(encoding='utf-8'))['graph'] == {
        'real_stations': 7,
        'connections': 6,
    }
    assert f'Report saved to {destination}' in capsys.readouterr().err


def test_cli_stdout_is_only_utf8_json(feed):
    completed = run_cli(feed, '--date', '2026-11-17')
    assert completed.returncode == 0, completed.stderr
    assert 'Estação C' in completed.stdout
    assert json.loads(completed.stdout)['articulation_points']['count'] == 3


@pytest.mark.parametrize('arguments', [
    [], ['--date', '2026-02-30'], ['--date', 'invalid'],
    ['--date', '2026-11-17', '--unknown'],
])
def test_cli_rejects_missing_date_or_invalid_arguments(feed, arguments):
    completed = run_cli(feed, *arguments)
    assert completed.returncode == 2
    assert completed.stdout == ''
    assert 'usage:' in completed.stderr


@pytest.mark.parametrize('broken_file', ['stops.txt', 'calendar.txt'])
def test_cli_reports_malformed_input_without_writing_report(feed, broken_file):
    (feed / broken_file).write_text('wrong,header\n', encoding='utf-8')
    destination = feed / 'topology.json'
    completed = run_cli(feed, '--date', '2026-11-17', '--output', destination)
    assert completed.returncode == 1
    assert completed.stdout == ''
    assert broken_file in completed.stderr
    assert 'Traceback' not in completed.stderr
    assert not destination.exists()


def test_cli_reports_missing_feed(feed):
    completed = run_cli(feed / 'missing', '--date', '2026-11-17')
    assert completed.returncode == 1
    assert completed.stdout == ''
    assert 'stops.txt' in completed.stderr
    assert 'Traceback' not in completed.stderr


def test_cli_reports_output_failure(feed):
    completed = run_cli(feed, '--date', '2026-11-17', '--output', feed)
    assert completed.returncode == 1
    assert completed.stdout == ''
    assert feed.name in completed.stderr
    assert 'Traceback' not in completed.stderr


def test_no_active_service_reports_isolated_stations(feed):
    from app.analyze_topology import analyze_dataset

    result = analyze_dataset(feed, service_date=date(2027, 1, 1))
    assert result['graph'] == {'real_stations': 7, 'connections': 0}
    assert result['critical_stations'] == []
    assert result['articulation_points'] == {'count': 0, 'station_ids': []}
    assert result['strongly_connected_components'] == {'count': 7, 'sizes': [1] * 7}


@pytest.mark.parametrize('failure', ['write', 'replace'])
def test_cli_preserves_previous_report_and_cleans_temporary_on_failure(feed, monkeypatch, failure):
    from app.analyze_topology import main

    destination = feed / 'topology.json'
    previous = b'{"previous": true}\n'
    destination.write_bytes(previous)
    previous_files = set(feed.iterdir())
    original_write = Path.write_text

    def partial_write(path, contents, **kwargs):
        original_write(path, contents[:20], **kwargs)
        raise OSError('simulated disk full after partial write')

    def failed_replace(path, target):
        raise OSError('simulated replacement failure')

    if failure == 'write':
        monkeypatch.setattr(Path, 'write_text', partial_write)
    else:
        monkeypatch.setattr(Path, 'replace', failed_replace)
    monkeypatch.setattr(sys, 'argv', [
        'analyze_topology', str(feed), '--date', '2026-11-17', '--output', str(destination),
    ])

    assert main() == 1
    assert destination.read_bytes() == previous
    assert set(feed.iterdir()) == previous_files


@pytest.mark.parametrize('filename', [
    'stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt', 'calendar.txt', 'calendar_dates.txt',
])
@pytest.mark.parametrize('spelling', ['direct', 'equivalent', 'hardlink'])
def test_cli_rejects_output_identifying_used_gtfs_input(feed, filename, spelling):
    original_sources = {path: path.read_bytes() for path in feed.glob('*.txt')}
    destination = feed / filename
    if spelling == 'equivalent':
        (feed / 'subdirectory').mkdir()
        destination = feed / 'subdirectory' / '..' / filename
    elif spelling == 'hardlink':
        destination = feed / 'linked-input.txt'
        destination.hardlink_to(feed / filename)
    original_files = set(feed.iterdir())

    completed = run_cli(feed, '--date', '2026-11-17', '--output', destination)

    assert completed.returncode == 1
    assert completed.stdout == ''
    assert 'GTFS input' in completed.stderr
    assert all(path.read_bytes() == contents for path, contents in original_sources.items())
    assert set(feed.iterdir()) == original_files
