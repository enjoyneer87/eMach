"""SC per-element B(t) extraction from the archived HYBRID .mes files.

Identical to extract_sc_b.py but reads from Hybrid_Speed_* folders
instead of FullFEA_Speed_*, so the element B is the MS (magnetostatic,
sigma=0 in conductors) source field that Motor-CAD uses internally for
its Hybrid AC loss calculation — NOT the TS field with eddy reaction.

Output: sc_b_data_hybrid/Hybrid_Speed_{rpm}RPM_{I}A_{ph}deg.json
  (separate from sc_b_data/ which holds the TS-sourced extraction)

Use these JSONs with mesh_b_vs_mcad.py to replicate the eMag Hybrid
internal calculation more faithfully:
  P_prox = sigma * L * omega^2 * w * h^3 / 24 * |B|^2 (per harmonic)

The conductors in the Hybrid .mes are sigma=0 (no eddy), so the B field
inside the conductor is the true external source field — area-weighted
mean |B|^2 here will be much closer to what Motor-CAD's slot field model
provides per layer than the TS eddy-distorted equivalent.

Differences vs extract_sc_b.py:
  ARCHIVE subfolder : Hybrid_Speed_*  (was FullFEA_Speed_*)
  OUT_DIR           : sc_b_data_hybrid/  (was sc_b_data/)
  field_source tag  : 'Hybrid MS solution (sigma=0 conductors)'
  KEEP_TXT          : none (all txt cleaned up; no J panel needed)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / 'tools' / 'motorCAD'))

import elhajji_2d_fea_extract as ex  # noqa: E402

MOT = r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot'
ARCHIVE = Path(r'D:\KangDH\Thesis\e10\ACLossCalcExport_SC_no_txt')
OUT_DIR = HERE / 'sc_b_data_hybrid'
TXT_DIR = Path(r'C:\Users\user\AppData\Local\Temp\mcad_hybrid_b_txt')

CASES = [(2000, '920.0', 36.0), (4000, '920.0', 36.0),
         (8000, '920.0', 36.0), (16000, '920.0', 36.0),
         (16000, '920.0', 54.0), (16000, '460.1', 36.0)]

RE_TURN = re.compile(r'^Turn_\d+_\d+$')
RE_SLOT = re.compile(r'^ArmatureSlot[A-F]\d$')


def extract_any(txt_path):
    """extract_case trying both conductor-region naming schemes."""
    for pat in (RE_TURN, RE_SLOT):
        ex.COPPER_RE = pat
        try:
            return ex.extract_case(txt_path)
        except ValueError:
            continue
    raise ValueError(f'no copper regions matched in {txt_path}')


def main() -> None:
    import ansys.motorcad.core as pymotorcad
    from pyMCAD.fea_workflow import prepare_fea_export_session
    from pyMCAD.magnetic import get_magnetic_data

    OUT_DIR.mkdir(exist_ok=True)
    TXT_DIR.mkdir(parents=True, exist_ok=True)

    mc = pymotorcad.MotorCAD(enable_success_variable=False)
    try:
        mc.set_variable('MessageDisplayState', 2)
    except Exception:
        pass
    mc.load_from_file(MOT)
    print('loaded:', MOT)

    for spd, cur, ph in CASES:
        # ------ KEY DIFFERENCE: read from Hybrid_Speed_* folder ------
        tag = f'Hybrid_Speed_{spd}RPM_{cur}A_{ph}deg'
        out_json = OUT_DIR / f'Hybrid_Speed_{spd}RPM_{cur}A_{ph}deg.json'
        if out_json.exists():
            print('[skip] already extracted:', out_json.name)
            continue
        mes = ARCHIVE / tag / 'FEResultsData' / 'OnLoadTorque_result_1.mes'
        if not mes.exists():
            print('[skip] missing mes:', mes)
            continue
        print(f'--- {tag} (Hybrid MS .mes, sigma=0 conductors)')
        prepare_fea_export_session(mc, mes_path=mes)
        txt = TXT_DIR / f'{tag}.txt'
        get_magnetic_data(mc, first_step=1, final_step=0,
                          auto_final_step=True, filename=txt,
                          clean_up=False)
        print('    exported txt:', txt.name)

        d = extract_any(txt)
        d['speed_rpm'] = spd
        d['phase_deg'] = ph
        d['current_A'] = float(cur)
        d['source'] = str(mes)
        d['field_source'] = ('Hybrid MS solution (sigma=0 conductors; '
                             'B is source field without eddy reaction)')
        json.dump(d, open(out_json, 'w', encoding='utf-8'))
        print(f"    saved {out_json.name} (steps={d.get('n_steps_total')}, "
              f"regions={len(d['regions'])})")
        try:
            txt.unlink()   # ~60 MB each
        except OSError:
            pass

    mc.quit()
    print('done')


if __name__ == '__main__':
    main()
