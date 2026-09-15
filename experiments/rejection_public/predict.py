"""Apply a locally trained kidney-biopsy classifier to raw NanoString counts.

CSV input: one specimen per row, first column specimen ID, other columns target
names from the same B-HOT assay, including the 12 housekeeping targets.
"""
import argparse, csv, json, sys
from run import ROOT, matrix, raw_biopsy
import joblib, pandas as pd, numpy as np

sys.path.insert(0, str(ROOT / 'scripts'))
from verify_local_data import local_path, records, verify, sha256


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--counts-csv',type=str)
    source.add_argument('--geo-validation',action='store_true')
    parser.add_argument('--results-dir',default='results/reproduction/baseline')
    parser.add_argument('--model-dir',default='data/processed/models/baseline')
    parser.add_argument('--output',default='results/reproduction/baseline/inference.csv')
    args=parser.parse_args()
    results_dir=local_path(args.results_dir)
    model_dir=local_path(args.model_dir)
    manifest_path=results_dir/'run_manifest.json'
    if not manifest_path.is_file():
        raise ValueError('Prediction requires a completed local training run with run_manifest.json.')
    manifest=json.loads(manifest_path.read_text())
    if model_dir != local_path(manifest['model_dir']):
        raise ValueError('Model directory does not match the selected training run.')
    frozen_path=results_dir/'any_rejection_frozen.json'
    model_path=model_dir/'any_rejection_selected_model.joblib'
    artifacts={item['file']:item for item in manifest['artifacts']}
    for path in [frozen_path,model_path]:
        relative=path.relative_to(ROOT).as_posix()
        item=artifacts.get(relative)
        if item is None or path.stat().st_size!=item['bytes'] or sha256(path)!=item['sha256']:
            raise ValueError(f'Model or threshold metadata differs from the training run: {relative}')
    frozen=json.loads(frozen_path.read_text())
    model=joblib.load(model_path)
    if args.geo_validation:
        for item in records():
            verify(local_path(item['file']),item)
        _,meta=matrix('GSE212160')
        x=raw_biopsy(meta).loc[meta['cohort'].eq('Validation cohort sample')]
    else:
        path=local_path(args.counts_csv)
        with path.open(newline='',encoding='utf-8-sig') as stream:
            header=next(csv.reader(stream),[])
        if not header or len(header)!=len(set(header)):
            raise ValueError('CSV needs a header with unique target names.')
        counts=pd.read_csv(path,index_col=0).astype(float)
        if counts.empty or not counts.index.is_unique or counts.index.isna().any():
            raise ValueError('CSV needs at least one specimen and unique, present specimen IDs.')
        if not np.isfinite(counts.to_numpy()).all() or (counts<0).any().any():
            raise ValueError('Raw counts must be finite, nonnegative, and present for every assay target.')
        hk=['ABCF1','G6PD','GUSB','NRDE2','OAZ1','POLR2A','PPIA','SDHA','STK11IP','TBC1D10B','TBP','UBB']
        missing=sorted(set(hk+frozen['features'])-set(counts.columns))
        if missing:
            raise ValueError(f'Missing required assay targets: {", ".join(missing)}')
        log=np.log2(counts+1)
        x=log.sub(log[hk].mean(axis=1),axis=0)
    x=x[frozen['features']]
    probability=model.predict_proba(x)[:,1]
    output=local_path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame({'specimen':x.index,'rejection_score':probability,
                  'rejection_flag':probability>=frozen['threshold']}).to_csv(output,index=False)
    print(f'Wrote {len(x)} exploratory biopsy predictions to {args.output}')


if __name__=='__main__':
    main()
