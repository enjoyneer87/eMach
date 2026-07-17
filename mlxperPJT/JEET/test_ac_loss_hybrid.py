# -*- coding: utf-8 -*-
"""ac_loss_hybrid.py 단위 테스트.

pytest로도, 단독 스크립트로도 실행 가능:
    python test_ac_loss_hybrid.py
    pytest test_ac_loss_hybrid.py -v
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ac_loss_hybrid import (  # noqa: E402
    MU0,
    SIGMA_CU_20C,
    ConductorParams,
    MotorParams,
    OperatingPoint,
    calc_gamma,
    calc_hybrid_ac_loss_1D,
    calc_hybrid_ac_loss_2D,
    calc_prox_2d_g2_prime,
    calc_proximity_effect_2D,
    calc_skin_depth,
    calc_skin_depth_modified,
    calc_skin_effect_1D,
    calc_skin_effect_1D_detail,
    eq_hyperbolic,
    extract_conductor_B,
    parse_magnetic_snapshot,
    parse_magnetic_timeseries,
    prox_coeff_g1,
    prox_coeff_g2,
    skin_effect_factor,
    speed_to_freq,
)

COND = ConductorParams(width_mm=3.7, height_mm=1.6, active_length_mm=150.0)


# ---------------------------------------------------------------------------
# 커널 검증
# ---------------------------------------------------------------------------
def test_skin_depth_textbook():
    """구리 skin depth 교과서 값: δ(50Hz)≈9.35mm, δ(1kHz)≈2.09mm"""
    d50 = float(calc_skin_depth(50.0)) * 1e3
    d1k = float(calc_skin_depth(1000.0)) * 1e3
    assert abs(d50 - 9.346) < 0.01, d50
    assert abs(d1k - 2.090) < 0.005, d1k


def test_skin_depth_modified():
    """δ' = δ·sqrt((d1+d2)/(2·d2)) (calcSkinDepthModi.m)"""
    w, h, f = 3.7e-3, 1.6e-3, 1000.0
    delta = float(calc_skin_depth(f))
    dw = float(calc_skin_depth_modified(w, h, f))
    assert abs(dw - delta * math.sqrt((w + h) / (2 * h))) < 1e-12


def test_eq_hyperbolic_series_continuity():
    """급수 근사(x<1e-2)와 직접 계산의 경계 연속성"""
    for x in (0.009, 0.0099, 0.0101, 0.011):
        o_direct = (math.sinh(2 * x) + math.sin(2 * x)) / (math.cosh(2 * x) - math.cos(2 * x))
        n2_direct = 0.5 * (math.sinh(x) - math.sin(x)) / (math.cosh(x) + math.cos(x))
        o, _, n2 = eq_hyperbolic(x)
        assert abs(o - o_direct) / o_direct < 1e-7, x
        assert abs(n2 - n2_direct) / n2_direct < 1e-6, x


def test_eq_hyperbolic_large_x_no_overflow():
    """x>710에서도 overflow 없이 점근값 반환"""
    o, n1, n2 = eq_hyperbolic(1000.0)
    assert o == 1.0 and n1 == 0.5 and n2 == 0.5


def test_skin_factor_asymptotes():
    """φ(ξ): ξ→0에서 1, ξ→∞에서 ξ, 저주파 전개 φ≈1+4ξ⁴/45"""
    assert abs(float(skin_effect_factor(1e-4)) - 1.0) < 1e-12
    xi = 50.0
    assert abs(float(skin_effect_factor(xi)) - xi) / xi < 1e-9
    xi = 0.3
    phi_series = 1.0 + 4.0 * xi**4 / 45.0
    assert abs(float(skin_effect_factor(xi)) - phi_series) / phi_series < 1e-4


# ---------------------------------------------------------------------------
# proximity 계수 검증 — 핵심 항등성
# ---------------------------------------------------------------------------
def test_g2_lowfreq_equals_mcad24():
    """[핵심] g2(non-prime) 저주파 극한 == MCAD /24 공식 (정확 항등)"""
    f = 1.0
    p_g2 = calc_proximity_effect_2D(f, 0.05, COND, method="g2", use_prime=False)
    p_24 = calc_proximity_effect_2D(f, 0.05, COND, method="mcad24")
    assert abs(p_g2 - p_24) / p_24 < 1e-6, (p_g2, p_24)


def test_g1_equals_mcad24():
    """수정된 g1 == MCAD /24 (전 주파수 항등; MATLAB pi^2 버그 수정 반영)"""
    for f in (1.0, 1000.0, 4000.0):
        p_g1 = calc_proximity_effect_2D(f, 0.05, COND, method="g1", use_prime=False)
        p_24 = calc_proximity_effect_2D(f, 0.05, COND, method="mcad24")
        assert abs(p_g1 - p_24) / p_24 < 1e-9, (f, p_g1, p_24)


def test_g2_coefficient_formula():
    """g2 = (γw/(σμ²))·(sinh γh − sin γh)/(cosh γh + cos γh) 직접 대조"""
    gw, gh = 0.8, 1.5
    expected = (gw / (SIGMA_CU_20C * MU0**2)) * (
        (math.sinh(gh) - math.sin(gh)) / (math.cosh(gh) + math.cos(gh)))
    got = float(prox_coeff_g2(gw, gh))
    assert abs(got - expected) / expected < 1e-12


def test_g1_coefficient_formula():
    """g1 = γw·γh³/(6μ²σ) 직접 대조 (calcProxg1.m 버그 수정판)"""
    gw, gh = 0.8, 1.5
    expected = gw * gh**3 / (6.0 * MU0**2 * SIGMA_CU_20C)
    got = float(prox_coeff_g1(gw, gh))
    assert abs(got - expected) / expected < 1e-12


def test_2d_combination_linearity():
    """2D 결합식의 Br²/Bθ² 분리 선형성 (calcHybridACLossWave.m:63)"""
    f = 1000.0
    p_r = calc_proximity_effect_2D(f, (0.05, 0.0), COND)
    p_t = calc_proximity_effect_2D(f, (0.0, 0.03), COND)
    p_both = calc_proximity_effect_2D(f, (0.05, 0.03), COND)
    assert abs(p_both - (p_r + p_t)) / p_both < 1e-12


def test_2d_coeff_radial_theta_swap():
    """coeff_radial=g2(γw',γh'), coeff_theta=g2(γh',γw') — w/h 스왑 대칭"""
    cr, ct = calc_prox_2d_g2_prime(3.7, 1.6, 1000.0)
    cr2, ct2 = calc_prox_2d_g2_prime(1.6, 3.7, 1000.0)
    assert abs(float(cr) - float(ct2)) / float(cr) < 1e-12
    assert abs(float(ct) - float(cr2)) / float(ct) < 1e-12


def test_rect24_vs_round128():
    """사각 /24 vs 원형 /128 공식 비율 sanity: 동일 (ωB)²·σ·L에서
    P_rect/P_round = (w·h³/24)/(π·d⁴/128)"""
    f, B = 1000.0, 0.05
    rect = ConductorParams(width_mm=2.0, height_mm=2.0, shape="rect")
    rnd = ConductorParams(width_mm=2.0, height_mm=2.0, shape="round")  # d=2mm
    p_rect = calc_proximity_effect_2D(f, B, rect, method="mcad24")
    p_rnd = calc_proximity_effect_2D(f, B, rnd, method="mcad24")
    d = 2.0e-3
    expected_ratio = (d * d**3 / 24.0) / (math.pi * d**4 / 128.0)
    assert abs(p_rect / p_rnd - expected_ratio) / expected_ratio < 1e-12


# ---------------------------------------------------------------------------
# 요구 API 검증
# ---------------------------------------------------------------------------
def test_skin_effect_1d_dc_limit():
    """저주파에서 P_skin → P_dc (φ→1)"""
    d = calc_skin_effect_1D_detail(1.0, 5.0, COND)
    assert abs(d["phi"] - 1.0) < 1e-6
    assert abs(d["P_total_W"] - d["P_dc_W"]) / d["P_dc_W"] < 1e-6


def test_skin_effect_1d_dc_value():
    """P_dc = ρ·L/A·(J·A)² 손계산 대조"""
    J = 5.0  # A/mm^2
    A = COND.w * COND.h
    I = J * 1e6 * A
    P_dc_hand = (1.0 / SIGMA_CU_20C) * COND.lactive / A * I**2
    d = calc_skin_effect_1D_detail(1.0, J, COND)
    assert abs(d["P_dc_W"] - P_dc_hand) / P_dc_hand < 1e-12
    # float 반환 버전과 일치
    assert abs(calc_skin_effect_1D(1.0, J, COND) - d["P_total_W"]) < 1e-12


def test_hybrid_1d_composition():
    """calc_hybrid_ac_loss_1D = skin(φ) + Σ큐보이드 /24, dict 구성 확인"""
    motor = MotorParams(conductor=COND, n_conductors=4)
    B = np.array([0.02, 0.03, 0.04, 0.05])
    op = OperatingPoint(freq_elec_Hz=1000.0, J_rms_A_per_mm2=5.0, B_cuboids_T=B)
    r = calc_hybrid_ac_loss_1D(motor, op)
    # proximity 손계산
    omega = 2 * math.pi * 1000.0
    p_prox_hand = float(np.sum(
        COND.lactive * COND.w * COND.h**3 * SIGMA_CU_20C * (omega * B) ** 2 / 24.0))
    assert abs(r["P_prox_W"] - p_prox_hand) / p_prox_hand < 1e-12
    # skin = n × 도체당
    p_skin_hand = 4 * calc_skin_effect_1D(1000.0, 5.0, COND)
    assert abs(r["P_skin_W"] - p_skin_hand) / p_skin_hand < 1e-12
    assert abs(r["P_ac_total_W"] - (r["P_skin_W"] + r["P_prox_W"])) < 1e-9
    assert len(r["per_cuboid_W"]) == 4


def test_speed_to_freq():
    """rpm → 전기주파수: 3000rpm, 4극쌍 → 200Hz"""
    assert speed_to_freq(3000, 4) == 200.0


def test_temperature_correction():
    """σ 온도보정: 120°C에서 저항 ~39% 증가 → 같은 J에서 P_dc 증가"""
    hot = ConductorParams(width_mm=3.7, height_mm=1.6, active_length_mm=150.0,
                          temperature_C=120.0)
    d20 = calc_skin_effect_1D_detail(1.0, 5.0, COND)
    d120 = calc_skin_effect_1D_detail(1.0, 5.0, hot)
    expected = 1.0 + 3.93e-3 * 100.0
    assert abs(d120["P_dc_W"] / d20["P_dc_W"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# 메시 파싱 + 2D 경로 (합성 파일)
# ---------------------------------------------------------------------------
def _write_synth_mesh(path: Path, n_steps: int = 1, freq: float = 1000.0,
                      br0: float = 0.05, bt0: float = 0.02):
    """MCAD 포맷 합성 메시 txt 생성.

    영역 2개: RegCode 1 = ArmatureCopper (도체, 요소 2개),
              RegCode 2 = StatorIron (비도체, 요소 1개)
    도체 중심을 +x축에 놓아 radial=x, tangential=y가 되게 함.
    n_steps>1이면 순수 정현파 Br(t)=br0·cos, Bt(t)=bt0·cos로 스텝 생성.
    """
    lines = []
    for step in range(n_steps):
        ang = 2 * math.pi * step / n_steps
        bx = br0 * math.cos(ang)   # radial = x (도체가 +x축 위)
        by = bt0 * math.cos(ang)   # tangential = y
        lines.append(f"{step + 1} Solution 1 Time index {step} Time {step * 1e-4:.6e} [s] Rotate Step {step}")
        lines.append("1 3 ElementsTable")
        lines.append("")
        lines.append("TriIndex,Node1,Node2,Node3,RegCode,Bx,By,A,J")
        lines.append("-,-,-,-,-,T,T,Wb/m,A/mm2")
        lines.append("----")
        lines.append(f"1,1,2,3,1,{bx:.8e},{by:.8e},0.0,0.0")
        lines.append(f"2,2,3,4,1,{bx:.8e},{by:.8e},0.0,0.0")
        lines.append(f"3,5,6,7,2,0.5,0.1,0.0,0.0")
        lines.append("2 7 NodesTable")
        lines.append("")
        lines.append("NodeIndex,X,Y")
        lines.append("-,mm,mm")
        lines.append("----")
        lines.append("1,50.0,0.0")
        lines.append("2,52.0,0.0")
        lines.append("3,51.0,1.0")
        lines.append("4,53.0,1.0")
        lines.append("5,60.0,0.0")
        lines.append("6,62.0,0.0")
        lines.append("7,61.0,2.0")
        lines.append("3 2 RegionsTable")
        lines.append("")
        lines.append("RegionCode,RegionName")
        lines.append("-,-")
        lines.append("----")
        lines.append("1,ArmatureCopper")
        lines.append("2,StatorIron")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_parse_synth_snapshot():
    """합성 파일 파싱: 영역/요소/이름/노드 좌표"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synth.txt"
        _write_synth_mesh(p)
        mesh = parse_magnetic_snapshot(p)
        assert len(mesh) == 2
        assert mesh[0].region_name == "ArmatureCopper"
        assert len(mesh[0].elements) == 2
        assert len(mesh[1].elements) == 1
        assert mesh.node_xy[1] == (50.0, 0.0)


def test_extract_conductor_b():
    """구리 영역 선택 + 면적가중 B, radial 좌표계 변환"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synth.txt"
        _write_synth_mesh(p, br0=0.05, bt0=0.02)
        mesh = parse_magnetic_snapshot(p)
        conds = extract_conductor_B(mesh)
        assert len(conds) == 1  # StatorIron은 패턴에서 제외
        c = conds[0]
        assert c["region_name"] == "ArmatureCopper"
        # 도체 중심이 거의 +x축 위 → Br≈Bx, Bt≈By
        assert abs(c["Br_T"] - 0.05) < 1e-3
        assert abs(c["Bt_T"] - 0.02) < 1e-3


def test_2d_peak_mode_matches_direct():
    """calc_hybrid_ac_loss_2D(peak) == calc_proximity_effect_2D 직접 호출"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synth.txt"
        _write_synth_mesh(p, br0=0.05, bt0=0.02)
        motor = MotorParams(conductor=COND)
        op = OperatingPoint(freq_elec_Hz=1000.0)
        r = calc_hybrid_ac_loss_2D(motor, op, mesh_file=str(p), mode="peak")
        assert r["n_conductors_found"] == 1
        br = r["per_conductor"][0]["Br_T"]
        bt = r["per_conductor"][0]["Bt_T"]
        p_direct = calc_proximity_effect_2D(1000.0, (br, bt), COND)
        assert abs(r["P_prox_total_W"] - p_direct) / p_direct < 1e-12


def test_2d_fft_pure_sine_matches_peak():
    """[핵심] 순수 정현파 시계열 FFT 모드 == peak 모드 (기본파 성분만)"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synth_ts.txt"
        _write_synth_mesh(p, n_steps=16, br0=0.05, bt0=0.02)
        motor = MotorParams(conductor=COND)
        op = OperatingPoint(freq_elec_Hz=1000.0)
        r_fft = calc_hybrid_ac_loss_2D(motor, op, mesh_file=str(p), mode="fft")
        # peak 모드: 스냅샷 t=0에서 B=(0.05, 0.02)=진폭 → 같은 손실이어야 함
        r_peak = calc_hybrid_ac_loss_2D(motor, op, mesh_file=str(p), mode="peak")
        rel = abs(r_fft["P_prox_total_W"] - r_peak["P_prox_total_W"]) / r_peak["P_prox_total_W"]
        assert rel < 1e-9, rel
        # 기본파 외 하모닉은 0
        P_harm = r_fft["per_conductor"][0]["P_harm_W"]
        assert P_harm[0] > 0
        assert float(np.sum(P_harm[1:])) / float(P_harm[0]) < 1e-15


def test_2d_fft_harmonic_orders():
    """cycle_fraction 반영: 1/6 주기 데이터 → 하모닉 차수 6, 12, ..."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synth_ts.txt"
        _write_synth_mesh(p, n_steps=12, br0=0.05, bt0=0.02)
        motor = MotorParams(conductor=COND)
        op = OperatingPoint(freq_elec_Hz=1000.0)
        r = calc_hybrid_ac_loss_2D(motor, op, mesh_file=str(p), mode="fft",
                                   cycle_fraction=1.0 / 6.0)
        orders = r["harmonics"]["orders"]
        assert abs(orders[0] - 6.0) < 1e-12
        assert abs(orders[1] - 12.0) < 1e-12


def test_pdf_blend_low_freq_noop():
    """PDF 블렌드: 전이주파수보다 훨씬 낮으면 배율 ≈ 1 (변화 없음)"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synth.txt"
        _write_synth_mesh(p)
        motor = MotorParams(conductor=COND)
        op = OperatingPoint(freq_elec_Hz=50.0)  # fT(h=1.6mm)≈1.7kHz보다 낮음
        r0 = calc_hybrid_ac_loss_2D(motor, op, mesh_file=str(p), mode="peak")
        r1 = calc_hybrid_ac_loss_2D(motor, op, mesh_file=str(p), mode="peak",
                                    apply_pdf_blend=True)
        rel = abs(r1["P_prox_total_W"] - r0["P_prox_total_W"]) / r0["P_prox_total_W"]
        assert rel < 0.02, rel


def test_parse_timeseries_steps():
    """시계열 파싱: 스텝 수/키 확인"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synth_ts.txt"
        _write_synth_mesh(p, n_steps=8)
        ts = parse_magnetic_timeseries(p)
        assert len(ts) == 8
        assert ts.steps == list(range(8))


# ---------------------------------------------------------------------------
# 실측 내보내기 파일이 있으면 end-to-end 확인 (없으면 skip)
# ---------------------------------------------------------------------------
def test_real_export_file_if_present():
    jeet = Path(__file__).resolve().parent
    candidates = list(jeet.glob("From*/**/Mag_*.txt")) + list(jeet.glob("From*/Mag_*.txt"))
    if not candidates:
        print("  (no real export file found - skip)")
        return
    mesh = parse_magnetic_snapshot(candidates[0])
    assert len(mesh) > 0
    n_el = sum(len(mesh[i].elements) for i in range(len(mesh)))
    assert n_el > 0
    print(f"  실측 파일 OK: {candidates[0].name}, regions={len(mesh)}, elements={n_el}")


# ---------------------------------------------------------------------------
# 단독 실행 러너
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
