# -*- coding: utf-8 -*-
"""em2struct.axial — 2D 전자계 단면 힘을 3D 구조 메시로 축방향 분배.

2D Maxwell 은 xy 단면만 푼다. 3D 구조해석에는 이 단면 힘을 스택 길이에 걸쳐
축(z) 방향으로 분배해야 한다. skew(사구), 세그먼트 적층, 엔드이펙트 가중을
axial_profile 로 표현한다.
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence, Union

import numpy as np

from .core import ForceField, Quantity


def extrude_field(
    field2d: ForceField,
    z_stations: Sequence[float],
    weights: Optional[Sequence[float]] = None,
    per_unit_length: bool = False,
    stack_length: Optional[float] = None,
    skew_rate: float = 0.0,
) -> ForceField:
    """2D ForceField(z=0 단면)를 z_stations 축위치들로 복제·분배.

    Parameters
    ----------
    field2d         : 2D 소스(모든 점 z=0). NODAL_FORCE 또는 TRACTION.
    z_stations      : (L,) 축방향 스테이션 위치 [m].
    weights         : (L,) 각 스테이션 가중. None 이면 트리뷰터리 길이 기반 균등.
                      합=1 로 정규화되어 총력 보존(per_unit_length=False 일 때).
    per_unit_length : True 면 field2d 가 '단위길이당' 값(N/m 등) → 각 스테이션에
                      트리뷰터리 길이 dz 를 곱한다(총력 = 적분).
    stack_length    : per_unit_length 검증/기본가중용 총 길이 [m].
    skew_rate       : 사구율 [rad/m]. 각 스테이션에서 xy 를 z*skew_rate 만큼 회전
                      (스큐 로터/스테이터). 0 이면 직선 적층.

    Returns
    -------
    3D ForceField : 점수 = N(2D)·L, z 성분 포함.
    """
    z = np.asarray(z_stations, float).ravel()
    L = len(z)
    n = field2d.n

    # 축방향 트리뷰터리 길이(중점법)
    if L == 1:
        dz = np.array([stack_length if stack_length else 1.0])
    else:
        edges = np.empty(L + 1)
        edges[1:-1] = 0.5 * (z[:-1] + z[1:])
        edges[0] = z[0] - (z[1] - z[0]) / 2
        edges[-1] = z[-1] + (z[-1] - z[-2]) / 2
        dz = np.diff(edges)

    if weights is None:
        w = dz / dz.sum() if not per_unit_length else dz
    else:
        w = np.asarray(weights, float).ravel()
        if not per_unit_length:
            w = w / w.sum()

    pts_all, vals_all = [], []
    areas_all = [] if field2d.areas is not None else None
    normals_all = [] if field2d.normals is not None else None

    base_xy = field2d.points[:, :2]
    vals = field2d.values  # (n,3,C)
    for zi, wi in zip(z, w):
        if skew_rate:
            ang = zi * skew_rate
            c, s = np.cos(ang), np.sin(ang)
            R = np.array([[c, -s], [s, c]])
            xy = base_xy @ R.T
            # 힘 벡터도 동일 회전(면내 x,y)
            vv = vals.copy()
            vv[:, 0, :] = c * vals[:, 0, :] - s * vals[:, 1, :]
            vv[:, 1, :] = s * vals[:, 0, :] + c * vals[:, 1, :]
        else:
            xy = base_xy
            vv = vals
        pts = np.column_stack([xy, np.full(n, zi)])
        pts_all.append(pts)
        vals_all.append(vv * wi)
        if areas_all is not None:
            # 면적 스케일: TRACTION 은 값 아닌 면적에 축길이 반영
            areas_all.append(field2d.areas * (wi if per_unit_length else 1.0))
        if normals_all is not None:
            normals_all.append(field2d.normals)

    out = ForceField(
        points=np.vstack(pts_all),
        values=np.concatenate(vals_all, axis=0),
        quantity=field2d.quantity,
        areas=(np.concatenate(areas_all) if areas_all is not None else None),
        normals=(np.vstack(normals_all) if normals_all is not None else None),
        times=field2d.times,
        meta={**field2d.meta, "extruded": True, "n_axial": L, "skew_rate": skew_rate},
    )
    return out
