"""Fig 15 효율맵 소스 3종 일괄 계산 (pymotorcad 버전).

Motor-CAD Lab 효율맵(EmagneticCalcType_Lab=1)을 세 모델에서 순차 실행,
MotorLAB_elecdata.mat을 map_exports/e10/effmaps/에 수집.
(MATLAB actxserver는 COM 등록이 v2025.2를 가리켜 실패 — pymotorcad는
자체 exe 경로로 v261을 띄우므로 이쪽 사용. runAFCustomLossLab.m S5 참조)
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / 'map_exports' / 'e10' / 'effmaps'

JOBS = [
    ('Ref', r'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot', 460),
    ('SC_hyb', r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_Lab48.mot',
     920),
    ('SC_fullfea',
     r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_FullFEA_LAB.mot', 920),
]


def main() -> None:
    import ansys.motorcad.core as pymotorcad

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, (tag, mot, imax) in enumerate(JOBS, 1):
        out_mat = OUT_DIR / f'MotorLAB_elecdata_{tag}.mat'
        if out_mat.exists():
            print(f'[skip] exists: {out_mat.name}')
            continue
        print(f'=== [{i}/3] {tag}: {mot} (Imax {imax} A)', flush=True)
        mc = pymotorcad.MotorCAD(enable_success_variable=False)
        try:
            mc.set_variable('MessageDisplayState', 2)
            mc.load_from_file(mot)
            built = mc.get_model_built_lab()
            print('  Lab built:', built, flush=True)
            if not built:
                raise RuntimeError(f'Lab model not built: {tag}')

            mc.set_motorlab_context()
            mc.set_variable('EmagneticCalcType_Lab', 1)  # efficiency map
            mc.set_variable('SpeedMin_MotorLAB', 0)
            mc.set_variable('SpeedMax_MotorLAB', 16000)
            mc.set_variable('Speedinc_MotorLAB', 500)
            mc.set_variable('CurrentSpec_MotorLAB', 1)   # RMS
            mc.set_variable('Imax_RMS_MotorLAB', imax)
            mc.set_variable('Imin_MotorLAB', 0)
            for v in ('DCBusVoltage', 'ControlStrat_MotorLAB',
                      'ModulationIndex_MotorLAB', 'OperatingMode_Lab'):
                try:
                    print(f'  {v} =', mc.get_variable(v))
                except Exception:
                    pass

            print('  calculating efficiency map ...', flush=True)
            mc.calculate_magnetic_lab()
            res_dir = Path(str(mc.get_variable('ResultsPath_MotorLAB'))
                           .strip())
            src = res_dir / 'MotorLAB_elecdata.mat'
            if not src.exists():
                raise FileNotFoundError(f'Lab result mat not found: {src}')
            shutil.copyfile(src, out_mat)
            print('  saved:', out_mat, flush=True)
        finally:
            try:
                mc.quit()
            except Exception:
                pass
    print('done')


if __name__ == '__main__':
    main()
