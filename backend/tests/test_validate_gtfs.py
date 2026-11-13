"""Exercise the manual validation command using a complete tiny GTFS feed."""

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def feed(tmp_path):
    tables = {
        'stops': [('stop_id', 'stop_name', 'stop_lat', 'stop_lon'),
                  ('A', 'Central', '-19.9167', '-43.9345'),
                  ('B', 'Terminal', '-19.9100', '-43.9400')],
        'routes': [('route_id', 'route_type'), ('r', '3')],
        'trips': [('route_id', 'service_id', 'trip_id'), ('r', 'weekday', 't')],
        'stop_times': [('trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'),
                       ('t', '08:00:00', '08:00:00', 'A', '1'),
                       ('t', '08:10:00', '08:10:00', 'B', '2')],
    }
    for name, rows in tables.items():
        with (tmp_path / (name + '.txt')).open('w', encoding='utf-8', newline='') as source:
            csv.writer(source).writerows(rows)
    return tmp_path


def test_validates_graph_and_measures_load(feed):
    from app.validate_gtfs import validate_dataset

    result = validate_dataset(feed)
    assert result['passed'] is True
    assert all(result['checks'].values())
    assert result['graph']['stations'] == 2
    assert result['graph']['connections'] == 1
    assert result['load_report']['loaded_trips'] == 1
    assert result['metrics']['load_seconds'] >= 0
    assert result['metrics']['validation_seconds'] >= 0
    assert result['metrics']['process_peak_rss_mib'] > 0
    json.dumps(result)


def test_cli_writes_json_report(feed):
    destination = feed / 'result.json'
    completed = subprocess.run(
        [sys.executable, '-m', 'app.validate_gtfs', str(feed), '--output', str(destination)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(destination.read_text())
    assert result['passed'] is True
    assert result['graph']['connections'] == 1
    assert 'Carregando' in completed.stderr


def test_audit_comparison_detects_changed_snapshot(feed):
    from app.validate_gtfs import validate_dataset

    audit = {}
    for name in ('stops', 'routes', 'trips', 'stop_times'):
        path = feed / (name + '.txt')
        audit[name] = {'rows': 2 if name in ('stops', 'stop_times') else 1,
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    audit['additional_checks'] = {'zero_time_affected_trips': 0}
    audit_path = feed / 'audit.json'
    audit_path.write_text(json.dumps(audit), encoding='utf-8')
    assert validate_dataset(feed, audit_path)['passed'] is True
    path = feed / 'stops.txt'
    path.write_text(path.read_text().replace('Central', 'Central changed'), encoding='utf-8')
    result = validate_dataset(feed, audit_path)
    assert result['passed'] is False
    assert result['audit']['files']['stops.txt']['hash_matches'] is False


def test_graph_validation_detects_unsorted_or_invalid_connections():
    from app.domain import Connection, Station, VehicleType
    from app.graph import TransportGraph
    from app.validate_gtfs import validate_graph

    graph = TransportGraph()
    a = Station('A', 'Central', 0, 0)
    b = Station('B', 'Terminal', 0, 1)
    graph.add_station(a)
    graph.add_station(b)
    graph.add_connection(a, Connection('r', b, VehicleType.BUS, 10, 1, 480))
    graph.add_connection(a, Connection('r', b, VehicleType.BUS, 10, 1, 490))
    first, second = graph.get_neighbors(a)
    first.departure_time = 500
    second.travel_time = float('nan')
    result = validate_graph(graph)
    assert result['sorted_departures'] is False
    assert result['valid_weights'] is False
