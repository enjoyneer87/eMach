# -*- coding: utf-8 -*-
"""em2struct.readers — 소스 전자계 가진력 → 공통 ForceField.

세 형식 모두 지원:
  1) read_maxwell_nodal  : Maxwell 가상일 nodal/element 힘 벡터 (2D/3D 메시).
  2) read_airgap_mst     : 에어갭 Maxwell 응력 σ_r,σ_t (θ, t) — NVH 표준.
  3) read_motorcad_nvh   : Motor-CAD NVH 모듈 스테이터 치(teeth) 힘.

파일 스키마는 도구/버전마다 다르므로, 각 리더는 **열이름 매핑(column map)** 이나
in-memory 배열을 받도록 유연하게 설계했다. 실제 export 헤더가 다르면 col_map 만
바꾸면 된다(코드 수정 불필요). 모든 리더는 SI 단위(m, N, Pa) 로 정규화한다.
"""
from __future__ import annotations

import csv
import os
from typing import Optional, Sequence

import numpy as np

from .core import ForceField, Quantity


# ------------------------------------------------------------------ CSV util
def _read_table(path: str, delimiter=None, skip_header=0):
    """헤더 있는 수치 CSV/TSV → (headers[list], data[ndarray]). 구분자 자동추정."""
    with open(path, "r", encoding="utf-8-sig") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        if delimiter is None:
            delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
        for _ in range(skip_header):
            fh.readline()
        reader = csv.reader(fh, delimiter=delimiter)
        rows = [r for r in reader if r and not r[0].lstrip().startswith("#")]
    headers = [h.strip() for h in rows[0]]
    # 첫 행이 숫자면 헤더 없음
    try:
        float(headers[0]); headers = [f"c{i}" for i in range(len(rows[0]))]; body = rows
    except ValueError:
        body = rows[1:]
    data = np.array([[_to_float(x) for x in r] for r in body], dtype=float)
    return headers, data


def _to_float(x):
    x = x.strip()
    if x in ("", "nan", "NaN", "NA"):
        return np.nan
    return float(x)


def _pick(headers, data, names, required=True, default=None):
    """열이름 후보 중 첫 매칭 열 반환(대소문자 무시). names 는 문자열 또는 리스트."""
    if isinstance(names, str):
        names = [names]
    low = [h.lower() for h in headers]
    for nm in names:
        if nm.lower() in low:
            return data[:, low.index(nm.lower())]
    if required:
        raise KeyError(f"열 {names} 을(를) 헤더 {headers} 에서 찾지 못했습니다.")
    return None if default is None else np.full(len(data), default, dtype=float)


# ============================================================ 1) Maxwell nodal
def read_maxwell_nodal(
    src,
    col_map: Optional[dict] = None,
    quantity: Quantity = Quantity.NODAL_FORCE,
    scale_len: float = 1.0,
    scale_force: float = 1.0,
    delimiter=None,
) -> ForceField:
    """Maxwell(또는 임의 FE) 절점/요소 힘 벡터 파일 → ForceField.

    기대 열(기본): x,y[,z], Fx,Fy[,Fz]. 헤더가 다르면 col_map 지정.
    예: col_map={'x':'X [mm]','y':'Y [mm]','Fx':'Force_x','Fy':'Force_y'}

    Parameters
    ----------
    src        : CSV 경로(str) 또는 (points, values) 튜플/배열.
    col_map    : 열이름 커스텀 매핑.
    quantity   : 기본 NODAL_FORCE(절점력). FORCE_DENSITY 로도 읽을 수 있음.
    scale_len  : 좌표 단위→m 환산(mm 면 1e-3).
    scale_force: 힘 단위→N 환산.
    """
    if not isinstance(src, str):  # in-memory (points, values)
        pts, vals = src
        pts = np.asarray(pts, float) * scale_len
        vals = np.asarray(vals, float) * scale_force
        return ForceField(points=pts, values=vals, quantity=quantity,
                          meta={"source": "maxwell_nodal(array)"})

    headers, data = _read_table(src, delimiter=delimiter)
    cm = col_map or {}
    x = _pick(headers, data, cm.get("x", ["x", "X [mm]", "X", "c0"]))
    y = _pick(headers, data, cm.get("y", ["y", "Y [mm]", "Y", "c1"]))
    z = _pick(headers, data, cm.get("z", ["z", "Z [mm]", "Z"]), required=False, default=0.0)
    fx = _pick(headers, data, cm.get("Fx", ["fx", "Force_x", "Fx", "FX"]))
    fy = _pick(headers, data, cm.get("Fy", ["fy", "Force_y", "Fy", "FY"]))
    fz = _pick(headers, data, cm.get("Fz", ["fz", "Force_z", "Fz", "FZ"]),
               required=False, default=0.0)
    pts = np.column_stack([x, y, z]) * scale_len
    vals = np.column_stack([fx, fy, fz]) * scale_force
    return ForceField(points=pts, values=vals, quantity=quantity,
                      meta={"source": os.path.basename(src)})


# ============================================================ 2) air-gap MST
def read_airgap_mst(
    theta,
    sigma_r,
    sigma_t=None,
    radius: float = None,
    stack_length: float = 1.0,
    times=None,
    axial_z: float = 0.0,
    sigma_z=None,
    theta_in_deg: bool = False,
) -> ForceField:
    """에어갭 Maxwell 응력텐서 → 원주 트랙션 ForceField (NVH 표준 입력).

    각 각도 θ 위치에 반경압력 σ_r(→ e_r)과 접선압력 σ_t(→ e_θ)를 트랙션 벡터로
    싣고, 대표 면적 = radius·Δθ·stack_length 로 둔다. 시간축 지원(σ 가 (Nθ,T)).

    Parameters
    ----------
    theta        : (Nθ,) 각도(라디안, 등간격 가정). theta_in_deg=True 면 도.
    sigma_r      : (Nθ,) 또는 (Nθ,T) 반경 Maxwell 응력 [Pa].
    sigma_t      : (Nθ,) 또는 (Nθ,T) 접선 응력 [Pa](선택).
    radius       : 에어갭 응력 계산 반경 [m]. 필수.
    stack_length : 적층 길이 [m](2D→면적 환산).
    times        : (T,) 시간값(선택).
    axial_z      : 이 단면의 축방향 위치 [m](2D 이면 0).
    sigma_z      : 축방향 응력(3D 케이스, 선택).

    Returns
    -------
    ForceField(quantity=TRACTION), points 는 반경 radius 원 위의 점,
    areas 채워짐 → 이후 as_nodal_forces() 로 절점력 환산 가능.
    """
    if radius is None:
        raise ValueError("radius(에어갭 반경, m) 는 필수입니다.")
    theta = np.asarray(theta, float).ravel()
    if theta_in_deg:
        theta = np.deg2rad(theta)
    nth = len(theta)
    sr = np.atleast_2d(np.asarray(sigma_r, float))
    if sr.shape[0] != nth:
        sr = sr.T
    T = sr.shape[1]
    st = (np.atleast_2d(np.asarray(sigma_t, float)) if sigma_t is not None
          else np.zeros_like(sr))
    if st.shape[0] != nth:
        st = st.T
    sz = (np.atleast_2d(np.asarray(sigma_z, float)) if sigma_z is not None
          else np.zeros_like(sr))
    if sz.shape[0] != nth:
        sz = sz.T

    er = np.column_stack([np.cos(theta), np.sin(theta), np.zeros(nth)])   # 반경 단위
    et = np.column_stack([-np.sin(theta), np.cos(theta), np.zeros(nth)])  # 접선 단위
    ez = np.array([0.0, 0.0, 1.0])
    # 트랙션 벡터 (Nθ,3,T)
    trac = (er[:, :, None] * sr[:, None, :]
            + et[:, :, None] * st[:, None, :]
            + ez[None, :, None] * sz[:, None, :])
    pts = radius * er + np.array([0, 0, axial_z])
    # 대표 면적: 등간격 가정 → radius * (2π/Nθ) * stack_length
    dtheta = 2 * np.pi / nth
    areas = np.full(nth, radius * dtheta * stack_length)
    normals = er
    return ForceField(points=pts, values=trac, quantity=Quantity.TRACTION,
                      areas=areas, normals=normals, times=times,
                      meta={"source": "airgap_mst", "radius": radius,
                            "stack_length": stack_length, "ncols": T})


# ============================================================ 3) Motor-CAD NVH
def read_motorcad_nvh(
    src,
    col_map: Optional[dict] = None,
    stack_length: float = 1.0,
    scale_len: float = 1e-3,
    representation: str = "cartesian",
    delimiter=None,
) -> ForceField:
    """Motor-CAD NVH 스테이터 치(teeth) 힘 export → ForceField(NODAL_FORCE).

    Motor-CAD NVH 모듈은 스테이터 치별 시공간 힘(반경/접선, 또는 x/y)을 내보낸다.
    이 리더는 치 중심좌표 + (시간스텝 또는 하모닉별) 힘 성분 테이블을 읽는다.

    기대 스키마(기본, representation='cartesian'):
        x, y, Fx_t0, Fy_t0, Fx_t1, Fy_t1, ...  (치 한 행, 시간스텝이 열로 반복)
    또는 representation='polar':
        x, y, Fr_t0, Ft_t0, Fr_t1, Ft_t1, ...  (반경/접선 → 위치각으로 x/y 변환)

    파일 형식이 다르면 col_map 으로 좌표열을, 나머지 힘열은 자동으로 짝지어
    (Fx,Fy) 또는 (Fr,Ft) 쌍으로 해석한다. 실제 헤더에 맞게 아래 규칙만 조정하라.

    Parameters
    ----------
    src            : CSV 경로 또는 dict(points=..., F=... (Nteeth,3,T)).
    representation : 'cartesian'(Fx,Fy) | 'polar'(Fr,Ft, 치 위치각 기준).
    scale_len      : 좌표 단위→m(Motor-CAD mm 기본 1e-3).
    stack_length   : 참고 메타(치 힘은 이미 총력으로 가정).
    """
    if isinstance(src, dict):  # in-memory
        pts = np.asarray(src["points"], float) * scale_len
        F = np.asarray(src["F"], float)
        return ForceField(points=pts, values=F, quantity=Quantity.NODAL_FORCE,
                          times=src.get("times"),
                          meta={"source": "motorcad_nvh(dict)"})

    headers, data = _read_table(src, delimiter=delimiter)
    cm = col_map or {}
    x = _pick(headers, data, cm.get("x", ["x", "X", "tooth_x", "c0"])) * scale_len
    y = _pick(headers, data, cm.get("y", ["y", "Y", "tooth_y", "c1"])) * scale_len
    pts = np.column_stack([x, y, np.zeros(len(x))])

    # 좌표열 인덱스 제외한 나머지를 힘 성분으로 (2개씩 짝: a,b 반복)
    low = [h.lower() for h in headers]
    used = set()
    for key in ("x", "y"):
        for cand in cm.get(key, [key]):
            if cand.lower() in low:
                used.add(low.index(cand.lower())); break
    force_cols = [i for i in range(data.shape[1]) if i not in used]
    if len(force_cols) % 2 != 0:
        raise ValueError("힘 성분 열 개수가 홀수입니다. (a,b) 쌍이어야 함.")
    T = len(force_cols) // 2
    fa = data[:, force_cols[0::2]]   # (Nteeth, T)  Fx 또는 Fr
    fb = data[:, force_cols[1::2]]   # (Nteeth, T)  Fy 또는 Ft

    if representation == "polar":
        ang = np.arctan2(y, x)
        er = np.column_stack([np.cos(ang), np.sin(ang)])
        et = np.column_stack([-np.sin(ang), np.cos(ang)])
        Fx = er[:, 0:1] * fa + et[:, 0:1] * fb
        Fy = er[:, 1:2] * fa + et[:, 1:2] * fb
    else:
        Fx, Fy = fa, fb
    F = np.stack([Fx, Fy, np.zeros_like(Fx)], axis=1)  # (Nteeth,3,T)
    return ForceField(points=pts, values=F, quantity=Quantity.NODAL_FORCE,
                      meta={"source": os.path.basename(src),
                            "stack_length": stack_length, "ncols": T})
