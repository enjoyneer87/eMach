# -*- coding: utf-8 -*-
"""em2struct 검증 — 보존 성질·라운드트립. pytest 또는 단독 실행 가능.

    python tools/em2struct/tests/test_em2struct.py     # 단독
    pytest tools/em2struct/tests/                        # pytest
"""
from __future__ import annotations

import os
import sys
import tempfile

import numpy as np

# 패키지 임포트(tools/ 를 경로에 추가)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..")))

from em2struct import (EMStructMapper, ForceField, Quantity, TargetMesh,
                       conservation_report, extrude_field, make_mapper,
                       read_airgap_mst, read_maxwell_nodal, write_ansys_mechanical,
                       write_ansys_motion, write_lsdyna)


def _synthetic(seed=0, n=200, m=120, ncols=3):
    """무작위 소스 절점력 + 다른 밀도의 타깃 메시(비컨포멀)."""
    rng = np.random.default_rng(seed)
    sp = rng.uniform(-1, 1, size=(n, 3)); sp[:, 2] *= 0.1
    sv = rng.normal(0, 1, size=(n, 3, ncols))
    src = ForceField(sp, sv, quantity=Quantity.NODAL_FORCE)
    tp = rng.uniform(-1.1, 1.1, size=(m, 3)); tp[:, 2] *= 0.1
    tgt = TargetMesh(tp, node_ids=np.arange(10, 10 + m))
    return src, tgt


# ---------------------------------------------------------------- 보존
def test_idw_conserves_force():
    src, tgt = _synthetic()
    res = make_mapper("idw", conservative=True, k=4).fit_apply(src, tgt)
    rep = conservation_report(src, res)
    assert rep.force_rel_err < 1e-10, rep.force_rel_err  # 합력 정확 보존


def test_lsq_conserves_force_and_moment():
    src, tgt = _synthetic()
    res = make_mapper("lsq", k=6).fit_apply(src, tgt)
    rep = conservation_report(src, res)
    assert rep.force_rel_err < 1e-8, rep.force_rel_err
    assert rep.moment_rel_err < 1e-6, rep.moment_rel_err  # 모멘트까지 보존


def test_lsq_beats_idw_on_moment():
    """LSQ 의 모멘트 오차가 IDW 보다 작아야(모멘트 제약 효과)."""
    src, tgt = _synthetic(seed=3)
    r_idw = make_mapper("idw", k=4).fit_apply(src, tgt)
    r_lsq = make_mapper("lsq", k=6).fit_apply(src, tgt)
    m_idw = conservation_report(src, r_idw).moment_rel_err
    m_lsq = conservation_report(src, r_lsq).moment_rel_err
    assert m_lsq < m_idw


def test_nearest_conserves_force():
    src, tgt = _synthetic()
    res = make_mapper("nearest", conservative=True).fit_apply(src, tgt)
    rep = conservation_report(src, res)
    assert rep.force_rel_err < 1e-10


# ---------------------------------------------------------------- 다열 일괄
def test_multicol_shapes():
    src, tgt = _synthetic(ncols=50)
    res = make_mapper("lsq").fit_apply(src, tgt)
    assert res.forces.shape == (tgt.m, 3, 50)


# ---------------------------------------------------------------- 리더
def test_airgap_reader_total_force():
    """균일 반경압력 → 합력 0(대칭), 순수 x 압력분포 검증."""
    nth = 360
    theta = np.linspace(0, 2*np.pi, nth, endpoint=False)
    sigma_r = np.cos(theta)               # r=1 공간하모닉 → 알짜 x 힘
    src = read_airgap_mst(theta, sigma_r, radius=0.07, stack_length=0.15)
    F = src.total_force()[:, 0]
    # 해석: ∮ σ_r cosθ · (r·L) e_r,x dθ = π r L (x성분)
    expect_x = np.pi * 0.07 * 0.15
    assert abs(F[0] - expect_x) / expect_x < 1e-2, (F[0], expect_x)


def test_maxwell_nodal_array():
    pts = np.array([[0, 0], [1, 0], [0, 1.]])
    vals = np.array([[1, 0], [0, 1], [1, 1.]])
    src = read_maxwell_nodal((pts, vals))
    assert src.n == 3 and src.ncols == 1
    assert np.allclose(src.total_force()[:, 0], [2, 2, 0])


# ---------------------------------------------------------------- 축방향
def test_extrude_conserves_total():
    rng = np.random.default_rng(1)
    sp = rng.uniform(-1, 1, (50, 2))
    sv = rng.normal(0, 1, (50, 2))
    src2d = ForceField(sp, sv, quantity=Quantity.NODAL_FORCE)
    z = np.linspace(0, 0.15, 20)
    src3d = extrude_field(src2d, z)
    f2 = src2d.total_force()[:2, 0]
    f3 = src3d.total_force()[:2, 0]
    assert np.allclose(f2, f3, rtol=1e-10), (f2, f3)  # 총력 보존
    assert src3d.n == 50 * 20


# ---------------------------------------------------------------- 라이터
def test_writers_produce_files():
    src, tgt = _synthetic(ncols=4)
    res = make_mapper("lsq").fit_apply(src, tgt)
    d = tempfile.mkdtemp()
    a = write_ansys_mechanical(res, os.path.join(d, "f.inp"))
    b = write_lsdyna(res, os.path.join(d, "f.k"))
    c = write_ansys_motion(res, os.path.join(d, "f.csv"))
    for p in ([*a] if isinstance(a, list) else [a]) + [b, c]:
        assert os.path.exists(p) and os.path.getsize(p) > 0


# ---------------------------------------------------------------- 단독 실행
if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    npass = 0
    for fn in fns:
        try:
            fn(); npass += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as e:
            print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{npass}/{len(fns)} passed")
    sys.exit(0 if npass == len(fns) else 1)
