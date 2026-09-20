"""Recheck cached shaft-map arrays using an explicit common feasibility mask.

This does not run the trajectory solver. Input is the author-side
effmap_shaft_SC.npz, which is not part of the reviewed public release.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def audit(path):
    with np.load(path) as d:
        target = d['targets']
        common = np.isfinite(target) & (target > 10)
        for tag in ('truth', 'hybrid', 'cal'):
            common &= np.isfinite(d[tag + '_eta'])
            common &= np.abs(d[tag + '_t_shaft'] - target) <= .02 * np.abs(target)
        if not common.any():
            raise ValueError('No common feasible nodes')
        result = {'mode':'cached_array_recheck',
                  'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                  'mask':'finite three-model eta, target > 10 Nm, each shaft torque within 2% of target',
                  'common_n':int(common.sum()), 'models':{}}
        for tag in ('hybrid','cal'):
            diff = 100 * (d[tag+'_eta'] - d['truth_eta'])
            pair = np.isfinite(diff)
            result['models'][tag] = {
                'common_mean_abs_pp':float(np.mean(np.abs(diff[common]))),
                'common_p95_abs_pp':float(np.percentile(np.abs(diff[common]),95)),
                'legacy_panel_n':int(pair.sum()),
                'legacy_panel_mean_abs_pp':float(np.mean(np.abs(diff[pair])))}
        return result


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if not args.input.is_file():
        print('UNAVAILABLE: shaft-map array not provided; no fallback to MotorLAB arrays')
        raise SystemExit(2)
    output=json.dumps(audit(args.input),indent=2,allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(output+'\n',encoding='utf-8')
    print(output)
