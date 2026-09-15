"""Check local training artifacts and independent inference against this run's evaluation."""
import argparse
import csv
import json
import math
from pathlib import Path

from verify_local_data import ROOT, local_path, sha256


def read_rows(path, key):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    mapping = {row[key]: row for row in rows}
    if not rows or len(mapping) != len(rows):
        raise ValueError(f'Empty output or duplicate specimen IDs: {path.name}')
    return mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', default='results/reproduction/baseline')
    parser.add_argument('--inference-csv', default='results/reproduction/baseline/inference.csv')
    args = parser.parse_args()
    run_dir = local_path(args.run_dir)
    manifest = json.loads((run_dir/'run_manifest.json').read_text())
    for item in manifest['artifacts']:
        path = local_path(item['file'])
        if path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
            raise ValueError(f'Run artifact does not match its training manifest: {item["file"]}')
    for item in [manifest['source'], manifest['environment_lock']]:
        if sha256(local_path(item['file'])) != item['sha256']:
            raise ValueError(f'Run source or environment changed: {item["file"]}')
    frozen = json.loads((run_dir/'any_rejection_frozen.json').read_text())
    expected = read_rows(run_dir/f'any_rejection_{frozen["selected_model"]}_test_predictions.csv', 'sample')
    actual = read_rows(local_path(args.inference_csv), 'specimen')
    if expected.keys() != actual.keys() or len(actual) != frozen['test_n']:
        raise ValueError('Inference and evaluation specimen IDs differ.')
    differences = []
    predicted_positive = 0
    for specimen, row in actual.items():
        score = float(row['rejection_score'])
        difference = abs(score-float(expected[specimen]['probability']))
        if not math.isfinite(score) or difference > 1e-12:
            raise ValueError(f'Inference probability mismatch: {specimen}')
        flag = row['rejection_flag'] == 'True'
        if flag != (expected[specimen]['predicted'] == 'True') or flag != (score >= frozen['threshold']):
            raise ValueError(f'Inference class mismatch: {specimen}')
        differences.append(difference)
        predicted_positive += flag
    summary = {'verified_artifacts': len(manifest['artifacts']), 'specimens': len(actual),
               'max_absolute_probability_difference': max(differences),
               'predicted_positive': predicted_positive, 'predicted_negative': len(actual)-predicted_positive,
               'threshold': frozen['threshold'], 'comparison': 'Separate inference versus evaluation produced by this local training run.'}
    (run_dir/'inference_verification.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
