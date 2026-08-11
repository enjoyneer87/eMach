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

import json as _json

from em2struct import (EMStructMapper, ForceField, Quantity, TargetMesh,
                       conservation_report, coverage_report, extrude_field, make_mapper,
                       make_segment_target, read_airgap_mst, read_maxwell_nodal,
                       read_motorcad_multiforce, read_vwp_force, lump_torsor,
                       write_ansys_mechanical, write_ansys_motion, write_lsdyna,
                       write_lsdyna_segment, write_ansys_remote_force,
                       consistent_mass_matrix, nodal_to_density)


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


# ---------------------------------------------------------------- Motor-CAD JSON
def test_motorcad_multiforce_json():
    """실제 Motor-CAD export 포맷(축소본) 파싱 검증: 극→직교 변환, 시간·메타."""
    nT = 4
    teeth = [{"nodeID": f"S_{i:04d}",
              "forceRValues": [10.0, 0, -10.0, 0],      # 반경력
              "forceTValues": [0.0, 5.0, 0, -5.0]}      # 접선력
             for i in range(4)]
    nodes = [{"nodeID": f"S_{i:04d}", "nodeCoord": [70.0, i * 90.0], "axialSlice": 1}
             for i in range(4)]  # 0,90,180,270도
    doc = {
        "loadPointDefinition": [{
            "speedPoint": 1500, "torquePoint": 100.0,
            "excitationData": {"torqueValues": [1] * nT,
                               "statorExcitation": teeth, "rotorExcitation": []}}],
        "statorNodeLocations": {"geometryUnitLinear": "mm", "geometryUnitAngular": "deg",
                                "statorNodes": nodes},
        "eMachineGeometry": {"rotorPoleNumber": 8, "statorLength": 150},
    }
    d = tempfile.mkdtemp(); p = os.path.join(d, "mf.json")
    _json.dump(doc, open(p, "w"))
    f = read_motorcad_multiforce(p)
    assert f.n == 4 and f.ncols == 4 and f.quantity == Quantity.NODAL_FORCE
    # 반경 70mm → 0.07m
    assert np.allclose(np.hypot(f.points[:, 0], f.points[:, 1]), 0.07, atol=1e-6)
    # 치0(θ=0): e_r=(1,0),e_t=(0,1) → t0: Fr=10→Fx=10,Fy=0
    assert np.allclose(f.values[0, :, 0], [10, 0, 0], atol=1e-9)
    # 치1(θ=90): e_r=(0,1),e_t=(-1,0) → t1: Ft=5 → Fx=-5,Fy=0
    assert np.allclose(f.values[1, :, 1], [-5, 0, 0], atol=1e-9)
    # f_elec = 1500/60*4 = 100 Hz → 시간축
    assert abs(f.meta["f_elec_Hz"] - 100.0) < 1e-6


# ---------------------------------------------------------------- VWP 리더
def test_vwp_force_density():
    """힘밀도[N/m³] × 체적 → 절점력[N]. 총력 검증."""
    pts = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0.]])
    fdens = np.array([[100, 0, 0], [0, 200, 0], [0, 0, 50.]])  # N/m^3
    vol = np.array([2.0, 3.0, 4.0])                             # m^3
    f = read_vwp_force((pts, fdens, vol), density=True)
    assert f.quantity == Quantity.FORCE_DENSITY
    nf = f.as_nodal_forces()[:, :, 0]     # density*vol
    assert np.allclose(nf, [[200, 0, 0], [0, 600, 0], [0, 0, 200]])
    assert np.allclose(f.total_force()[:, 0], [200, 600, 200])


def test_vwp_force_nodal():
    pts = np.array([[0, 0], [1, 1.]]); F = np.array([[3, 4.], [1, 0]])
    f = read_vwp_force((pts, F), density=False)
    assert f.quantity == Quantity.NODAL_FORCE
    assert np.allclose(f.total_force()[:, 0], [4, 4, 0])


# ---------------------------------------------------------------- 원격힘 라이터
def test_remote_force_writer():
    """소스 4점 → 링 타깃. pilot 4개, RBE3, F 커맨드, 파티션 전체 커버 검증."""
    # 링 타깃(z≠0, 소스는 z=0 슬라이스) → 축 불일치 자동보정 확인
    ang = np.linspace(0, 2*np.pi, 40, endpoint=False)
    tp = np.column_stack([0.07*np.cos(ang), 0.07*np.sin(ang), np.full(40, -0.13)])
    tgt = TargetMesh(tp, node_ids=np.arange(500, 540))
    sang = np.array([0, np.pi/2, np.pi, 3*np.pi/2])
    sp = np.column_stack([0.07*np.cos(sang), 0.07*np.sin(sang), np.zeros(4)])
    sv = np.zeros((4, 3, 2)); sv[:, 0, :] = 10.0  # Fx=10, 2 스텝
    src = ForceField(sp, sv, quantity=Quantity.NODAL_FORCE, times=[0., 1.])
    d = tempfile.mkdtemp(); p = os.path.join(d, "rf.inp")
    write_ansys_remote_force(src, tgt, p, scope="nearest", coupling="rbe3")
    txt = open(p, encoding="utf-8").read()
    assert txt.count("rbe3,") == 4                  # 극당 pilot 1개
    assert txt.count("\nn,900") == 4                # pilot 절점 4개
    assert "f,9000001,FX" in txt                    # 힘 적용
    assert "antype,trans" in txt                    # 다스텝 → 트랜지언트
    # 모든 타깃이 어떤 파티션엔가 배정(nsel,a 총계 ≥ 타깃수)
    assert txt.count("nsel,a,node,,") >= 40


# ---------------------------------------------------------------- 세그먼트 압력
def _flat_plate():
    """z=0 평판: 3x3 절점, 4개 사각 세그먼트. 법선 +z."""
    xs = np.array([0, 1, 2.0])
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    nodes = np.column_stack([X.ravel(), Y.ravel(), np.zeros(9)])
    # 절점 인덱스(0-based) 3x3 → 4 사각형
    idx = np.arange(9).reshape(3, 3)
    segs = []
    for i in range(2):
        for j in range(2):
            segs.append([idx[i, j], idx[i+1, j], idx[i+1, j+1], idx[i, j+1]])
    return nodes, np.array(segs)


def test_segment_target_geometry():
    nodes, segs = _flat_plate()
    st = make_segment_target(nodes, segs)
    assert st.s == 4
    assert np.allclose(st.areas, 1.0)                    # 단위 사각형
    assert np.allclose(np.abs(st.normals[:, 2]), 1.0)    # 법선 ±z


def test_segment_pressure_matches_uniform():
    """균일 +z 트랙션 1000 Pa → 각 세그먼트 압력 1000 Pa(부호관례 포함)."""
    nodes, segs = _flat_plate()
    st = make_segment_target(nodes, segs)
    # 소스: 중심점 위 균일 z-트랙션
    src = ForceField(st.centroids, np.tile([0, 0, 1000.0], (4, 1)),
                     quantity=Quantity.TRACTION, areas=st.areas,
                     normals=st.normals)
    res = make_mapper("nearest", conservative=False).fit_apply(src, st.as_target_mesh())
    d = tempfile.mkdtemp()
    p = write_lsdyna_segment(res, os.path.join(d, "seg.k"), seg_target=st, sign=1.0)
    txt = open(p, encoding="utf-8").read()
    assert "*LOAD_SEGMENT" in txt and "*DEFINE_CURVE" in txt
    # 압력 = F·n/area, F=1000*area*n → 1000 Pa
    Fn = np.einsum("sjc,sj->sc", res.forces, st.normals)
    pres = Fn[:, 0] / st.areas
    assert np.allclose(pres, 1000.0, rtol=1e-6), pres


# ------------------------------------------------- 회귀: 2026-08-11 검토 결함
def test_rbf_conservative_is_rejected():
    """RBF 보존형은 (M,N)이어야 할 연산자를 (N,M)로 만들어 크래시했다.
    가상일 보존전달은 타깃중심 RBF(M×M)라 대형메시에 비현실적 → 명시적 차단."""
    try:
        make_mapper("rbf", conservative=True)
    except ValueError as e:
        assert "lsq" in str(e)   # 대안을 안내해야 함
    else:
        raise AssertionError("RBF conservative=True 가 차단되지 않음")


def test_consistent_intensive_requires_areas():
    """일관형 + intensive(TRACTION) + target.areas 없음 → [Pa]가 [N]으로 둔갑했었다."""
    th = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    src = read_airgap_mst(th, np.cos(th) * 1e5, radius=0.07, stack_length=0.15)
    tgt = TargetMesh(np.column_stack([0.07*np.cos(th), 0.07*np.sin(th), np.zeros(24)]))
    try:
        make_mapper("idw", conservative=False).fit_apply(src, tgt)
    except ValueError as e:
        assert "areas" in str(e)
    else:
        raise AssertionError("면적 없는 일관형 intensive 맵핑이 통과됨(단위 오염)")
    # areas 를 주면 정상 동작
    tgt2 = TargetMesh(tgt.nodes, areas=np.full(24, 1e-3))
    r = make_mapper("idw", conservative=False).fit_apply(src, tgt2)
    assert r.forces.shape == (24, 3, 1)


def test_multistep_has_no_stale_loads():
    """스텝별로 0을 생략하면 MAPDL F 는 이전 값을 유지 → 잔류하중.
    활성절점의 전 성분을 매 스텝 기록해야 한다."""
    pts = np.array([[0, 0, 0], [1, 0, 0.]])
    v = np.zeros((2, 3, 2)); v[0, 0, 0] = 100.0; v[1, 0, 1] = 50.0
    res = make_mapper("nearest").fit_apply(
        ForceField(pts, v, times=[0., 1.]), TargetMesh(pts, node_ids=[11, 22]))
    d = tempfile.mkdtemp(); p = os.path.join(d, "t.inp")
    write_ansys_mechanical(res, p)
    txt = open(p, encoding="utf-8").read()
    blocks = txt.split("! ---- load step")
    counts = [b.count("\nf,") for b in blocks[1:]]
    assert len(set(counts)) == 1, f"스텝별 F 개수 불일치 {counts} → 잔류하중 위험"
    # step2 에서 노드11 은 명시적으로 0 이어야 함
    assert "f,11,FX,0.00000000e+00" in blocks[2]


def test_cerig_syntax():
    """CERIG,MASTE,SLAVE,Ldof — 3번째는 Ldof. 컴포넌트명을 넣으면 MAPDL 실패."""
    ang = np.linspace(0, 2*np.pi, 12, endpoint=False)
    tp = np.column_stack([0.07*np.cos(ang), 0.07*np.sin(ang), np.zeros(12)])
    src = ForceField(np.array([[0.07, 0, 0], [-0.07, 0, 0.]]), np.ones((2, 3, 1)))
    d = tempfile.mkdtemp(); p = os.path.join(d, "c.inp")
    write_ansys_remote_force(src, TargetMesh(tp, node_ids=np.arange(1, 13)), p,
                             coupling="cerig")
    for line in open(p, encoding="utf-8"):
        if line.startswith("cerig"):
            parts = line.strip().split(",")
            assert not any(pp.startswith("_RF_SLV") for pp in parts), \
                f"컴포넌트명이 Ldof 자리에 들어감: {line.strip()}"


def test_coverage_report_detects_concentration():
    """보존은 정확해도 하중이 소수 절점에 뭉치는 결함을 잡는 지표."""
    rng = np.random.default_rng(5)
    src = ForceField(rng.uniform(-1, 1, (10, 3)), rng.normal(0, 1, (10, 3)))
    tgt = TargetMesh(rng.uniform(-1, 1, (1000, 3)))          # 소스≪타깃
    res = make_mapper("lsq", k=4).fit_apply(src, tgt)
    cov = coverage_report(res)
    assert cov.n_target == 1000
    assert cov.n_loaded <= 40                                 # 10소스×4이웃
    assert cov.coverage < 0.05                                # 커버리지 경고 영역
    assert "⚠️" in cov.summary()


def test_lump_torsor_conserves_and_recovers_moment():
    """분포 힘 → 치별 토서. 합력 보존 + 합력만으론 사라지는 모멘트 복원.
    (Pile 2021 §3.4.2: 합력만 lumping 시 ~4 dB 손실, 토서로 <1 dB 회복.)"""
    nth = 240
    th = np.linspace(0, 2*np.pi, nth, endpoint=False)
    f = read_airgap_mst(th, 120e3*np.cos(8*th), 25e3*np.sin(8*th),
                        radius=0.0713, stack_length=0.15)
    ang = np.linspace(0, 2*np.pi, 24, endpoint=False)
    centers = np.column_stack([0.0713*np.cos(ang), 0.0713*np.sin(ang)])
    C, F, M = lump_torsor(f, centers)
    assert F.shape == (24, 3, 1) and M.shape == (24, 3, 1)
    # 합력 보존
    assert np.allclose(F.sum(axis=0)[:, 0], f.total_force()[:, 0], atol=1e-9)
    # 분포가 만드는 모멘트는 0 이 아니어야(합력만 쓰면 이게 버려짐)
    assert np.linalg.norm(M, axis=1).max() > 0
    # 라이터가 모멘트를 실제로 기록하는지
    d = tempfile.mkdtemp(); p = os.path.join(d, "rf.inp")
    src = ForceField(C, F)
    tp = np.column_stack([0.0713*np.cos(np.linspace(0, 2*np.pi, 100, endpoint=False)),
                          0.0713*np.sin(np.linspace(0, 2*np.pi, 100, endpoint=False)),
                          np.zeros(100)])
    write_ansys_remote_force(src, TargetMesh(tp, node_ids=np.arange(1, 101)), p,
                             moments=M)
    txt = open(p, encoding="utf-8").read()
    assert ",MX," in txt and ",MY," in txt and ",MZ," in txt


# --------------------------------------------- L² Galerkin / VWP 밀도 (문헌 경로)
def _plate(nx=3, ny=3, sx=1.0, sy=1.0):
    """z=0 평판 절점/사각요소. 반환 (nodes(N,3), segs(S,4))."""
    xs = np.linspace(0, sx * (nx - 1), nx)
    ys = np.linspace(0, sy * (ny - 1), ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    nodes = np.column_stack([X.ravel(), Y.ravel(), np.zeros(nx * ny)])
    idx = np.arange(nx * ny).reshape(nx, ny)
    segs = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            segs.append([idx[i, j], idx[i+1, j], idx[i+1, j+1], idx[i, j+1]])
    return nodes, np.array(segs)


def test_l2_partition_of_unity_conserves_total():
    """균일 트랙션 → ΣF = t·A 가 **기계정밀**(Kotter eq.3.11 분할단위 성질)."""
    nodes, segs = _plate()
    tgt = TargetMesh(nodes, segments=segs)
    # 소스: 성긴 균일 트랙션(값이 상수면 IDW 도 정확)
    sp = np.array([[0.3, 0.3, 0], [1.5, 0.7, 0], [0.8, 1.6, 0.]])
    t0 = np.array([0, 0, 1000.0])
    src = ForceField(sp, np.tile(t0, (3, 1)), quantity=Quantity.TRACTION,
                     areas=np.ones(3))
    res = make_mapper("l2", n_gauss=3).fit_apply(src, tgt)
    F = res.forces[:, :, 0]
    assert np.allclose(F.sum(axis=0), [0, 0, 1000.0 * 4.0], rtol=1e-12), F.sum(axis=0)
    # 일관하중 패턴: 중앙절점 = p·1.0 (인접 4요소 × A/4)
    center = 4  # (1,1) of 3x3
    assert abs(F[center, 2] - 1000.0 * 1.0) < 1e-9


def test_l2_requires_segments():
    nodes, _ = _plate()
    src = ForceField(nodes[:3], np.ones((3, 3)), quantity=Quantity.TRACTION)
    try:
        make_mapper("l2").fit(src, TargetMesh(nodes))
    except ValueError as e:
        assert "segments" in str(e) or "표면요소" in str(e)
    else:
        raise AssertionError("연결성 없는 타깃이 통과됨")


def test_l2_nodal_force_needs_density():
    """절점력 소스 + areas 없음 → Pile §1.4.6.1 근거로 명시적 거부."""
    nodes, segs = _plate()
    src = ForceField(nodes[:4], np.ones((4, 3)))       # NODAL_FORCE, areas 없음
    m = make_mapper("l2").fit(src, TargetMesh(nodes, segments=segs))
    try:
        m.apply()
    except ValueError as e:
        assert "nodal_to_density" in str(e)
    else:
        raise AssertionError("절점력 직접 투영이 허용됨(보간 불가 원칙 위반)")


def test_nodal_to_density_roundtrip():
    """ρ(선형장) → F=Mρ → 역산 → ρ 복원(기계정밀). [M]{ρ}={F} 검증."""
    nodes, segs = _plate(4, 4, 0.5, 0.5)
    rho = np.column_stack([2.0 + 3.0 * nodes[:, 0],
                           1.0 - 0.5 * nodes[:, 1],
                           np.full(len(nodes), 7.0)])
    M = consistent_mass_matrix(nodes, segs)
    F = np.column_stack([M @ rho[:, j] for j in range(3)])
    rec = nodal_to_density(F, nodes, segs)
    assert np.allclose(rec, rho, rtol=1e-10), np.abs(rec - rho).max()
    # 질량행렬 자체 검증: 행합 = 절점 담당면적, 총합 = 전체면적
    assert abs(M.sum() - 1.5 * 1.5) < 1e-12


def test_l2_on_curved_quad():
    """원통 곡면(비평면 quad) 야코비안: 균일 반경압력 합력 ≈ 해석적분."""
    R, L = 0.07, 0.1
    th = np.linspace(-0.4, 0.4, 9)
    zz = np.linspace(0, L, 5)
    TH, ZZ = np.meshgrid(th, zz, indexing="ij")
    nodes = np.column_stack([R*np.cos(TH).ravel(), R*np.sin(TH).ravel(), ZZ.ravel()])
    idx = np.arange(9*5).reshape(9, 5)
    segs = [[idx[i, j], idx[i+1, j], idx[i+1, j+1], idx[i, j+1]]
            for i in range(8) for j in range(4)]
    tgt = TargetMesh(nodes, segments=np.array(segs))
    # 소스: 세밀한 원호 위 반경 트랙션 p0
    ths = np.linspace(-0.45, 0.45, 60)
    sp = np.column_stack([R*np.cos(ths), R*np.sin(ths), np.full(60, L/2)])
    p0 = 5e4
    tvec = p0 * np.column_stack([np.cos(ths), np.sin(ths), np.zeros(60)])
    src = ForceField(sp, tvec, quantity=Quantity.TRACTION)
    F = make_mapper("l2", n_gauss=3).fit_apply(src, tgt).forces[:, :, 0]
    # 해석: Fx = p0 L R ∫cosθ dθ = p0 L R (sin0.4-sin(-0.4))
    Fx_ref = p0 * L * R * 2 * np.sin(0.4)
    assert abs(F.sum(axis=0)[0] - Fx_ref) / Fx_ref < 5e-3, (F.sum(axis=0)[0], Fx_ref)


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
