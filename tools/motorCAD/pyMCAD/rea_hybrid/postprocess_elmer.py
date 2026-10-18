"""Offline CLI for an existing homogenized Elmer MS A history; never solves FEA.

Run as `python -m rea_hybrid.postprocess_elmer` with pyMCAD on PYTHONPATH.
Each invocation consumes one explicit field/manifest pair, including no-load.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np
from matplotlib.tri import Triangulation
from .e10_sampling import sampling_geometry, evaluate_active_samples


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract_samples(field, manifest, contract):
    with np.load(field, allow_pickle=False) as d:
        required = {'node_ids', 'node_xy_m', 'triangles', 'physical', 'A_node_Wb_per_m'}
        if not required.issubset(d.files):
            raise ValueError('Expected ALL_A_HISTORY.npz schema from homogenized_ms_worker')
        xy, triangles, physical, a = (d[k] for k in ('node_xy_m','triangles','physical','A_node_Wb_per_m'))
    count = int(manifest['samples_per_period'])
    if a.shape != (count, len(xy)) or int(manifest['total_steps']) != count:
        raise ValueError('Require exactly one complete MS cycle; resolve any multi-cycle window explicitly')
    if not np.isfinite(a).all() or manifest['profile'] != 'homogenized-slot-MS-v1':
        raise ValueError('Expected finite homogenized-slot MS potential')
    if not manifest['diffusion_all_regions_off'] or manifest['circuit_ODE_present']:
        raise ValueError('MS source must be diffusion-free with no circuit ODE')
    source_kr = float(manifest['radial_factor'])
    if source_kr <= 0:
        raise ValueError('Positive source radial factor required')
    g = sampling_geometry(contract['geometry_settings_mm'])
    p = g['points_m']*source_kr
    chosen = np.flatnonzero(physical == 2401)
    finder = Triangulation(xy[:,0], xy[:,1], triangles[chosen]).get_trifinder()
    found = finder(p[:,0], p[:,1])
    if np.any(found < 0):
        raise ValueError('Sampling leaves homogenized slot 1; do not silently extrapolate')
    ti = chosen[found]
    vertices = xy[triangles[ti]]
    edges = vertices[:,1:]-vertices[:,:1]
    values = []
    for frame in a:
        av = frame[triangles[ti]]
        grad = np.linalg.solve(edges, (av[:,1:]-av[:,:1])[...,None])[...,0]
        values.append(np.linalg.norm(grad, axis=1))
    b = np.asarray(values)
    return b, g


def run(field, manifest_path, contract_path, output, targets, speeds):
    field, manifest_path, contract_path, output = map(Path, (field,manifest_path,contract_path,output))
    # Fail rather than overwrite another host's results on a repeated command.
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    contract = json.loads(contract_path.read_text(encoding='utf8'))
    source_kr = float(manifest['radial_factor'])
    contract = dict(contract, Ref_current_Arms=float(manifest['current_rms_A'])/source_kr)
    b, geometry = extract_samples(field, manifest, contract)
    rows, waves = [], {}
    factors = {'Ref':1., 'HalfSC':1.5, 'SC':2.}
    for target in targets:
        kr = factors[target]
        current = contract['Ref_current_Arms']*kr
        for speed in speeds:
            r = evaluate_active_samples(b, geometry, contract, current, speed, kr)
            waves[f'{target}_{speed}'] = r.pop('proximity_waveform_W')
            rows.append(dict(source_case_id=manifest['case_id'], source_model=manifest['model'],
                             source_current_Arms=manifest['current_rms_A'], source_radial_factor=source_kr,
                             model=target, current_Arms=current, beta_deg=manifest['beta_deg'],
                             speed_rpm=speed, radial_factor=kr, **r))
    np.savez_compressed(output/'SAMPLES.npz', B_magnitude_T=b, **geometry)
    np.savez_compressed(output/'WAVEFORMS.npz', **waves)
    (output/'LOSSES.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
    with (output/'LOSSES.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    provenance = dict(schema='rea-elmer-offline-v1', source_case_id=manifest['case_id'],
                      field_sha256=sha(field), manifest_sha256=sha(manifest_path),
                      contract_sha256=sha(contract_path), samples_shape=list(b.shape),
                      line_counts=geometry['line_counts'], source_solver='Elmer',
                      field_scope='MS A to exact P1 curl magnitude, 600 samples in slot 1',
                      window='One full cycle of distinct post-step phases; arithmetic mean',
                      loss_scope='Active-stack AC excess, no transport DC or end winding',
                      sigma_S_m=contract['sigma_S_m'], active_length_m=contract['active_length_m'],
                      fitted_parameters=0, new_solver_calls=0, AF_refit=False,
                      comparison_scope='Standalone Hybrid estimate, not a Full-FEA accuracy claim',
                      code_sha256={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')})
    (output/'RECEIPT.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf8')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--field',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--contract',type=Path,default=Path(__file__).parent/'examples/e10_ref_input.json')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--targets',nargs='+',choices=['Ref','HalfSC','SC'],default=['Ref','HalfSC','SC'])
    p.add_argument('--speeds',nargs='+',type=int,default=[2000,4000,8000,16000])
    args=p.parse_args()
    rows=run(args.field,args.manifest,args.contract,args.out,args.targets,args.speeds)
    print(json.dumps(dict(rows=len(rows),output=str(args.out.resolve()),solver_calls=0)))


if __name__ == '__main__':
    main()
