"""Rapid kidney biopsy rejection experiments, with author validation untouched until selection.

Run: uv run python experiments/rejection_public/run.py
Raw NanoString counts are transformed sample-by-sample. No jointly corrected matrix
values, phenotype metadata, sample identifiers, or batch identifiers are predictors.
"""
from pathlib import Path
import argparse, csv, gzip, io, json, tarfile, re, time, hashlib, sys, platform
from datetime import datetime, timezone
from importlib.metadata import version
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, confusion_matrix, accuracy_score, f1_score
import joblib

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw/rejection_public'
OUT=ROOT/'results/reproduction/baseline'
MODEL_DIR=ROOT/'data/processed/models/baseline'

def matrix(gse):
    text=gzip.open(RAW/f'{gse}_series_matrix.txt.gz','rt',encoding='utf-8').read()
    pre,table=text.split('!series_matrix_table_begin',1)
    rows=[next(csv.reader([l],delimiter='\t')) for l in pre.splitlines() if l.startswith('!Sample_')]
    ids=next(row[1:] for row in rows if row[0]=='!Sample_geo_accession')
    meta=pd.DataFrame(index=ids)
    for row in rows:
        if row[0]=='!Sample_characteristics_ch1':
            for ident,value in zip(ids,row[1:]):
                if ': ' in value:
                    k,v=value.split(': ',1); meta.loc[ident,k]=v
        elif row[0] in ('!Sample_title','!Sample_source_name_ch1'):
            meta[row[0].removeprefix('!Sample_')]=row[1:]
    values=pd.read_csv(io.StringIO(table.split('!series_matrix_table_end')[0].strip()),sep='\t',index_col=0).T
    return values,meta

def raw_biopsy(meta, batch_output=None):
    records={}; batches={}
    with tarfile.open(RAW/'GSE212160_RAW.tar') as archive:
        for member in archive.getmembers():
            ident=member.name.split('_')[0]
            text=gzip.decompress(archive.extractfile(member).read()).decode()
            body=text.split('<Code_Summary>')[1].split('</Code_Summary>')[0].strip()
            table=pd.read_csv(io.StringIO(body))
            table=table[table.CodeClass.isin(['Endogenous','Housekeeping'])]
            records[ident]=dict(zip(table.Name,table.Count))
            batches[ident]=dict(re.findall(r'^(Date|CartridgeID|ScannerID),([^\r\n]*)',text,flags=re.M))
    counts=pd.DataFrame.from_dict(records,orient='index').loc[meta.index]
    hk=['ABCF1','G6PD','GUSB','NRDE2','OAZ1','POLR2A','PPIA','SDHA','STK11IP','TBC1D10B','TBP','UBB']
    # Equivalent to log of the count divided by the sample's housekeeping geometric mean.
    log=np.log2(counts.astype(float)+1)
    values=log.sub(log[hk].mean(axis=1),axis=0).drop(columns=hk)
    if batch_output is not None:
        pd.DataFrame.from_dict(batches,orient='index').to_csv(batch_output)
    return values

def threshold(y,p,sensitivity=.90):
    # Highest threshold that keeps >=90% of calibration positives, no test data used.
    candidates=np.unique(p)
    return float(max(t for t in candidates if (p[y==1]>=t).mean()>=sensitivity))

def scores(y,p,t):
    tn,fp,fn,tp=confusion_matrix(y,p>=t,labels=[0,1]).ravel()
    return {'n':int(len(y)),'positives':int(sum(y)),'roc_auc':float(roc_auc_score(y,p)),
            'average_precision':float(average_precision_score(y,p)),'threshold':float(t),
            'sensitivity':float(tp/(tp+fn)),'specificity':float(tn/(tn+fp)),
            'ppv':float(tp/(tp+fp)) if tp+fp else 0.,'npv':float(tn/(tn+fn)) if tn+fn else 0.,
            'tp':int(tp),'fp':int(fp),'tn':int(tn),'fn':int(fn),
            'accuracy':float((tp+tn)/len(y)),'brier':float(np.mean((y-p)**2))}

def models(n):
    cat=lambda d:CatBoostClassifier(iterations=300,depth=d,learning_rate=.04,loss_function='Logloss',verbose=False,thread_count=3,random_seed=2026,allow_writing_files=False)
    return {
      'catboost_all_depth4':cat(4),
      'catboost_all_depth6':cat(6),
      'catboost_top50':make_pipeline(SelectKBest(f_classif,k=min(50,n)),cat(4)),
      'catboost_top200':make_pipeline(SelectKBest(f_classif,k=min(200,n)),cat(4)),
      'logistic_all':make_pipeline(StandardScaler(),LogisticRegression(C=.1,max_iter=2000)),
      'logistic_top50':make_pipeline(SelectKBest(f_classif,k=min(50,n)),StandardScaler(),LogisticRegression(C=.1,max_iter=2000)),
      'extra_trees':ExtraTreesClassifier(n_estimators=400,min_samples_leaf=3,max_features=.3,n_jobs=3,random_state=2026),
      'hist_boosting':HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=7,l2_regularization=5,random_state=2026)
    }

def biopsy():
    _,meta=matrix('GSE212160')
    X=raw_biopsy(meta, OUT/'raw_batch_identifiers.csv')
    assert not X.isna().any().any()
    discovery=meta.index[meta['cohort'].eq('Discovery cohort sample')]
    test=meta.index[meta['cohort'].eq('Validation cohort sample')]
    hist=meta['histology diganosis of rejection']
    train,valid=train_test_split(discovery.to_numpy(),test_size=.25,stratify=hist.loc[discovery].to_numpy(),random_state=20260915)
    split=pd.Series('author_validation',index=meta.index); split.loc[train]='train'; split.loc[valid]='discovery_screen'
    pd.DataFrame({'sample':meta.index,'split':split,'histology':hist,'title':meta.title}).to_csv(OUT/'biopsy_split.csv',index=False)
    duplicate_values=X.duplicated(keep=False)
    print('COUNTS',len(train),len(valid),len(test),len(X.columns),'duplicate_raw_profiles',duplicate_values.sum(),flush=True)
    targets={'any_rejection':hist.ne('No Rejection').astype(int),
             'antibody_mediated_component':hist.isin(['Antibody-mediated Rejection','Mixed Rejection']).astype(int),
             't_cell_mediated_component':hist.isin(['T cell-mediated Rejection','Mixed Rejection']).astype(int)}
    outputs={}; all_screens=[]
    for target,y in targets.items():
        experiments=models(X.shape[1]); fitted={}; screens=[]
        # Simple single-gene benchmark, fitted only on training rows.
        experiments['single_gene_IFNG']=make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=1000))
        for name,model in experiments.items():
            xx=X[['IFNG']] if name=='single_gene_IFNG' else X
            start=time.time(); model.fit(xx.loc[train],y.loc[train])
            p=model.predict_proba(xx.loc[valid])[:,1]
            t=threshold(y.loc[valid].to_numpy(),p)
            used_features=int(model.named_steps['selectkbest'].get_support().sum()) if hasattr(model,'named_steps') and 'selectkbest' in model.named_steps else xx.shape[1]
            result={'target':target,'model':name,'features':used_features,**scores(y.loc[valid].to_numpy(),p,t),'seconds':time.time()-start}
            print('SCREEN',json.dumps(result),flush=True)
            screens.append(result); fitted[name]=model
        all_screens.extend(screens)
        pd.DataFrame(all_screens).to_csv(OUT/'biopsy_screen.csv',index=False)
        # Freeze choice on discovery specificity at >=90% sensitivity; ROC-AUC breaks ties.
        selected=max([s for s in screens if s['model']!='single_gene_IFNG'],key=lambda s:(s['specificity'],s['roc_auc']))
        freeze={'target':target,'selected_model':selected['model'],'threshold':selected['threshold'],
                'selection':'Max discovery-screen specificity at >=90% sensitivity, then AUC; no refit.',
                'train_n':len(train),'screen_n':len(valid),'test_n':len(test),'features':list(X.columns)}
        (OUT/f'{target}_frozen.json').write_text(json.dumps(freeze,indent=2))
        # Author validation accessed only after the selection and threshold are written.
        final={}
        for name in dict.fromkeys([selected['model'],'single_gene_IFNG','logistic_all']):
            row=next(s for s in screens if s['model']==name)
            xx=X[['IFNG']] if name=='single_gene_IFNG' else X
            p=fitted[name].predict_proba(xx.loc[test])[:,1]
            final[name]=scores(y.loc[test].to_numpy(),p,row['threshold'])
            pd.DataFrame({'sample':test,'y':y.loc[test],'probability':p,'predicted':p>=row['threshold']}).to_csv(OUT/f'{target}_{name}_test_predictions.csv',index=False)
        p=np.full(len(test),float(y.loc[train].mean()))
        final['training_prevalence']=scores(y.loc[test].to_numpy(),p,.5)
        final['prevalence_all_positive']=scores(y.loc[test].to_numpy(),p,0)
        outputs[target]={'selected_model':selected['model'],'screen':selected,'author_validation':final}
        print('FINAL',target,json.dumps(final),flush=True)
        joblib.dump(fitted[selected['model']],MODEL_DIR/f'{target}_selected_model.joblib')
        if hasattr(fitted[selected['model']], 'save_model'):
            fitted[selected['model']].save_model(str(MODEL_DIR/f'{target}_selected_model.cbm'))
        if target == 'any_rejection' and hasattr(fitted[selected['model']], 'feature_importances_'):
            pd.DataFrame({'gene':X.columns, 'importance':fitted[selected['model']].feature_importances_}).sort_values('importance',ascending=False).to_csv(OUT/'any_rejection_gene_importance.csv',index=False)
        (OUT/'biopsy_results.json').write_text(json.dumps(outputs,indent=2))
    print('FINISHED',flush=True)

def main():
    global OUT, MODEL_DIR
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default='results/reproduction/baseline')
    parser.add_argument('--model-dir', default='data/processed/models/baseline')
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT/'scripts'))
    from verify_local_data import local_path, records, verify, sha256
    OUT=local_path(args.output_dir)
    MODEL_DIR=local_path(args.model_dir)
    if (OUT/'run_manifest.json').exists() or (OUT/'biopsy_results.json').exists():
        parser.error('This output directory already contains a run; choose a new --output-dir and --model-dir.')
    if MODEL_DIR.exists() and any(MODEL_DIR.iterdir()):
        parser.error('The model directory must be empty; choose a new --model-dir.')
    for item in records():
        verify(local_path(item['file']),item)
    OUT.mkdir(parents=True,exist_ok=True)
    MODEL_DIR.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat()
    biopsy()
    artifacts=[]
    for directory in [OUT,MODEL_DIR]:
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.name not in {'run_manifest.json','run.log'}:
                artifacts.append({'file':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha256(path)})
    manifest={'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),
              'python':platform.python_version(),'dependencies':{name:version(name) for name in ['catboost','joblib','numpy','pandas','scikit-learn','scipy']},
              'input_manifest':'data/manifest.json','input_manifest_sha256':sha256(ROOT/'data/manifest.json'),
              'source':{'file':'experiments/rejection_public/run.py','sha256':sha256(Path(__file__))},
              'environment_lock':{'file':'uv.lock','sha256':sha256(ROOT/'uv.lock')},
              'seeds':{'discovery_split':20260915,'catboost':2026,'extra_trees':2026,'hist_boosting':2026},
              'fit_count':27,'output_dir':args.output_dir,'model_dir':args.model_dir,'artifacts':artifacts}
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
