# -*- coding: utf-8 -*-
"""Lab30 재빌드 후 효율맵 3종 재계산 (run_lab_effmaps_fig15.py 의 Lab30 후속판).

구 elecdata(.mat, Lab48 기반)는 effmaps/archive_lab48/ 로 이동해 보존하고
(스킵 가드가 구본을 조용히 재사용하는 사고 방지), Lab30 사본 3개에서
Lab 효율맵을 다시 계산해 같은 파일명으로 수집한다 — plotFig15Effmaps.m 등
후속 스크립트는 무수정으로 재사용.

주의: .mot들은 2026.1(v261) 포맷 — set_motorcad_exe 로 v261 강제
(기본 탐색이 v252_SP1을 띄우면 프로세스 크래시, run_lab30_rebuild.py 참조).
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / 'map_exports' / 'e10' / 'effmaps'
ARCHIVE = OUT_DIR / 'archive_lab48'
V261_EXE = r"C:\Program Files\ANSYS Inc\v261\motorcad\MotorCAD.exe"

JOBS = [
    ('Ref', r'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_Lab30.mot', 460),
    ('SC_hyb', r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_Lab30.mot',
     920),
    ('SC_fullfea',
     r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_FullFEA_Lab30.mot', 920),
]


def main() -> None:
    import ansys.motorcad.core as pymotorcad
    pymotorcad.set_motorcad_exe(V261_EXE)

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for tag, _, _ in JOBS:
        old = OUT_DIR / f'MotorLAB_elecdata_{tag}.mat'
        if old.exists():
            shutil.move(str(old), str(ARCHIVE / old.name))
            print(f'[archive] {old.name} -> archive_lab48/', flush=True)

    for i, (tag, mot, imax) in enumerate(JOBS, 1):
        out_mat = OUT_DIR / f'MotorLAB_elecdata_{tag}.mat'
        assert Path(mot).exists(), f'.mot 없음: {mot}'
        print(f'=== [{i}/3] {tag}: {mot} (Imax {imax} A)', flush=True)
        mc = pymotorcad.MotorCAD(open_new_instance=True,
                                 enable_success_variable=False)
        try:
            mc.set_variable('MessageDisplayState', 2)
            mc.load_from_file(mot)
            if not mc.get_model_built_lab():
                raise RuntimeError(f'Lab model not built: {tag}')

            mc.set_motorlab_context()
            mc.set_variable('EmagneticCalcType_Lab', 1)  # efficiency map
            mc.set_variable('SpeedMin_MotorLAB', 0)
            mc.set_variable('SpeedMax_MotorLAB', 16000)
            mc.set_variable('Speedinc_MotorLAB', 500)
            mc.set_variable('CurrentSpec_MotorLAB', 1)   # RMS
            mc.set_variable('Imax_RMS_MotorLAB', imax)
            mc.set_variable('Imin_MotorLAB', 0)

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
