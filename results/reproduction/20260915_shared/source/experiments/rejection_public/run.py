"""Reproduce kidney biopsy models using discovery data for model/threshold selection.

Run: uv run python experiments/rejection_public/run.py
Raw NanoString counts are transformed sample-by-sample. No jointly corrected matrix
values, phenotype metadata, sample identifiers, or batch identifiers are predictors.
This repeats the fixed baseline recipe; its evaluation results have already been seen.
"""
from pathlib import Path
import argparse, json, time, sys, platform, shutil
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
from sklearn.metrics import roc_auc_score, average_precision_score, confusion_matrix
import joblib
from kidney_biopsy import (
    AssaySchema, map_diagnoses, normalize_counts, predict_scores,
    read_geo_matrix, read_rcc_archive,
)

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw/rejection_public'
OUT=ROOT/'results/reproduction/baseline'
MODEL_DIR=ROOT/'data/processed/models/baseline'

def matrix(gse):
    return read_geo_matrix(RAW/f'{gse}_series_matrix.txt.gz')

def raw_biopsy(meta, batch_output=None):
    counts,batches=read_rcc_archive(RAW/'GSE212160_RAW.tar', specimen_ids=meta.index)
    values=normalize_counts(counts)
    if batch_output is not None:
        batches.to_csv(batch_output)
    return values

def threshold(y,p,sensitivity=.90):
    # Highest threshold that keeps >=90% of screening positives; no calibration fit.
    candidates=np.unique(p)
    return float(max(t for t in candidates if (p[y==1]>=t).mean()>=sensitivity))

def scores(y,p,t):
    tn,fp,fn,tp=confusion_matrix(y,p>=t,labels=[0,1]).ravel()
    return {'n':int(len(y)),'positives':int(sum(y)),'roc_auc':float(roc_auc_score(y,p)),
            'average_precision':float(average_precision_score(y,p)),'threshold':float(t),
            'sensitivity':float(tp/(tp+fn)),'specificity':float(tn/(tn+fp)),
            'ppv':float(tp/(tp+fp)) if tp+fp else None,'npv':float(tn/(tn+fn)) if tn+fn else None,
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
    if X.shape != (1395,758):
        raise ValueError(f'Expected 1,395 specimens and 758 assay predictors, received {X.shape}.')
    expected_cohorts={'Discovery cohort sample':1050,'Validation cohort sample':345}
    if meta['cohort'].value_counts(dropna=False).to_dict() != expected_cohorts:
        raise ValueError('Unexpected or missing source cohort membership.')
    discovery=meta.index[meta['cohort'].eq('Discovery cohort sample')]
    test=meta.index[meta['cohort'].eq('Validation cohort sample')]
    hist=meta['histology diganosis of rejection'].rename('histology_diagnosis')
    binary_target=map_diagnoses(hist)
    train,valid=train_test_split(discovery.to_numpy(),test_size=.25,stratify=hist.loc[discovery].to_numpy(),random_state=20260915)
    split=pd.Series('author_validation',index=meta.index); split.loc[train]='train'; split.loc[valid]='discovery_screen'
    pd.DataFrame({'sample':meta.index,'split':split,'histology':hist,'title':meta.title}).to_csv(OUT/'biopsy_split.csv',index=False)
    duplicate_values=X.duplicated(keep=False)
    if duplicate_values.any():
        profile_hash=pd.util.hash_pandas_object(X,index=False)
        across=pd.DataFrame({'profile':profile_hash,'split':split}).groupby('profile')['split'].nunique()
        if across.gt(1).any():
            raise ValueError('Identical molecular profiles cross training/screening/evaluation splits.')
    audit={'included_specimens':len(meta),'excluded_specimens':0,'predictor_count':len(X.columns),
           'cohorts':expected_cohorts,'duplicate_normalized_profiles':int(duplicate_values.sum()),
           'cross_split_duplicate_profiles':0,
           'class_counts':pd.crosstab(split,hist).to_dict(orient='index'),
           'sample_join':'GEO and raw RCC specimen sets match exactly; each appears once.',
           'predictors':'Assay targets only; housekeeping targets, diagnosis, cohort, IDs, and batch excluded.'}
    (OUT/'data_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print('COUNTS',len(train),len(valid),len(test),len(X.columns),'duplicate_raw_profiles',duplicate_values.sum(),flush=True)
    targets={'any_rejection':binary_target,
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
            p=predict_scores(model,xx.loc[valid])
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
                'train_n':len(train),'screen_n':len(valid),'test_n':len(test),'features':list(X.columns),
                'schema':AssaySchema(features=tuple(X.columns)).to_dict(),
                'model_version':f'{OUT.name}:{target}:{selected["model"]}'}
        (OUT/f'{target}_frozen.json').write_text(json.dumps(freeze,indent=2))
        # Author validation accessed only after the selection and threshold are written.
        final={}
        for name in dict.fromkeys([selected['model'],'single_gene_IFNG','logistic_all']):
            row=next(s for s in screens if s['model']==name)
            xx=X[['IFNG']] if name=='single_gene_IFNG' else X
            screen_scores=predict_scores(fitted[name],xx.loc[valid])
            pd.DataFrame({'sample':valid,'y':y.loc[valid],'rejection_score':screen_scores,
                          'predicted':screen_scores>=row['threshold']}).to_csv(OUT/f'{target}_{name}_screen_predictions.csv',index=False)
            joblib.dump(fitted[name],MODEL_DIR/f'{target}_{name}.joblib')
            p=predict_scores(fitted[name],xx.loc[test])
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
    start_time=time.perf_counter()
    configuration={
        'procedure':'Reproduction of baseline models, discovery split, selection, and thresholds; shared preprocessing/prediction extraction.',
        'target':'Any recorded rejection, plus two secondary component targets.',
        'normalization':'log2(raw count + 1) minus within-specimen mean of 12 log2(housekeeping count + 1) values.',
        'discovery_split':{'test_size':.25,'stratify':'four original diagnoses','random_state':20260915},
        'threshold_rule':'Highest screening score threshold retaining at least 90% of rejection cases.',
        'selection_rule':'Maximum screening specificity, then ROC-AUC; fitted model retained without refitting.',
        'models':{
            'catboost_all_depth4':{'iterations':300,'depth':4,'learning_rate':.04,'random_seed':2026},
            'catboost_all_depth6':{'iterations':300,'depth':6,'learning_rate':.04,'random_seed':2026},
            'catboost_top50':{'selection':'f_classif on training only','k':50,'catboost':'catboost_all_depth4'},
            'catboost_top200':{'selection':'f_classif on training only','k':200,'catboost':'catboost_all_depth4'},
            'logistic_all':{'scaler':'StandardScaler fitted on training only','C':.1,'max_iter':2000},
            'logistic_top50':{'selection':'f_classif on training only','k':50,'logistic':'logistic_all'},
            'extra_trees':{'n_estimators':400,'min_samples_leaf':3,'max_features':.3,'random_state':2026},
            'hist_boosting':{'max_iter':150,'max_leaf_nodes':7,'l2_regularization':5,'random_state':2026},
            'single_gene_IFNG':{'scaler':'StandardScaler fitted on training only','C':1,'max_iter':1000},
        },
        'constant_baseline':'Training-label prevalence as score; threshold 0.5 (majority prediction).',
    }
    (OUT/'configuration.json').write_text(json.dumps(configuration,indent=2),encoding='utf-8')
    # Preserve executable source and lockfile with the run, even after later development.
    sources=[Path(__file__),ROOT/'pyproject.toml',ROOT/'uv.lock',ROOT/'scripts/verify_local_data.py',
             *sorted((ROOT/'src/kidney_biopsy').glob('*.py'))]
    snapshots=[]
    for source in sources:
        relative=source.relative_to(ROOT)
        snapshot=OUT/'source'/relative
        snapshot.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,snapshot)
        snapshots.append({'file':relative.as_posix(),'sha256':sha256(source),
                          'snapshot':snapshot.relative_to(ROOT).as_posix()})
    biopsy()
    artifacts=[]
    for directory in [OUT,MODEL_DIR]:
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.name not in {'run_manifest.json','run.log'}:
                artifacts.append({'file':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha256(path)})
    manifest={'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),
              'elapsed_seconds':time.perf_counter()-start_time,
              'python':platform.python_version(),'dependencies':{name:version(name) for name in ['catboost','joblib','numpy','pandas','scikit-learn','scipy']},
              'input_manifest':'data/manifest.json','input_manifest_sha256':sha256(ROOT/'data/manifest.json'),
              'source':{'file':'experiments/rejection_public/run.py','sha256':sha256(Path(__file__))},
              'sources':snapshots,
              'environment_lock':{'file':'uv.lock','sha256':sha256(ROOT/'uv.lock')},
              'seeds':{'discovery_split':20260915,'catboost':2026,'extra_trees':2026,'hist_boosting':2026},
              'fit_count':27,'output_dir':args.output_dir,'model_dir':args.model_dir,'artifacts':artifacts,
              'configuration':'configuration.json'}
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
