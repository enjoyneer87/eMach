# -*- coding: utf-8 -*-
"""예제: e10 형상 에어갭 Maxwell 응력(2D, θ·t) → 3D 스테이터 구조메시 하중.

실제 Maxwell 파일 없이도 돌아가는 자립 데모(합성 가진력). 흐름:
  1) 에어갭 응력 σ_r,σ_t(θ,t) 생성  — 공간하모닉(극수) × 시간(전기주파수)
  2) read_airgap_mst 로 ForceField(TRACTION)
  3) 스테이터 보어 표면 3D 구조 절점(비컨포멀) 생성
  4) extrude 로 2D 단면 → 3D 축방향 분배(사구 옵션)
  5) LSQ 맵핑(합력+모멘트 보존) → 보존 진단
  6) ANSYS Mechanical / LS-DYNA / Motion 3종 export + QA 그림
"""
from __future__ import annotations

import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..")))

from em2struct import EMStructMapper, TargetMesh, read_airgap_mst
from em2struct.viz import plot_mapping

OUT = os.environ.get("EM2S_OUT", _HERE)

# --- e10 파라미터 (OD198, bore142.5 → 에어갭반경≈0.071, stack150) ---
R_AG = 0.0712
STACK = 0.150
POLES = 8
F_ELEC = 16000 / 60 * (POLES / 2)   # 16000rpm, 8극 → 전기주파수 [Hz]

# 1) 에어갭 응력 (θ, t)
n_theta = 360
n_time = 24
theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
t = np.linspace(0, 1.0 / F_ELEC, n_time, endpoint=False)
# 반경응력: 공간 2p 하모닉 회전파 + 슬롯 하모닉. Maxwell σ_r ~ B^2/2μ0 스케일(예시값 kPa)
TH, TT = np.meshgrid(theta, t, indexing="ij")   # (n_theta, n_time)
sigma_r = (120e3 * np.cos(POLES * TH - 2 * np.pi * F_ELEC * TT)
           + 40e3 * np.cos(48 * TH - 2 * np.pi * F_ELEC * TT))   # 슬롯48 하모닉
sigma_t = 25e3 * np.sin(POLES * TH - 2 * np.pi * F_ELEC * TT)

# 2) 소스 필드
src = read_airgap_mst(theta, sigma_r, sigma_t, radius=R_AG,
                      stack_length=STACK, times=t)
print(f"source: {src.n} pts × {src.ncols} time steps, "
      f"|ΣF|(t0)={np.linalg.norm(src.total_force()[:,0]):.2f} N")

# 3) 스테이터 보어 표면 구조 절점(비컨포멀: 다른 각·축 분해능)
n_theta_s, n_axial_s = 96, 20
th_s = np.linspace(0, 2 * np.pi, n_theta_s, endpoint=False)
z_s = np.linspace(0, STACK, n_axial_s)
TS, ZS = np.meshgrid(th_s, z_s, indexing="ij")
nodes = np.column_stack([
    R_AG * np.cos(TS).ravel(), R_AG * np.sin(TS).ravel(), ZS.ravel()])
tgt = TargetMesh(nodes=nodes, node_ids=np.arange(1, len(nodes) + 1))

# 4~6) 파이프라인
z_stations = np.linspace(0, STACK, n_axial_s)
pipe = (EMStructMapper()
        .load_source(src)
        .set_target(tgt)
        .extrude(z_stations=z_stations, per_unit_length=False)  # 2D→3D
        .map("lsq", k=6)
        .report())

for solver, fname in [("ansys_mechanical", "e10_emforce.inp"),
                      ("lsdyna", "e10_emforce.k"),
                      ("ansys_motion", "e10_emforce_motion.csv")]:
    pipe.export(os.path.join(OUT, fname), solver=solver)

fig = plot_mapping(pipe.source, pipe.result,
                   os.path.join(OUT, "e10_mapping_qa.png"),
                   col=0, plane="xy",
                   title="e10 air-gap MST → stator structural mesh (LSQ, t0)")
print("QA figure:", fig)
print("done.")
