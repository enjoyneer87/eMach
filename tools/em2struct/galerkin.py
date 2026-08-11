# -*- coding: utf-8 -*-
"""em2struct.galerkin — L² Galerkin 일관하중 투영 + VWP 절점력→밀도 역산.

문헌 근거 (원문 확인, README '문헌 근거' 절 참조)
--------------------------------------------------
* Pile(2021) §1.4.6.2-3: 투영은 **Ritz-Galerkin L²**(타깃 형상함수를 시험함수로)
  를 권장 — 해의 유일성, 오차의 타깃부분공간 직교성, **총력 보존 적합**.
  비정합 메시의 교차적분은 supermesh(정확·고비용) 또는 **다점 Gauss 구적**
  (저비용 — Gauss 점을 늘려도 선형계가 커지지 않음; Pile 운용치 11²=121점/요소).
* Kotter(2019) §3.1 eq.3.11: 타깃 절점기저가 **분할단위(partition of unity)** 이면
  총력 보존이 증명됨 — "보존형 vs 형상보존형 택일" 은 잘못된 구도, L² Galerkin 은
  둘 다 만족한다.
* Pile §1.4.6.1: **VWP 절점력은 Dirac 진폭이라 보간 불가** — 먼저 일관질량계
  [M]{ρ}={F} 를 풀어 연속 밀도로 복원한 뒤 투영할 것.

구현 범위
---------
- 표면요소: 3절점 삼각형(선형) / 4절점 사각형(쌍선형). SegmentTarget 의
  (S,4) 연결성(삼각형은 마지막 인덱스 반복)을 그대로 받는다.
- `L2ProjectionMapper`(등록명 'l2'): 소스 **밀도장**(TRACTION [Pa] 등)을 타깃
  요소 Gauss 점에서 평가(k-NN IDW)해 일관 절점하중 F_i = ∫ φ_i t dΓ 로 조립.
  분할단위 ⇒ ΣF = (타깃 위 소스 구적) — 소스·타깃이 같은 면을 덮으면 총력 일치.
- `consistent_mass_matrix` / `nodal_to_density`: [M]{ρ}={F} 역산(성분·열 일괄).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

from .core import ForceField, MappingResult, Quantity, TargetMesh
from .mappers import BaseMapper


# ================================================================ 요소 기하
def _split_conn(conn):
    """(S,4) 연결성 → (is_tri, 유효 절점인덱스 리스트). 마지막 반복 = 삼각형."""
    conn = np.asarray(conn, dtype=int)
    tri = conn[:, 3] == conn[:, 2]
    return tri, conn


def _tri_gauss(order: int):
    """삼각형 기준요소(면적좌표) Gauss 규칙. order: 근사 다항 차수."""
    if order <= 1:
        pts = np.array([[1/3, 1/3]]); w = np.array([0.5])
    elif order == 2:
        pts = np.array([[1/6, 1/6], [2/3, 1/6], [1/6, 2/3]])
        w = np.full(3, 1/6)
    else:  # degree 3 (4점, 음가중 없는 대안으로 6점 degree4 를 써도 됨)
        pts = np.array([[1/3, 1/3], [0.6, 0.2], [0.2, 0.6], [0.2, 0.2]])
        w = np.array([-27/96, 25/96, 25/96, 25/96])
    return pts, w


def _quad_gauss(n: int):
    """사각형 기준요소 [-1,1]² 텐서 Gauss (n×n)."""
    x, w = np.polynomial.legendre.leggauss(n)
    XI, ETA = np.meshgrid(x, x, indexing="ij")
    WI, WJ = np.meshgrid(w, w, indexing="ij")
    return np.column_stack([XI.ravel(), ETA.ravel()]), (WI * WJ).ravel()


def _tri_shape(pts):
    """삼각형 선형 형상함수 φ(ξ,η) = [1-ξ-η, ξ, η] : (G,3)."""
    xi, eta = pts[:, 0], pts[:, 1]
    return np.column_stack([1 - xi - eta, xi, eta])


def _quad_shape(pts):
    """쌍선형 형상함수 (G,4): 절점순서 (-1,-1),(1,-1),(1,1),(-1,1)."""
    xi, eta = pts[:, 0], pts[:, 1]
    return 0.25 * np.column_stack([(1 - xi) * (1 - eta), (1 + xi) * (1 - eta),
                                   (1 + xi) * (1 + eta), (1 - xi) * (1 + eta)])


def _quad_dshape(pts):
    """쌍선형 ∂φ/∂(ξ,η) : (G,4,2)."""
    xi, eta = pts[:, 0], pts[:, 1]
    d = np.empty((len(pts), 4, 2))
    d[:, 0, 0] = -0.25 * (1 - eta); d[:, 0, 1] = -0.25 * (1 - xi)
    d[:, 1, 0] = +0.25 * (1 - eta); d[:, 1, 1] = -0.25 * (1 + xi)
    d[:, 2, 0] = +0.25 * (1 + eta); d[:, 2, 1] = +0.25 * (1 + xi)
    d[:, 3, 0] = -0.25 * (1 + eta); d[:, 3, 1] = +0.25 * (1 - xi)
    return d


def _element_quadrature(verts, is_tri, n_gauss):
    """요소 하나의 (Gauss 물리좌표 (G,3), 가중·야코비안 w*J (G,), 형상값 (G,k)).

    verts : (3,3) 또는 (4,3) 절점 좌표(3D). 삼각형이면 3개만 사용.
    """
    if is_tri:
        pts, w = _tri_gauss(min(n_gauss, 3))
        phi = _tri_shape(pts)                      # (G,3)
        v0, v1, v2 = verts[0], verts[1], verts[2]
        J = np.linalg.norm(np.cross(v1 - v0, v2 - v0))   # = 2A (기준면적 0.5 포함됨)
        xg = phi @ verts[:3]                       # (G,3)
        wj = w * J
        return xg, wj, phi
    # quad: 비평면 대응 — Gauss 점별 야코비안
    pts, w = _quad_gauss(max(2, n_gauss))
    phi = _quad_shape(pts)                         # (G,4)
    dphi = _quad_dshape(pts)                       # (G,4,2)
    xg = phi @ verts                               # (G,3)
    # ∂x/∂ξ = Σ dφ_k/∂ξ · x_k
    dx_dxi = np.einsum("gk,kj->gj", dphi[:, :, 0], verts)
    dx_deta = np.einsum("gk,kj->gj", dphi[:, :, 1], verts)
    J = np.linalg.norm(np.cross(dx_dxi, dx_deta), axis=1)  # (G,)
    return xg, w * J, phi


# ================================================================ 질량행렬 / 밀도역산
def consistent_mass_matrix(nodes, segments, n_gauss: int = 3) -> sparse.csr_matrix:
    """표면 메시의 일관질량행렬 M_ij = ∫ φ_i φ_j dΓ (희소, M×M)."""
    nodes = np.asarray(nodes, float)
    tri, conn = _split_conn(segments)
    rows, cols, data = [], [], []
    for e in range(len(conn)):
        k = 3 if tri[e] else 4
        idx = conn[e, :k]
        _, wj, phi = _element_quadrature(nodes[idx], tri[e], n_gauss)
        Me = np.einsum("g,gi,gj->ij", wj, phi, phi)      # (k,k)
        for a in range(k):
            for b in range(k):
                rows.append(idx[a]); cols.append(idx[b]); data.append(Me[a, b])
    M = sparse.csr_matrix((data, (rows, cols)), shape=(len(nodes), len(nodes)))
    return M


def nodal_to_density(nodal_forces, nodes, segments, n_gauss: int = 3):
    """VWP **절점력** → 연속 **힘밀도** 복원: [M]{ρ}={F} (성분·열 일괄).

    Pile(2021) §1.4.6.1: 절점력은 그 자체로 Dirac 진폭이라 다른 메시로 보간할 수
    없다. 일관질량행렬을 풀어 밀도로 되돌린 뒤에야 투영(L² 등)이 성립한다.

    Parameters
    ----------
    nodal_forces : (M,3) 또는 (M,3,C) 절점력 [N].
    nodes        : (M,2|3) 절점 좌표 [m] (소스 EM 메시).
    segments     : (S,3|4) 표면요소 연결성(0-based, 삼각형은 마지막 반복 허용).

    Returns
    -------
    density : nodal_forces 와 같은 shape 의 밀도 [N/m²] (표면 기준).
    """
    F = np.asarray(nodal_forces, float)
    single = F.ndim == 2
    if single:
        F = F[:, :, None]
    Mmat = consistent_mass_matrix(nodes, segments, n_gauss=n_gauss).tocsc()
    Mn, _, C = F.shape
    rho = np.empty_like(F)
    # 성분×열을 한 번에: M ρ = F  (M 은 대칭 양정치)
    rhs = F.reshape(Mn, 3 * C)
    sol = spsolve(Mmat, rhs)
    sol = np.asarray(sol).reshape(Mn, 3, C)
    rho[:] = sol
    return rho[:, :, 0] if single else rho


# ================================================================ L² 투영 맵퍼
class L2ProjectionMapper(BaseMapper):
    """L² Galerkin **일관 절점하중** 투영 (문헌 권장 경로).

    타깃 표면요소 위 Gauss 구적으로  F_i = ∫_Γ φ_i(x) · t(x) dΓ  를 조립한다.
    t(x) 는 소스 밀도장(TRACTION [Pa] 등)을 Gauss 점에서 k-NN IDW 로 평가.
    타깃 형상함수가 분할단위(Σφ_i=1)이므로 **ΣF = 타깃 위 소스 구적** — 총력이
    구적 정확도로 보존된다(Kotter eq.3.11 의 성질).

    요구사항: 타깃에 **표면요소 연결성** 필요 → ``TargetMesh.segments`` 또는
    ``SegmentTarget``. 절점 클라우드만 있으면 쓸 수 없다('lsq'/'idw' 사용).

    Parameters
    ----------
    n_gauss : 요소당 Gauss 밀도(quad 는 n×n). Pile 운용치 11(=121점) 참고,
              기본 3(=9점). **점을 늘려도 선형계가 커지지 않는다**(저비용 손잡이).
    k       : 소스 평가 k-NN 이웃 수.
    power   : IDW 지수.

    소스 물리량
    -----------
    - TRACTION / FORCE_DENSITY : 그대로 밀도로 평가.
    - NODAL_FORCE : source.areas 가 있으면 F/A 로 밀도화(집중질량 근사).
      areas 도 없으면 예외 — :func:`nodal_to_density` 로 먼저 밀도 복원할 것.
    """

    name = "l2"

    def __init__(self, n_gauss: int = 3, k: int = 4, power: float = 2.0,
                 eps: float = 1e-12):
        super().__init__(conservative=False)   # 밀도장을 다룸(일관형 계열)
        self.n_gauss, self.k, self.power, self.eps = n_gauss, k, power, eps

    def fit(self, source: ForceField, target: TargetMesh) -> "L2ProjectionMapper":
        self._src, self._tgt = source, target
        segs = getattr(target, "segments", None)
        if segs is None:
            raise ValueError(
                "L2ProjectionMapper 는 타깃 표면요소 연결성이 필요합니다 — "
                "TargetMesh(segments=...) 또는 make_segment_target 을 쓰세요. "
                "절점 클라우드만 있으면 'lsq'/'idw' 를 사용하세요.")
        nodes = target.nodes
        tri, conn = _split_conn(segs)
        stree = cKDTree(source.points)
        kk = min(self.k, source.n)

        rows, cols, data = [], [], []
        for e in range(len(conn)):
            nk = 3 if tri[e] else 4
            idx = conn[e, :nk]
            xg, wj, phi = _element_quadrature(nodes[idx], tri[e], self.n_gauss)
            d, s_idx = stree.query(xg, k=kk)
            d = np.atleast_2d(d.T).T if kk == 1 else d
            s_idx = np.atleast_2d(s_idx.T).T if kk == 1 else s_idx
            wsrc = 1.0 / np.power(d + self.eps, self.power)
            wsrc /= wsrc.sum(axis=1, keepdims=True)          # (G,kk) IDW 행정규화
            # W[i, s] += Σ_g wj_g φ_i(g) wsrc_g,s
            for a in range(nk):
                contrib = (wj * phi[:, a])[:, None] * wsrc    # (G,kk)
                rows.extend([idx[a]] * (len(xg) * kk))
                cols.extend(s_idx.ravel())
                data.extend(contrib.ravel())
        from scipy import sparse as sp
        self._W = sp.csr_matrix((data, (rows, cols)),
                                shape=(target.m, source.n))
        return self

    def apply(self, source: Optional[ForceField] = None) -> MappingResult:
        src = source or self._src
        # 소스를 밀도 [N/m²] 로 정규화
        if src.quantity in (Quantity.TRACTION, Quantity.FORCE_DENSITY):
            dens = src.values
        else:  # NODAL_FORCE
            if src.areas is None:
                raise ValueError(
                    "NODAL_FORCE 소스를 L² 투영하려면 밀도가 필요합니다 — "
                    "source.areas 를 주거나(집중질량 F/A), nodal_to_density() 로 "
                    "일관 밀도를 복원해 TRACTION 필드로 만드세요. "
                    "(Pile 2021 §1.4.6.1: 절점력은 보간 불가)")
            dens = src.values / src.areas[:, None, None]
        n, _, c = dens.shape
        f = np.empty((self._tgt.m, 3, c))
        for j in range(3):
            f[:, j, :] = self._W @ dens[:, j, :]
        return MappingResult(forces=f, target=self._tgt, times=src.times,
                             mapper=self.name,
                             meta={"n_gauss": self.n_gauss, "k": self.k,
                                   "consistent_load": True})


# make_mapper('l2', ...) 로 쓸 수 있게 레지스트리에 등록
from .mappers import MAPPERS as _MAPPERS  # noqa: E402  (순환 없음: mappers→galerkin 미참조)
_MAPPERS["l2"] = L2ProjectionMapper
