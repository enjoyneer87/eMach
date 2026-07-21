# -*- coding: utf-8 -*-
"""커널 차원수 연구: 1-D vs 2-D 확산해 (같은 MS-FEA 여기 기준).

결론(REPRODUCE.md 주의 20): 손실 대리 총비 TS/1-D=14.5, TS/2-D=1.00.

원문 설명:
2-D 확산해로 풀면 크기가 맞는가?

현재 Fig 2 의 재구성은 1-D (반경방향만, 양 면의 접선 H 경계조건).
여기서는 같은 MS-FEA 여기(渦전류 없는 A_z)를 경계조건으로 주되
막대 단면 전체에서 **2-D** 확산 방정식을 푼다:

    (lap - j w mu sigma) A = -mu sigma E0,   A|_bd = A_MS|_bd
    J_z = sigma(-j w A + E0),   E0 는 순전류 I_net 을 맞추도록 결정

그리고 TS-FEA 의 실측 Je 와 주기 RMS 로 비교한다.
1-D 와 2-D 를 같은 여기·같은 기준으로 나란히 놓는 것이 목적.
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")
from jeet_acloss_rbf import (iter_mes_blocks, slot_conductor_codes,
                             hybrid_je_at_points, conductor_je_2d,
                             plot_fig2_kernel_comparison,
                             make_fig2_kernel_gif)

F = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10\fields"
TS = os.path.join(F, "Magnetic_Ref_ARCHIVE_460A_36deg_OnLoadTorque.txt")
HY = os.path.join(F, "Magnetic_Ref_Hybrid_ARCHIVE_460A_36deg_full_"
                     "OnLoadTorque.txt")
SLOT, FREQ, SIGMA, MU0 = 1, 1066.67, 4.709e7, 4e-7 * np.pi
# SC 는 운전점별 ACLossCalcExport 폴더에서 뽑은 것을 쓴다 ---
# 속도스윕 백업(FEResultsData_backup*)은 TS 0.7031 deg/step 128블록,
# Hybrid 2.0 deg/step 47블록으로 회전 격자가 달라 짝지을 수 없다.
SC = os.path.join(F, "Magnetic_SC_OP920A_36deg_OnLoadTorque.txt")
SC_HY = os.path.join(F, "Magnetic_SC_Hybrid_OP920A_36deg_"
                        "OnLoadTorque.txt")
# model -> (TS-FEA, MS-FEA, 파일태그, 전기주파수)
SOURCES = {"Ref": (TS, HY, "Ref", 1066.67),
           "SC": (SC, SC_HY, "SC", 1066.67)}
CU_H, CU_W = 1.686, 3.711            # [mm] .mot Copper_Height/Width
NX, NY = 40, 26                      # 접선 x 반경
EVERY = 4                            # 128블록 중 매 4번째만 (32스텝)
W = 2 * np.pi * FREQ


def main():
    acc = {}
    nstep = 0
    for (bi, p_ts), (_, p_ms) in zip(iter_mes_blocks(TS), iter_mes_blocks(HY)):
        if (bi - 1) % EVERY:
            continue
        codes_ts = sorted(slot_conductor_codes(p_ts, SLOT),
                          key=lambda c: np.hypot(
                              p_ts['x_mm'][p_ts['reg'] == c],
                              p_ts['y_mm'][p_ts['reg'] == c]).mean())
        codes_ms = sorted(slot_conductor_codes(p_ms, SLOT),
                          key=lambda c: np.hypot(
                              p_ms['x_mm'][p_ms['reg'] == c],
                              p_ms['y_mm'][p_ms['reg'] == c]).mean())
        m_all = np.isin(p_ts['reg'], codes_ts)
        xy = np.column_stack([p_ts['x_mm'][m_all], p_ts['y_mm'][m_all]])
        je1d = hybrid_je_at_points(p_ms, xy, FREQ, slot_id=SLOT,
                                   signed=False, thickness_mm=CU_H) / 1e6
        for L, (ct, cm) in enumerate(zip(codes_ts, codes_ms)):
            d = acc.setdefault(L, {'ts': 0.0, 'd1': 0.0, 'd2': 0.0, 'n': 0})
            mt = p_ts['reg'] == ct
            d['ts'] += float(((p_ts['je_am2'][mt] / 1e6) ** 2).mean())
            sub = p_ts['reg'][m_all] == ct
            d['d1'] += float(((je1d[sub] / np.sqrt(2)) ** 2).mean())
            i_net = float(p_ms['jval'][cm]) * 6.180e-6      # A (도체면적)
            J2 = conductor_je_2d(p_ms, cm, FREQ, CU_W, CU_H,
                                 i_net_a=i_net,
                                 nx=NX, ny=NY)['je'] / 1e6
            d['d2'] += float((np.abs(J2) ** 2).mean() / 2.0)
            d['n'] += 1
        nstep += 1
    print('스텝 %d개 (매 %d블록)' % (nstep, EVERY))
    print('\n%-6s %10s %10s %10s | %8s %8s'
          % ('layer', 'TS_rms', '1D_rms', '2D_rms', 'TS/1D', 'TS/2D'))
    t, a, b = [], [], []
    for L in sorted(acc):
        d = acc[L]
        rt = np.sqrt(d['ts'] / d['n'])
        r1 = np.sqrt(d['d1'] / d['n'])
        r2 = np.sqrt(d['d2'] / d['n'])
        t.append(rt)
        a.append(r1)
        b.append(r2)
        print('%-6d %10.2f %10.2f %10.2f | %8.2f %8.2f'
              % (L, rt, r1, r2, rt / r1, rt / r2))
    t, a, b = np.array(t), np.array(a), np.array(b)
    print('\n쏠림 기울기(공극/슬롯바닥):  TS %.3f   1-D %.3f   2-D %.3f'
          % (t[0] / t[-1], a[0] / a[-1], b[0] / b[-1]))
    print('손실 대리 총비  TS/1D = %.2f   TS/2D = %.2f'
          % ((t**2).sum() / (a**2).sum(), (t**2).sum() / (b**2).sum()))


def figures(model='Ref'):
    """커널 비교 PNG/GIF. 배치 규칙대로 저장.

    ``model='Ref'`` 또는 ``'SC'`` --- SC 는 스케일 변형체에서도 TS 와
    2-D 가 비슷한지 확인하기 위한 것.
    """
    ts, hy, tag, freq = SOURCES[model]
    figdir = r"E:\KDH\Overleaf\JEET-2024_rev1"
    drive = os.path.join(r"J:\내 드라이브", "EveryMotor_JEET_data",
                         "results")

    # 4패널 (진단용, 전체 비교)
    plot_fig2_kernel_comparison(
        ts, hy, os.path.join(figdir, "fig", "fig2_%s_kernel_dim.png" % tag),
        slot_id=SLOT, freq_hz=freq, every=EVERY,
        copper_w_mm=CU_W, copper_h_mm=CU_H,
        out_json=os.path.join(drive, "fig2_%s_kernel_dim.json" % tag))

    # 2패널 TS vs 2-D (논문 후보)
    plot_fig2_kernel_comparison(
        ts, hy, os.path.join(figdir, "fig", "fig2_%s_ts_vs_2d.png" % tag),
        slot_id=SLOT, freq_hz=freq, every=EVERY,
        copper_w_mm=CU_W, copper_h_mm=CU_H, panels=('ts', '2d'),
        out_json=os.path.join(drive, "fig2_%s_ts_vs_2d.json" % tag))

    make_fig2_kernel_gif(
        ts, hy, os.path.join(drive, "fig2_%s_ts_vs_2d.gif" % tag),
        slot_id=SLOT, freq_hz=freq, every=2,
        copper_w_mm=CU_W, copper_h_mm=CU_H, panels=('ts', '2d'))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--figures', action='store_true',
                    help='표 대신 PNG/GIF 생성')
    ap.add_argument('--model', default='Ref', choices=sorted(SOURCES))
    a = ap.parse_args()
    if a.figures:
        figures(a.model)
    else:
        main()
