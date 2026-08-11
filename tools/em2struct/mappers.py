# -*- coding: utf-8 -*-
"""em2struct.mappers — 메시투메시 맵핑 알고리즘.

설계 원칙
---------
* **맵핑 연산자는 기하만으로 fit() 에서 한 번 구성**된다. 이후 apply(values) 는
  임의 개수의 열(시간스텝·하모닉)을 한 번에 변환한다 → NVH 수백 스텝에 효율적.
* 두 패러다임:
    - 보존형(conservative): 절점력(extensive) 전달. 각 소스의 힘을 인접 타깃
      절점으로 **완전 재분배**(열 합=1) → 합력 정확 보존. LSQ 는 모멘트까지 보존.
    - 일관형(consistent): 압력/밀도(intensive) 필드를 타깃 위치로 보간(행 합=1).

맵퍼 목록
---------
NearestMapper         : 최근접(보존형/일관형 방향 선택). 기준선.
InverseDistanceMapper : k-최근접 역거리가중(PoU). 보존형 기본값(합력 보존, 빠름).
LeastSquaresMapper    : 소스별 최소norm LSQ. **합력+모멘트 정확 보존**(권장).
RBFMapper             : 방사기저함수. 일관형(부드러움). 보존은 가상일 전치로 옵션.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import sparse
from scipy.spatial import cKDTree

from .core import ForceField, MappingResult, Quantity, TargetMesh, _skew_batch


# ============================================================== base
class BaseMapper:
    """맵퍼 공통 인터페이스.

    conservative=True  → 소스 힘을 타깃으로 재분배(합력 보존). 절점력 전달용.
    conservative=False → 소스 값을 타깃으로 보간(일관형). 압력/밀도 필드용.
    """

    name = "base"

    def __init__(self, conservative: bool = True):
        self.conservative = conservative
        self._W: Optional[sparse.spmatrix] = None   # 스칼라 가중 (M x N), 성분 독립
        self._P: Optional[sparse.spmatrix] = None   # 성분결합 연산 (3M x 3N), LSQ 전용
        self._src: Optional[ForceField] = None
        self._tgt: Optional[TargetMesh] = None

    # -- 하위 클래스가 _W (또는 _P) 를 채운다 --
    def fit(self, source: ForceField, target: TargetMesh) -> "BaseMapper":
        raise NotImplementedError

    def apply(self, source: Optional[ForceField] = None) -> MappingResult:
        """fit() 로 만든 연산자를 소스 값에 적용 → 타깃 절점력."""
        src = source or self._src
        if src is None:
            raise RuntimeError("apply() 전에 fit() 하거나 source 를 넘기세요.")
        # 보존형은 등가 절점력을, 일관형은 원값을 다룬다.
        vals = src.as_nodal_forces() if self.conservative else src.values
        n, _, c = vals.shape

        if self._P is not None:  # 성분결합(LSQ)
            # _P: (3M x 3N), dof 순서 = 노드별 [x,y,z] 인접(3*node+comp)
            out = self._P @ _interleave_to_blocks(vals)  # (3M, c)
            f = _blocks_to_field(out, self._tgt.m, c)
        else:                    # 성분독립 스칼라 가중
            W = self._W
            f = np.empty((self._tgt.m, 3, c))
            for j in range(3):
                f[:, j, :] = W @ vals[:, j, :]

        if not self.conservative:
            # 일관형: 보간된 값이 압력/밀도 → 타깃 면적으로 절점력 환산.
            # 면적이 없으면 [Pa]가 [N]으로 둔갑하므로(무언의 단위오염) 명시적으로 막는다.
            if self._tgt.areas is None:
                if src.quantity != Quantity.NODAL_FORCE:
                    raise ValueError(
                        f"일관형 맵핑으로 {src.quantity.value}(intensive, 단위면적/체적당) 를 "
                        "절점력으로 환산하려면 target.areas 가 필요합니다. "
                        "TargetMesh(..., areas=...) 를 주거나, make_segment_target(...)"
                        ".as_target_mesh() 를 쓰거나, 보존형 맵퍼('lsq'/'idw')를 쓰세요.")
            else:
                f = f * self._tgt.areas[:, None, None]
        return MappingResult(
            forces=f, target=self._tgt, times=src.times, mapper=self.name,
            meta={"conservative": self.conservative, "ncols": c},
        )

    def fit_apply(self, source: ForceField, target: TargetMesh) -> MappingResult:
        return self.fit(source, target).apply(source)


# ============================================================== nearest
class NearestMapper(BaseMapper):
    """최근접 이웃. 가장 단순한 기준선.

    conservative : 각 소스를 가장 가까운 **타깃 절점 1개**로 100% 몰아줌
                   (합력 보존, 모멘트 오차 큼).
    consistent   : 각 타깃이 가장 가까운 **소스 1개** 값을 가져옴(계단형).
    """

    name = "nearest"

    def fit(self, source, target):
        self._src, self._tgt = source, target
        if self.conservative:
            tree = cKDTree(target.nodes)
            _, idx = tree.query(source.points, k=1)      # 각 소스 → 최근접 타깃
            data = np.ones(source.n)
            self._W = sparse.csr_matrix(
                (data, (idx, np.arange(source.n))), shape=(target.m, source.n)
            )
        else:
            tree = cKDTree(source.points)
            _, idx = tree.query(target.nodes, k=1)       # 각 타깃 → 최근접 소스
            data = np.ones(target.m)
            self._W = sparse.csr_matrix(
                (data, (np.arange(target.m), idx)), shape=(target.m, source.n)
            )
        return self


# ============================================================== IDW / PoU
class InverseDistanceMapper(BaseMapper):
    """k-최근접 역거리가중(Shepard). 보존형 기본값.

    보존형: 각 소스 힘을 인접 k개 타깃 절점에 역거리가중으로 재분배(열 합=1)
            → 합력 정확 보존. 국소 분배라 모멘트 오차는 작지만 0은 아님.
    일관형: 각 타깃을 인접 k개 소스로 보간(행 합=1).

    power  : 거리 지수(기본 2). power↑ 이면 최근접에 집중.
    k      : 이웃 개수(기본 4).
    eps    : 0거리 보호(자기위치 특이점 방지).
    radius : 지정 시 반경 밖 이웃 무시(초과분은 최근접 1개로 폴백).
    """

    name = "idw"

    def __init__(self, conservative=True, k=4, power=2.0, eps=1e-9, radius=None):
        super().__init__(conservative)
        self.k, self.power, self.eps, self.radius = k, power, eps, radius

    def fit(self, source, target):
        self._src, self._tgt = source, target
        if self.conservative:
            src_pts, dst_pts, nrows, ncols = target.nodes, source.points, target.m, source.n
            # 각 소스(col)를 인접 타깃(row)들로 분배 → 열정규화(열 합=1)
            tree = cKDTree(src_pts)
            self._W = self._build(tree, dst_pts, nrows, ncols, axis="col")
        else:
            tree = cKDTree(source.points)
            self._W = self._build(tree, target.nodes, target.m, source.n, axis="row")
        return self

    def _build(self, tree, query_pts, nrows, ncols, axis):
        k = min(self.k, tree.n)
        d, idx = tree.query(query_pts, k=k)
        d = np.atleast_2d(d.T).T if k == 1 else d
        idx = np.atleast_2d(idx.T).T if k == 1 else idx
        w = 1.0 / np.power(d + self.eps, self.power)
        if self.radius is not None:
            w[d > self.radius] = 0.0
            bad = w.sum(axis=1) == 0
            if bad.any():  # 반경 내 이웃 없음 → 최근접 1개 폴백
                w[bad, 0] = 1.0
        w /= w.sum(axis=1, keepdims=True)   # 각 query 행 정규화(합=1)

        q = np.repeat(np.arange(len(query_pts)), k)
        n = idx.ravel()
        val = w.ravel()
        if axis == "col":
            # query = 소스, idx = 타깃 → W[tgt, src]
            W = sparse.csr_matrix((val, (n, q)), shape=(nrows, ncols))
        else:
            # query = 타깃, idx = 소스 → W[tgt, src]
            W = sparse.csr_matrix((val, (q, n)), shape=(nrows, ncols))
        return W


# ============================================================== LSQ (force+moment)
class LeastSquaresMapper(BaseMapper):
    """소스별 최소norm 제약 최소제곱 — **합력+모멘트 동시 정확 보존**.

    각 소스 점힘 F(위치 x_s)를 인접 k개 타깃 절점 {x_i}에 실을 절점력 {f_i}로
    분배하되, ‖f‖ 최소화 + 다음 제약을 만족:
        Σ f_i = F                     (합력)
        Σ (x_i - x_s) × f_i = 0       (모멘트: 등가 합력이 x_s 에 작용)
    해석해 f = Cᵀ(CCᵀ)⁺ d, d=[F;0]. 성분이 모멘트로 결합되므로 (3M x 3N)
    희소 연산자 P 로 조립한다. 보존형 전용(절점력 전달). 회전기 NVH 권장.

    k       : 이웃 개수(기본 6, 3D 모멘트 제약 만족에 ≥3 권장).
    """

    name = "lsq"

    def __init__(self, k=6):
        super().__init__(conservative=True)
        self.k = k

    def fit(self, source, target):
        self._src, self._tgt = source, target
        N, M = source.n, target.m
        tree = cKDTree(target.nodes)
        k = min(self.k, M)
        _, nbr = tree.query(source.points, k=k)
        nbr = np.atleast_2d(nbr.T).T if k == 1 else nbr

        rows, cols, data = [], [], []
        for s in range(N):
            xs = source.points[s]
            js = nbr[s]                       # 타깃 이웃 인덱스 (k,)
            r = target.nodes[js] - xs         # (k,3)
            # 제약행렬 C (6 x 3k): 위(3)=힘, 아래(3)=모멘트
            C = np.zeros((6, 3 * k))
            for a in range(k):
                C[0:3, 3 * a:3 * a + 3] = np.eye(3)          # 힘
                C[3:6, 3 * a:3 * a + 3] = _skew_batch(r[a:a+1])[0]  # 모멘트: [r]_×
            # f = Cᵀ (CCᵀ)⁺ [I3;0] F  →  성분맵 P_s (3k x 3)
            CCt_inv = np.linalg.pinv(C @ C.T)                # (6x6)
            sel = np.zeros((6, 3)); sel[0:3, :] = np.eye(3)  # d = [F;0]
            Ps = C.T @ CCt_inv @ sel                         # (3k x 3)
            # 조립: 타깃 dof (3*js+comp) ← 소스 dof (3*s+comp)
            for a in range(k):
                for ci in range(3):
                    for cj in range(3):
                        v = Ps[3 * a + ci, cj]
                        if v != 0.0:
                            rows.append(3 * js[a] + ci)
                            cols.append(3 * s + cj)
                            data.append(v)
        self._P = sparse.csr_matrix((data, (rows, cols)), shape=(3 * M, 3 * N))
        return self


# ============================================================== RBF
class RBFMapper(BaseMapper):
    """방사기저함수(RBF) 맵핑 — **일관형 전용**(부드러운 필드 보간).

    소스 값을 RBF 로 보간하는 함수를 세우고 타깃 위치에서 평가한다. 산재한
    데이터에 매끈하다. 압력/트랙션 **필드** 전달에 적합.

    kernel : 'linear'|'tps'(thin-plate)|'gaussian'|'multiquadric'.
    eps    : gaussian/multiquadric 형상계수.

    ⚠️ **보존형(conservative=True) 미지원.** 가상일 일관 힘전달은 타깃중심 RBF
    계수행렬(M×M)이 필요해 대형 구조메시(M~1e4-1e5)에서 비현실적이다(48k면
    ~18GB). 힘(절점력) 전달에는 **`lsq`(합력+모멘트 보존, 권장)** 또는
    **`idw`(합력 보존, 빠름)** 를 쓸 것.
    """

    name = "rbf"

    def __init__(self, conservative=False, kernel="tps", eps=1.0, reg=1e-8):
        if conservative:
            raise ValueError(
                "RBFMapper 는 일관형 전용입니다(conservative=True 미지원). "
                "가상일 보존전달은 타깃중심 RBF(M×M)가 필요해 대형 메시에서 비현실적입니다. "
                "절점력 전달에는 make_mapper('lsq')(합력+모멘트 보존) 또는 "
                "make_mapper('idw')(합력 보존)를 사용하세요.")
        super().__init__(conservative)
        self.kernel, self.eps, self.reg = kernel, eps, reg

    def _phi(self, r):
        if self.kernel == "linear":
            return r
        if self.kernel == "tps":
            with np.errstate(divide="ignore", invalid="ignore"):
                out = np.where(r > 0, r * r * np.log(r + 1e-30), 0.0)
            return out
        if self.kernel == "gaussian":
            return np.exp(-(self.eps * r) ** 2)
        if self.kernel == "multiquadric":
            return np.sqrt(1.0 + (self.eps * r) ** 2)
        raise ValueError(f"unknown kernel {self.kernel}")

    def fit(self, source, target):
        self._src, self._tgt = source, target
        P = source.points
        # 소스-소스 커널로 보간 계수행렬 구성
        rss = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=-1)
        A = self._phi(rss) + self.reg * np.eye(len(P))
        # 타깃-소스 커널
        rts = np.linalg.norm(target.nodes[:, None, :] - P[None, :, :], axis=-1)
        B = self._phi(rts)
        # H = B A⁻¹  (타깃값 = H · 소스값), 행 정규화로 PoU 근사
        Ainv = np.linalg.pinv(A)
        W = B @ Ainv                      # (M,N) 일관형 보간
        rowsum = W.sum(axis=1, keepdims=True)
        rowsum[rowsum == 0] = 1.0
        W = W / rowsum
        self._W = sparse.csr_matrix(W)
        return self


# --------------------------------------------------------------- helpers
def _interleave_to_blocks(vals: np.ndarray) -> np.ndarray:
    """(N,3,C) → (3N,C) 블록순서 [x0,y0,z0, x1,y1,z1, ...] 로 평탄화."""
    n, _, c = vals.shape
    return vals.reshape(3 * n, c)  # (n,3,c) C-순서 = 노드별 xyz 인접 → 정확히 블록순서


def _blocks_to_field(flat: np.ndarray, m: int, c: int) -> np.ndarray:
    """(3M,C) 블록순서 → (M,3,C)."""
    return flat.reshape(m, 3, c)


# 편의: 이름 → 맵퍼 클래스
MAPPERS = {
    "nearest": NearestMapper,
    "idw": InverseDistanceMapper,
    "lsq": LeastSquaresMapper,
    "rbf": RBFMapper,
}


def make_mapper(name: str, **kw) -> BaseMapper:
    """이름으로 맵퍼 생성. 예: make_mapper('lsq', k=6)."""
    if name not in MAPPERS:
        raise ValueError(f"unknown mapper '{name}', choose from {list(MAPPERS)}")
    return MAPPERS[name](**kw)
