"""Summarize saved runs/scores without another model call."""
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean

def summarize(rows):
    values, latencies = {}, []
    for row in rows:
        if row.get('status') == 'ok' and row.get('timings', {}).get('total_seconds') is not None:
            latencies.append(row['timings']['total_seconds'])
        for metric, record in row.get('metrics', {}).items():
            value = record.get('value')
            if isinstance(value, (int, float)) and math.isfinite(value):
                values.setdefault(metric, []).append(value)
    report = dict(rows=len(rows), statuses=dict(Counter(r.get('status', 'unknown') for r in rows)),
                  metrics={k: dict(mean=mean(v), valid_rows=len(v)) for k, v in values.items()})
    if latencies:
        ordered = sorted(latencies)
        report['latency_seconds'] = dict(mean=mean(ordered),
            p50=ordered[max(0, math.ceil(len(ordered)*.5)-1)],
            p95=ordered[max(0, math.ceil(len(ordered)*.95)-1)], valid_rows=len(ordered),
            percentile_method='nearest-rank; successful generations only')
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.input).read_text(encoding='utf-8').splitlines() if line.strip()]
    report = summarize(rows)
    with Path(args.output).open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
