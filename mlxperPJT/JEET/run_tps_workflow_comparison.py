"""M4-3 matched bare-RBF / affine-TPS experiment before prospective M2.

Experimental adapter only. Production model and defaults are not modified.
All comparisons use the existing verification grid, not M2 outcomes.
"""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
import io
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.spatial import Delaunay

from run_evaluator_robustness import datasets_for, fixed_plans, fit_one, SCALES
from run_ref_only_field_pipeline import (
    AcLossPipeline, DEFAULT_CONFIG, Builder, record_result, predict, mask_truth, checksum,
)


def kernel(a, b):
    r2 = np.sum((np.asarray(a)[:, None, :] - np.asarray(b)[None, :, :])**2, axis=2)
    return r2*np.log(np.sqrt(r2)+1e-12)


@dataclass(frozen=True)
class Shape:
    centers: np.ndarray
    weights: np.ndarray
    affine: np.ndarray
    scales: np.ndarray

    def predict(self, current, phase):
        i,p = np.broadcast_arrays(np.asarray(current,float),np.asarray(phase,float))
        x = np.column_stack((i.ravel(),p.ravel()))/self.scales
        y = kernel(x,self.centers)@self.weights + np.column_stack((np.ones(len(x)),x))@self.affine
        return y.reshape(i.shape) if i.shape else float(y[0])


@dataclass(frozen=True)
class CandidateModel:
    shape: Shape
    p_coeffs: np.ndarray
    q_coeffs: np.ndarray

    def predict_g(self,current,phase):
        return self.shape.predict(current,phase)

    def predict(self,speed,current,phase):
        s,i,p = np.broadcast_arrays(np.asarray(speed,float)/1000,np.asarray(current,float),np.asarray(phase,float))
        return np.polyval(self.p_coeffs,s)*np.clip(self.predict_g(i,p),1e-3,None)**np.polyval(self.q_coeffs,s)


def shape_fit(ds, indices, affine):
    scales = np.array([ds.LS_I,ds.LS_P])
    x = np.column_stack((ds.irms_arr[indices],ds.phase_arr[indices]))/scales
    y = ds.af_arr[indices]
    k = kernel(x,x)+1e-6*np.eye(len(x))
    if affine:
        p = np.column_stack((np.ones(len(x)),x))
        a = np.block([[k,p],[p.T,np.zeros((3,3))]])
        solution = np.linalg.solve(a,np.r_[y,np.zeros(3)])
        w,c = solution[:-3],solution[-3:]
        assert np.max(np.abs(p.T@w)) < 1e-9
    else:
        w,c = np.linalg.solve(k,y),np.zeros(3)
    return Shape(x,w,c,scales)


def fit_candidate(scale,ds,plan,affine,donor=None,donor_ds=None):
    shape = shape_fit(ds,plan['base'],affine)
    kr = DEFAULT_CONFIG['k_r'][scale]
    samples,counts = {},{}
    train = list(plan['base'])
    for speed,indices in plan['by_speed'].items():
        counts[str(speed)] = 0
        for idx in indices:
            current,phase = ds.irms_arr[idx],ds.phase_arr[idx]
            transferred = scale!='Ref' and speed*kr**2<=16.1
            if transferred:
                sd,id_ = speed*kr**2,current/kr
                ti,tp = Builder.TRANSFER_COORD_TOL
                at = (np.abs(donor_ds.irms_arr-id_)<ti)&(np.abs(donor_ds.phase_arr-phase)<tp)
                assert at.sum()>=2
                sp,h = donor_ds.speeds_k[at],donor_ds.h_ac_arr[at]
                order = np.argsort(sp)
                assert sp[order][0]<=sd<=sp[order][-1]
                hd = np.exp(np.interp(np.log(sd),np.log(sp[order]),np.log(h[order])))
                value = float(donor.predict(sd*1000,id_,phase))*hd/ds.h_ac_arr[idx]
            else:
                train.append(int(idx))
                value = ds.af_arr[idx]
            g = float(shape.predict(current,phase))
            if 0.3<=value/(g+1e-12)<=3:
                samples.setdefault(speed,[]).append((float(value),g))
                counts[str(speed)] += 1
    pf,qp = Builder._fit_speed_scaling(samples,16.,True,verbose=False)
    return CandidateModel(shape,pf,qp),np.unique(train),counts


def family_fit(datasets,plans,affine,mask=None):
    models,records = {},{}
    data = {s:mask_truth(ds,mask[s]['own_train_indices']) if mask else ds for s,ds in datasets.items()}
    for s in SCALES:
        model,indices,admitted = fit_candidate(s,data[s],plans[s],affine,models.get('Ref'),data['Ref'])
        record,error = record_result(datasets[s],model,indices)
        assert not error,error
        record['admitted_pairs_per_speed'] = admitted
        records[s],models[s] = record,model
    return records,models


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--spectra',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    with contextlib.redirect_stdout(io.StringIO()):
        pipe=AcLossPipeline({'data_root':str(a.data)})
        deposited={s:pipe.load_dataset(s) for s in SCALES}
        data=datasets_for(deposited,json.loads(a.spectra.read_text())['rows'],'capped_P24c6')
        plans=fixed_plans(data)
    bare,bare_models=family_fit(data,plans,False)
    tps,tps_models=family_fit(data,plans,True)
    native,models = {},{}
    scipy_deltas = {}
    for s in SCALES:
        with contextlib.redirect_stdout(io.StringIO()):
            m,idx,_=fit_one(s,data[s],models.get('Ref'),data['Ref'],plans[s])
        native[s]=float(np.max(np.abs(predict(m,data[s])-np.asarray(bare[s]['prediction_kW']))))
        assert native[s]<1e-9,(s,native[s])
        models[s]=m
        shape=tps_models[s].shape
        y=data[s].af_arr[plans[s]['base']]
        ref=RBFInterpolator(shape.centers,y,kernel='thin_plate_spline',degree=1,smoothing=1e-6)
        q=np.array([[.21,.37],[.53,.82],[.77,.61]])
        # Fixed interior checks, independent of AF errors.
        x=shape.centers.min(axis=0)+q*np.ptp(shape.centers,axis=0)
        ours=shape.predict(x[:,0]*shape.scales[0],x[:,1]*shape.scales[1])
        scipy_deltas[s]=float(np.max(np.abs(ours-ref(x))))
        assert scipy_deltas[s]<1e-8
        affine_y=1+.2*shape.centers[:,0]-.3*shape.centers[:,1]
        af_ref=RBFInterpolator(shape.centers,affine_y,kernel='thin_plate_spline',degree=1,smoothing=1e-6)
        np.testing.assert_allclose(af_ref(x),1+.2*x[:,0]-.3*x[:,1],atol=1e-10)
    masked_deltas={}
    for label,use_affine,result in [('bare',False,bare),('affine_tps',True,tps)]:
        masked,_=family_fit(data,plans,use_affine,result)
        masked_deltas[label]={s:float(np.max(np.abs(np.asarray(result[s]['prediction_kW'])-masked[s]['prediction_kW']))) for s in SCALES}
        assert max(masked_deltas[label].values())==0
    loo={}
    for label,use_affine in [('bare',False),('affine_tps',True)]:
        loo[label]={}
        for s in SCALES:
            folds=[]
            for index in plans[s]['base']:
                fold_plans={k:{'base':v['base'].copy(),'by_speed':v['by_speed']} for k,v in plans.items()}
                fold_plans[s]['base']=fold_plans[s]['base'][fold_plans[s]['base']!=index]
                # Remove the held-out anchor truth from all training access.
                mask_ref={k:dict(bare[k]) for k in SCALES}
                mask_ref[s]['own_train_indices']=[i for i in bare[s]['own_train_indices'] if i!=index]
                fold_result,fold_models=family_fit(data,fold_plans,use_affine,mask_ref)
                ds=data[s]
                truth=ds.f_ac_arr[index]
                predicted=fold_result[s]['prediction_kW'][index]
                train_xy=np.column_stack((ds.irms_arr[fold_plans[s]['base']],ds.phase_arr[fold_plans[s]['base']]))
                xy=np.array([ds.irms_arr[index],ds.phase_arr[index]])
                in_hull=bool(Delaunay(train_xy).find_simplex(xy)>=0)
                folds.append({'index':int(index),'current_A':float(xy[0]),'beta_deg':float(xy[1]),
                              'truth_kW':float(truth),'prediction_kW':float(predicted),'inside_remaining_hull':in_hull,
                              'full_wmae_pct':fold_result[s]['full']['wmae_pct']})
            tr=np.array([x['truth_kW'] for x in folds]);pr=np.array([x['prediction_kW'] for x in folds])
            loo[label][s]={'wmae_pct':float(100*np.abs(tr-pr).sum()/tr.sum()),'folds':folds}
    result={'scope':'same Ref-only capped evaluator; fixed own and donor-probe coordinates; exact speed anchor',
            'new_FEA_solves':0,'regularization':1e-6,'native_bare_max_delta_kW':native,
            'independent_scipy_tps_max_delta_AF':scipy_deltas,'truth_mask_max_delta_kW':masked_deltas,
            'fixed_grid':{'bare':bare,'affine_tps':tps},'full_workflow_anchor_LOO':loo,
            'source_spectra_sha256':checksum(a.spectra),'script_sha256':checksum(Path(__file__)),
            'input_sha256':{s:checksum(a.data/DEFAULT_CONFIG['json'][s]) for s in SCALES},
            'limitations':['Existing-grid and LOO comparisons are model-development evidence.',
                           'No M2 outcomes used. No new 16 kRPM input points are tested.',
                           'Table B.1 three-dimensional baseline fairness is a separate outstanding audit.']}
    a.out.parent.mkdir(exist_ok=True,parents=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for s in SCALES:
        print(s,'grid full/held',bare[s]['full']['wmae_pct'],bare[s]['heldout_own_only']['wmae_pct'],
              '->',tps[s]['full']['wmae_pct'],tps[s]['heldout_own_only']['wmae_pct'],
              'anchor LOO',loo['bare'][s]['wmae_pct'],'->',loo['affine_tps'][s]['wmae_pct'])
    print('PASS native/SciPy/masking checks; output',a.out)


if __name__=='__main__':
    main()
