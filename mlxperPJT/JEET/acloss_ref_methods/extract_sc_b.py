"""SC per-element B(t) extraction from the archived FullFEA .mes files.

Per user direction, NO re-solving: the archived TS solutions in
ACLossCalcExport_SC_no_txt (FullFEA_Speed_* folders, .mes present) are
loaded through Motor-CAD COM and re-exported as element tables:
  load SC .mot -> prepare_fea_export_session(OnLoadTorque_result_1.mes)
  -> get_magnetic_data(all steps) writes the
  "Solution/ElementsTable(Bx,By,...)/NodesTable/RegionsTable" txt
  -> elhajji_2d_fea_extract.extract_case parses conductor regions.

Caveats (accepted): the element B is the TS field (conductor eddy
reaction included), not the MS source field the Hybrid method uses;
the archive predates the 2 mm magnet axial extension (negligible).

Archived FullFEA .mes name conductor regions 'Turn_<n>_<m>'; live
exports use 'ArmatureSlot<slot><layer>' — extraction tries both.

Output: sc_b_data/Hybrid_Speed_{rpm}RPM_{I}A_{ph}deg.json (filenames
keep the Hybrid_ prefix for mesh_b_vs_mcad.py compatibility), plus the
kept 16k FullFEA txt (element J for the Fig-8 style panel).
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
OUT_DIR = HERE / 'sc_b_data'
TXT_DIR = Path(r'C:\Users\user\AppData\Local\Temp\claude'
               r'\d--KangDH-EveryMotor'
               r'\6ca5d576-7208-4b98-afe7-21a673b592de\scratchpad'
               r'\sc_fea_txt')

CASES = [(2000, '920.0', 36.0), (4000, '920.0', 36.0),
         (8000, '920.0', 36.0), (16000, '920.0', 36.0),
         (16000, '920.0', 54.0), (16000, '460.1', 36.0)]

# cases whose exported txt is KEPT for the Fig-8 style J(x,y) panel
KEEP_TXT = {(16000, '920.0', 36.0)}

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
        tag = f'FullFEA_Speed_{spd}RPM_{cur}A_{ph}deg'
        out_json = OUT_DIR / f'Hybrid_Speed_{spd}RPM_{cur}A_{ph}deg.json'
        if out_json.exists():
            print('[skip] already extracted:', out_json.name)
            continue
        mes = ARCHIVE / tag / 'FEResultsData' / 'OnLoadTorque_result_1.mes'
        if not mes.exists():
            print('[skip] missing mes:', mes)
            continue
        print(f'--- {tag} (archived .mes export, no solve)')
        prepare_fea_export_session(mc, mes_path=mes)
        txt = TXT_DIR / f'{tag}.txt'
        # final_step=0 (NOT None): export_magnetic_txt only auto-infers
        # the last step when final_step <= 0 — None silently becomes 1
        get_magnetic_data(mc, first_step=1, final_step=0,
                          auto_final_step=True, filename=txt,
                          clean_up=False)
        print('    exported txt:', txt.name)

        d = extract_any(txt)
        d['speed_rpm'] = spd
        d['phase_deg'] = ph
        d['current_A'] = float(cur)
        d['source'] = str(mes)
        d['field_source'] = ('FullFEA TS solution (conductor reaction '
                             'included; archive predates 2 mm magnet '
                             'extension)')
        json.dump(d, open(out_json, 'w', encoding='utf-8'))
        print(f"    saved {out_json.name} (steps={d.get('n_steps_total')}, "
              f"regions={len(d['regions'])})")
        if (spd, cur, ph) in KEEP_TXT:
            print('    txt kept for Fig-8 panel')
        else:
            try:
                txt.unlink()                 # ~60 MB each; keep disk sane
            except OSError:
                pass

    mc.quit()
    print('done')


if __name__ == '__main__':
    main()
