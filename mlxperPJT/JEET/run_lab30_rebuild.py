# -*- coding: utf-8 -*-
"""LAB 포화 모델 30점(6I x 5gamma) 통일 재빌드 — 본문 'MS-FEA 30점'과 격자 서사 일원화.

원본 .mot는 불변. Lab30 사본 3개를 만들어 그리드 모드(6전류 x 5gamma)로 재빌드:
  Ref        refModel\e10Turn6V261.mot               -> e10Turn6V261_Lab30.mot
  SC hyb     SLFEA\e10Turn6V261SLFEA_Lab48.mot       -> e10Turn6V261SLFEA_Lab30.mot
  SC fullfea SLFEA\e10Turn6V261SLFEA_FullFEA_LAB.mot -> ..._FullFEA_Lab30.mot

30점 배치 = 균등 격자 {0..Imax_pk 6레벨} x {0,22.5,45,67.5,90}deg — SC의 역사적
커스텀 리스트와 동일 좌표이며 I_SC = 2 x I_Ref (k_r=2)라 상사 사상 하에 30/30
전 노드 일치 (Fig 9 보간 무개입 비교 유지).

주의(2026-07-30 1차 실패의 교훈):
  - .mot들은 2026.1.1.1(v261)로 작성됨. pymotorcad 기본 탐색이 v252_SP1을 띄우면
    빌드 중 프로세스가 죽는다(RPC 10054) -> set_motorcad_exe로 v261 강제.
  - 커스텀 포인트 모드(SatModelPoints=1) RPC 배열 주입 대신, Lab48 재빌드로 검증된
    그리드 모드(=2)를 쓴다. 균등 격자라 결과 좌표는 동일하다.
"""
from __future__ import annotations

import io
import re
import shutil
import sys
import time
from pathlib import Path

V261_EXE = r"C:\Program Files\ANSYS Inc\v261\motorcad\MotorCAD.exe"

JOBS = [  # (tag, 원본, Lab30 사본, Imax_pk 기대값)
    ('Ref',
     r'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot',
     r'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_Lab30.mot', 650.538),
    ('SC_hyb',
     r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_Lab48.mot',
     r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_Lab30.mot', 1301.076),
    ('SC_fullfea',
     r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_FullFEA_LAB.mot',
     r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_FullFEA_Lab30.mot',
     1301.076),
]
GAMMAS = [0.0, 22.5, 45.0, 67.5, 90.0]


# 포화 격자에 종속된 Lab 빌드 테이블(재빌드로 head-30 갱신 확인됨) —
# 저장 시 남는 구 48격자 잔류 항목(idx>=30)을 잘라내야 MATLAB 추출기의
# 크기=30 필터가 통과한다. Phase_*(권선, 정당한 48항목)·Fe/LossModel
# (별도 손실 빌드, 이번에 미갱신)은 절대 건드리지 않는다.
SAT_GRID_KEYS = (
    'SatModel_Is_Lab', 'SatModel_Gamma_Lab', 'SatModel_Speed_Lab',
    'PsiDModel_Lab', 'PsiQModel_Lab', 'TorqueRippleModel_Lab',
    'MagLossArray_MotorLAB',
    'Sync_psiDModel_Lab', 'Sync_psiQModel_Lab', 'Sync_IsSatModel_Lab',
    'Sync_GammaSatModel_Lab', 'Sync_IrSatModel_Lab',
)


def parse_grid(mot: str, n_active: int = 30):
    """저장된 .mot에서 활성(인덱스 < n_active) 포화 격자를 파싱."""
    s = io.open(mot, encoding='latin-1').read()
    n = re.search(r'SatModelBuildPoints_Lab=(\d+)', s)
    iss = sorted({round(float(v), 3) for i, v in
                  re.findall(r'SatModel_Is_Lab\[(\d+)\]=([\d.eE+-]+)', s)
                  if int(i) < n_active})
    gam = sorted({round(float(v), 3) for i, v in
                  re.findall(r'SatModel_Gamma_Lab\[(\d+)\]=([\d.eE+-]+)', s)
                  if int(i) < n_active})
    stale = len(re.findall(r'SatModel_Is_Lab\[(\d+)\]=', s)) - n_active
    return (int(n.group(1)) if n else -1), iss, gam, stale


def sanitize_stale(mot: str, n_active: int = 30) -> int:
    """포화 격자 테이블의 잔류 항목(idx >= n_active) 라인 제거."""
    s = io.open(mot, encoding='latin-1', newline='').read()
    pat = re.compile(
        r'^(?:' + '|'.join(SAT_GRID_KEYS) + r')\[(\d+)\]=[^\r\n]*\r?\n',
        re.M)
    removed = 0

    def repl(m):
        nonlocal removed
        if int(m.group(1)) >= n_active:
            removed += 1
            return ''
        return m.group(0)

    s2 = pat.sub(repl, s)
    if removed:
        io.open(mot, 'w', encoding='latin-1', newline='').write(s2)
    return removed


def build_one(pymotorcad, tag, src, dst, imax_pk, n_cur=6, n_gam=5):
    if Path(dst).exists():
        n0, iss0, gam0, stale0 = parse_grid(dst)
        if n0 == 30 and len(iss0) == 6 and len(gam0) == 5:
            if stale0 > 0:
                rm = sanitize_stale(dst)
                print(f'[{tag}] 기존 빌드 재사용 + 잔류 {rm}라인 정리', flush=True)
            else:
                print(f'[{tag}] 기존 빌드 재사용 (정리 완료 상태)', flush=True)
            verify(tag, dst, imax_pk)
            return
    if not Path(dst).exists():
        shutil.copyfile(src, dst)
        print(f'[{tag}] copy: {Path(dst).name}', flush=True)

    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    try:
        mc.set_variable('MessageDisplayState', 2)
        mc.load_from_file(dst)
        mc.set_motorlab_context()
        mc.clear_model_build_lab()
        mc.set_variable('SatModelPoints_MotorLAB', 2)      # 2 = 표준 격자
        mc.set_variable('ModelBuildPoints_Current_Lab', n_cur)
        mc.set_variable('ModelBuildPoints_Gamma_Lab', n_gam)
        for v in ('SatModelPoints_MotorLAB', 'ModelBuildPoints_Current_Lab',
                  'ModelBuildPoints_Gamma_Lab', 'CurrentSpec_MotorLAB',
                  'MaxModelCurrent_RMS_MotorLAB', 'CalcTypeCuLoss_MotorLAB'):
            try:
                print(f'  {v} = {mc.get_variable(v)}', flush=True)
            except Exception:
                pass
        mc.save_to_file(dst)                               # 설정 선저장

        print(f'[{tag}] BuildModel_Lab 시작 ...', flush=True)
        t0 = time.time()
        mc.build_model_lab()
        print(f'[{tag}] 빌드 완료 ({(time.time() - t0) / 60:.1f}분)',
              flush=True)
        if not mc.get_model_built_lab():
            raise RuntimeError(f'{tag}: Lab 빌드 실패 (GetModelBuilt_Lab=0)')
        mc.save_to_file(dst)
        print(f'[{tag}] 저장: {dst}', flush=True)
    finally:
        try:
            mc.quit()
        except Exception:
            pass

    rm = sanitize_stale(dst)
    print(f'[{tag}] 잔류 항목 정리: {rm}라인 제거', flush=True)
    verify(tag, dst, imax_pk)


def verify(tag, dst, imax_pk):
    n, iss, gam, stale = parse_grid(dst)
    print(f'[{tag}] 격자 확인: N={n}, I({len(iss)})={iss}, '
          f'G({len(gam)})={gam}, stale={stale}', flush=True)
    assert n == 30, f'{tag}: 총 점수 {n} != 30'
    assert len(iss) == 6 and len(gam) == 5, \
        f'{tag}: 격자 방향 확인 필요 (I {len(iss)} x G {len(gam)})'
    assert abs(max(iss) - imax_pk) < 1.0, \
        f'{tag}: Imax {max(iss)} != {imax_pk}'
    assert all(any(abs(g - t) < 0.1 for g in gam) for t in GAMMAS), \
        f'{tag}: gamma 격자 {gam} != {GAMMAS}'
    assert stale == 0, f'{tag}: 잔류 {stale}항목 미정리'


def main() -> int:
    import ansys.motorcad.core as pymotorcad

    assert Path(V261_EXE).exists(), f'v261 exe 없음: {V261_EXE}'
    pymotorcad.set_motorcad_exe(V261_EXE)
    for tag, src, dst, imax in JOBS:
        assert Path(src).exists(), f'원본 없음: {src}'
        build_one(pymotorcad, tag, src, dst, imax)
    print('ALL BUILDS DONE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
