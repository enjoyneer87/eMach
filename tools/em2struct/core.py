# -*- coding: utf-8 -*-
"""em2struct.core — 공통 데이터 모델 + 보존 진단.

전자계(Maxwell/Motor-CAD) 가진력을 구조해석(Mechanical/Motion/LS-DYNA) 메시로
넘기는 파이프라인의 뼈대. 모든 리더는 서로 다른 소스 형식을 아래 ``ForceField``
하나로 정규화하고, 모든 라이터는 ``MappingResult`` 하나를 받아 솔버별로 내보낸다.

핵심 개념
---------
- 물리량 종류(``Quantity``)에 따라 맵핑 패러다임이 갈린다:
    * NODAL_FORCE  (extensive, 단위 N)      → **보존형** 맵핑(합력/모멘트 보존)
    * TRACTION     (intensive, 단위 Pa, 면적 있음) → **일관형** 보간 후 면적 적분
    * FORCE_DENSITY(intensive, 단위 N/m^2·N/m^3)   → 일관형 보간 후 체적/면적 적분
- 시간/하모닉 의존성은 ``values`` 의 마지막 축(``ncols``)으로 표현한다. 맵핑
  연산자는 기하만으로 만들어지므로 열(시간스텝·하모닉)이 몇 개든 한 번에 적용된다.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


class Quantity(str, enum.Enum):
    """소스 힘의 물리적 종류. 맵핑 패러다임 선택에 사용된다."""

    NODAL_FORCE = "nodal_force"      # extensive, [N]        — 보존형
    TRACTION = "traction"            # intensive, [Pa]=[N/m^2] 표면응력 — 일관형+면적
    FORCE_DENSITY = "force_density"  # intensive, [N/m^3]/[N/m^2] 체적력 — 일관형+체적


def _as3d(pts: np.ndarray) -> np.ndarray:
    """(N,2) 또는 (N,3) 좌표를 항상 (N,3) 으로 (2D 는 z=0). 내부 계산 통일용."""
    pts = np.asarray(pts, dtype=float)
    if pts.ndim != 2 or pts.shape[1] not in (2, 3):
        raise ValueError(f"points must be (N,2) or (N,3), got {pts.shape}")
    if pts.shape[1] == 2:
        pts = np.column_stack([pts, np.zeros(len(pts))])
    return pts


def _as3d_vec(vec: np.ndarray, ncols: int) -> np.ndarray:
    """힘/응력 값을 (N,3,ncols) 로 정규화. 입력 허용: (N,2|3), (N,2|3,ncols)."""
    vec = np.asarray(vec, dtype=float)
    if vec.ndim == 2:
        vec = vec[:, :, None]
    if vec.ndim != 3:
        raise ValueError(f"values must be (N,dim) or (N,dim,ncols), got {vec.shape}")
    n, d, c = vec.shape
    if d == 2:  # 2D → z 성분 0
        vec = np.concatenate([vec, np.zeros((n, 1, c))], axis=1)
    elif d != 3:
        raise ValueError(f"value dim must be 2 or 3, got {d}")
    return vec


@dataclass
class ForceField:
    """정규화된 소스 가진력 필드 (전자계 측).

    Parameters
    ----------
    points : (N,2|3) 샘플 위치 [m]. 2D 는 xy 평면(z=0).
    values : (N,2|3) 또는 (N,2|3,ncols) 값. 마지막 축은 시간스텝/하모닉.
             NODAL_FORCE 는 [N], TRACTION 은 [Pa], FORCE_DENSITY 는 [N/m^3].
    quantity : 물리량 종류. 맵핑 패러다임을 결정.
    areas : (N,) 각 샘플의 대표 면적 [m^2]. TRACTION → 절점력 환산에 필요.
    volumes : (N,) 각 샘플의 대표 체적 [m^3]. FORCE_DENSITY 체적력용.
    normals : (N,2|3) 표면 법선(단위). 스칼라 압력→벡터 트랙션 환산에 사용.
    times : (ncols,) 열별 시간값 [s] 또는 하모닉 라벨(선택).
    dim : 원본 차원(2 또는 3). 출력 포맷팅용.
    meta : 자유 메타데이터(소스 파일, 회전속도, rpm 등).
    """

    points: np.ndarray
    values: np.ndarray
    quantity: Quantity = Quantity.NODAL_FORCE
    areas: Optional[np.ndarray] = None
    volumes: Optional[np.ndarray] = None
    normals: Optional[np.ndarray] = None
    times: Optional[np.ndarray] = None
    dim: int = 3
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        raw = np.asarray(self.points)
        self.dim = 2 if (raw.ndim == 2 and raw.shape[1] == 2) else 3
        self.points = _as3d(self.points)
        self.values = _as3d_vec(self.values, ncols=None)
        if len(self.values) != len(self.points):
            raise ValueError(
                f"points({len(self.points)}) and values({len(self.values)}) mismatch"
            )
        self.quantity = Quantity(self.quantity)
        if self.areas is not None:
            self.areas = np.asarray(self.areas, dtype=float).ravel()
        if self.volumes is not None:
            self.volumes = np.asarray(self.volumes, dtype=float).ravel()
        if self.normals is not None:
            self.normals = _as3d(self.normals)
        if self.times is not None:
            self.times = np.asarray(self.times).ravel()

    # ------------------------------------------------------------------ props
    @property
    def n(self) -> int:
        return len(self.points)

    @property
    def ncols(self) -> int:
        """시간스텝/하모닉 개수."""
        return self.values.shape[2]

    @property
    def is_extensive(self) -> bool:
        """절점력(extensive)이면 True → 보존형 맵핑 대상."""
        return self.quantity == Quantity.NODAL_FORCE

    # ------------------------------------------------------------- transforms
    def as_nodal_forces(self) -> np.ndarray:
        """소스를 등가 절점력 (N,3,ncols) [N] 으로 환산.

        - NODAL_FORCE  : 그대로.
        - TRACTION     : value[Pa] * area[m^2].
        - FORCE_DENSITY: value * volume (있으면) 아니면 * area.
        """
        if self.quantity == Quantity.NODAL_FORCE:
            return self.values
        if self.quantity == Quantity.TRACTION:
            if self.areas is None:
                raise ValueError("TRACTION → nodal force 환산에 areas 가 필요합니다.")
            return self.values * self.areas[:, None, None]
        # FORCE_DENSITY
        w = self.volumes if self.volumes is not None else self.areas
        if w is None:
            raise ValueError("FORCE_DENSITY 환산에 volumes 또는 areas 가 필요합니다.")
        return self.values * w[:, None, None]

    def total_force(self) -> np.ndarray:
        """열별 합력 (3,ncols) [N]."""
        return self.as_nodal_forces().sum(axis=0)

    def total_moment(self, about: Optional[np.ndarray] = None) -> np.ndarray:
        """기준점(about, 기본 원점) 둘레 합모멘트 (3,ncols) [N·m]."""
        about = np.zeros(3) if about is None else _as3d(np.atleast_2d(about))[0]
        f = self.as_nodal_forces()               # (N,3,C)
        r = self.points - about                  # (N,3)
        # M = Σ r × f  (열별)
        m = np.einsum("nij,njc->nic", _skew_batch(r), f)  # (N,3,C)
        return m.sum(axis=0)


@dataclass
class TargetMesh:
    """구조해석 타깃 메시(하중을 실을 절점/세그먼트).

    Parameters
    ----------
    nodes : (M,2|3) 절점 좌표 [m].
    node_ids : (M,) 솔버 절점 ID. 없으면 1..M.
    segments : (S,k) 표면 세그먼트(면요소)의 절점 인덱스(0-based). LS-DYNA
               *LOAD_SEGMENT, 면적 적분에 사용(선택).
    areas : (M,) 절점 담당 면적 [m^2](선택, 일관형 압력→절점력 환산·진단용).
    """

    nodes: np.ndarray
    node_ids: Optional[np.ndarray] = None
    segments: Optional[np.ndarray] = None
    areas: Optional[np.ndarray] = None
    dim: int = 3

    def __post_init__(self):
        raw = np.asarray(self.nodes)
        self.dim = 2 if (raw.ndim == 2 and raw.shape[1] == 2) else 3
        self.nodes = _as3d(self.nodes)
        if self.node_ids is None:
            self.node_ids = np.arange(1, len(self.nodes) + 1)
        else:
            self.node_ids = np.asarray(self.node_ids).ravel()
        if self.segments is not None:
            self.segments = np.asarray(self.segments, dtype=int)
        if self.areas is not None:
            self.areas = np.asarray(self.areas, dtype=float).ravel()

    @property
    def m(self) -> int:
        return len(self.nodes)


@dataclass
class SegmentTarget:
    """표면 세그먼트(면요소) 타깃 — LS-DYNA *LOAD_SEGMENT 압력용.

    맵핑은 세그먼트 **중심점**(``centroids``)에 대해 수행하고(공유절점 이중계산
    회피), 라이터는 ``conn_ids``(각 세그먼트 코너의 솔버 절점 ID)로 카드를 쓴다.

    centroids : (S,3) 세그먼트 중심점 [m] — 맵핑 타깃 노드.
    conn_ids  : (S,4) 세그먼트 코너 절점 ID. 삼각형은 마지막 ID 반복.
    areas     : (S,) 세그먼트 면적 [m^2].
    normals   : (S,3) 세그먼트 외향 단위 법선.
    """

    centroids: np.ndarray
    conn_ids: np.ndarray
    areas: np.ndarray
    normals: np.ndarray

    @property
    def s(self) -> int:
        return len(self.centroids)

    def as_target_mesh(self) -> "TargetMesh":
        """중심점을 절점으로 하는 TargetMesh(맵핑 입력용). areas 전달."""
        return TargetMesh(nodes=self.centroids,
                          node_ids=np.arange(1, self.s + 1), areas=self.areas)


def make_segment_target(nodes, segments, node_ids=None) -> SegmentTarget:
    """구조 표면 절점·연결성 → SegmentTarget(중심점·면적·법선·코너ID).

    Parameters
    ----------
    nodes    : (M,2|3) 절점 좌표 [m].
    segments : (S,3|4) 각 세그먼트의 절점 **인덱스**(0-based). 삼각형/사각형 혼용 시
               사각형 기준으로 패딩(삼각형은 마지막 인덱스 반복).
    node_ids : (M,) 솔버 절점 ID. 없으면 1..M.

    법선·면적은 Newell 법(비평면 사각형에도 강건)으로 계산.
    """
    nodes = _as3d(nodes)
    segments = np.asarray(segments, dtype=int)
    M = len(nodes)
    ids = np.arange(1, M + 1) if node_ids is None else np.asarray(node_ids).ravel()
    if segments.ndim != 2:
        raise ValueError("segments must be (S,k)")
    S, k = segments.shape

    centroids = np.zeros((S, 3))
    areas = np.zeros(S)
    normals = np.zeros((S, 3))
    conn = np.zeros((S, 4), dtype=np.int64)
    for i in range(S):
        verts = nodes[segments[i]]                 # (k,3)
        centroids[i] = verts.mean(axis=0)
        # Newell 법선(면적가중) : n = Σ (v_j × v_{j+1})
        nvec = np.zeros(3)
        for j in range(k):
            a = verts[j]; b = verts[(j + 1) % k]
            nvec += np.cross(a, b)
        area = 0.5 * np.linalg.norm(nvec)
        areas[i] = area
        normals[i] = nvec / (np.linalg.norm(nvec) + 1e-30)
        seg_ids = list(ids[segments[i]])
        while len(seg_ids) < 4:                     # 삼각형 → 4번째 반복
            seg_ids.append(seg_ids[-1])
        conn[i] = seg_ids[:4]
    return SegmentTarget(centroids=centroids, conn_ids=conn, areas=areas, normals=normals)


@dataclass
class MappingResult:
    """맵핑 산출: 타깃 절점력 + 진단.

    forces : (M,3,ncols) 타깃 절점력 [N].
    target : TargetMesh.
    times : (ncols,) 시간/하모닉 라벨(선택).
    mapper : 사용한 맵퍼 이름.
    meta : 진단·설정 메타.
    """

    forces: np.ndarray
    target: TargetMesh
    times: Optional[np.ndarray] = None
    mapper: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def ncols(self) -> int:
        return self.forces.shape[2]

    def total_force(self) -> np.ndarray:
        return self.forces.sum(axis=0)

    def total_moment(self, about: Optional[np.ndarray] = None) -> np.ndarray:
        about = np.zeros(3) if about is None else _as3d(np.atleast_2d(about))[0]
        r = self.target.nodes - about
        m = np.einsum("nij,njc->nic", _skew_batch(r), self.forces)
        return m.sum(axis=0)


# --------------------------------------------------------------------- utils
def _skew_batch(r: np.ndarray) -> np.ndarray:
    """(N,3) 위치벡터들 → (N,3,3) skew 행렬 (r× 연산자). M = Σ [r]_× f."""
    n = len(r)
    s = np.zeros((n, 3, 3))
    s[:, 0, 1] = -r[:, 2]; s[:, 0, 2] = r[:, 1]
    s[:, 1, 0] = r[:, 2];  s[:, 1, 2] = -r[:, 0]
    s[:, 2, 0] = -r[:, 1]; s[:, 2, 1] = r[:, 0]
    return s


@dataclass
class ConservationReport:
    """소스 대비 타깃 합력/합모멘트 보존 진단(열별 최댓값 기준 요약)."""

    src_force: np.ndarray      # (3,C)
    tgt_force: np.ndarray      # (3,C)
    src_moment: np.ndarray     # (3,C)
    tgt_moment: np.ndarray     # (3,C)
    force_abs_err: np.ndarray  # (3,C)
    force_rel_err: float       # 스칼라 요약
    moment_abs_err: np.ndarray
    moment_rel_err: float

    def summary(self) -> str:
        return (
            "── em2struct 보존 진단 ──────────────────────────────\n"
            f"  합력 소스(col0)  : [{self.src_force[0,0]:+.4g}, "
            f"{self.src_force[1,0]:+.4g}, {self.src_force[2,0]:+.4g}] N\n"
            f"  합력 타깃(col0)  : [{self.tgt_force[0,0]:+.4g}, "
            f"{self.tgt_force[1,0]:+.4g}, {self.tgt_force[2,0]:+.4g}] N\n"
            f"  합력 상대오차(max over cols) : {self.force_rel_err:.3e}\n"
            f"  합모멘트 상대오차(max)       : {self.moment_rel_err:.3e}\n"
            "─────────────────────────────────────────────────────"
        )


def conservation_report(
    source: ForceField, result: MappingResult, about: Optional[np.ndarray] = None
) -> ConservationReport:
    """소스 필드와 맵핑 결과의 합력·합모멘트 보존을 비교한다.

    합력은 항상 등가 절점력 기준으로 비교(TRACTION 은 면적 적분 후). 모멘트는
    동일 기준점 둘레로 계산.

    상대오차 분모는 **총 힘 처리량(L1: Σ‖f_i‖)** 을 쓴다. 회전 반경압력파처럼
    알짜 합력이 ≈0 인 경우 순 합력을 분모로 쓰면 비가 폭발하므로, 분배된 힘의
    총 규모로 정규화해야 물리적으로 의미가 있다. 보존형 맵퍼는 ~1e-12(기계정밀),
    일관형은 유한값이 나온다.
    """
    sf = source.total_force()
    tf = result.total_force()
    sm = source.total_moment(about)
    tm = result.total_moment(about)

    # 총 힘 처리량(열별): Σ_i ‖f_i^src‖ — 알짜합력이 0이어도 건전한 스케일
    src_nf = source.as_nodal_forces()                      # (N,3,C)
    f_throughput = np.linalg.norm(src_nf, axis=1).sum(axis=0)   # (C,)
    f_throughput[f_throughput == 0] = 1.0
    f_abs = np.abs(tf - sf)
    f_rel = float(np.max(np.linalg.norm(tf - sf, axis=0) / f_throughput))

    # 모멘트 스케일: Σ_i ‖r_i × f_i^src‖
    about3 = np.zeros(3) if about is None else _as3d(np.atleast_2d(about))[0]
    r = source.points - about3
    m_i = np.einsum("nij,njc->nic", _skew_batch(r), src_nf)     # (N,3,C)
    m_throughput = np.linalg.norm(m_i, axis=1).sum(axis=0)      # (C,)
    m_throughput[m_throughput == 0] = 1.0
    m_abs = np.abs(tm - sm)
    m_rel = float(np.max(np.linalg.norm(tm - sm, axis=0) / m_throughput))

    return ConservationReport(sf, tf, sm, tm, f_abs, f_rel, m_abs, m_rel)
