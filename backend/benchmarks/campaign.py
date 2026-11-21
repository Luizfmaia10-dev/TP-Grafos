"""Run the prescribed nested-size benchmark matrix, retaining every size report."""
import argparse
from pathlib import Path

from benchmarks import run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--service-date', required=True)
    parser.add_argument('--queries', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--timeout', type=run.positive, default=600)
    parser.add_argument('--memory-limit-mib', type=run.positive, default=4096)
    args = parser.parse_args(argv)
    report = {'status': 'incomplete', 'sizes': []}
    run.save_json(args.output / 'campaign.json', report)
    for limit in (100, 1000, None):
        name = str(limit) if limit is not None else 'full'
        command = ['--data-dir', args.data_dir, '--service-date', args.service_date,
                   '--queries', args.queries, '--output', str(args.output / name),
                   '--repetitions', '7', '--warmups', '2', '--seed', '42',
                   '--timeout', str(args.timeout), '--memory-limit-mib', str(args.memory_limit_mib)]
        if limit is not None:
            command.extend(['--station-limit', str(limit)])
        code = run.main(command)
        report['sizes'].append({'station_limit': limit, 'directory': name,
                                'status': 'valid' if code == 0 else 'incomplete'})
        run.save_json(args.output / 'campaign.json', report)
    if all(size['status'] == 'valid' for size in report['sizes']):
        report['status'] = 'valid'
    run.save_json(args.output / 'campaign.json', report)
    return 0 if report['status'] == 'valid' else 1


if __name__ == '__main__':
    raise SystemExit(main())
