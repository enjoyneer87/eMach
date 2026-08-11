# -*- coding: utf-8 -*-
"""em2struct.pipeline — 리더→(축방향)→맵퍼→라이터 원스톱 오케스트레이터.

전형적 사용:
    from em2struct import EMStructMapper
    m = (EMStructMapper()
            .load_source(field)              # ForceField (리더 산출)
            .set_target(target)              # TargetMesh
            .extrude(z_stations=[...])       # (선택) 2D→3D
            .map(mapper="lsq", k=6)          # 맵핑
            .report()                        # 보존 진단
            .export("out.inp", solver="ansys_mechanical"))
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

from .axial import extrude_field
from .core import (ConservationReport, ForceField, MappingResult, TargetMesh,
                   conservation_report)
from .mappers import BaseMapper, make_mapper
from .writers import WRITERS


class EMStructMapper:
    """전자계 가진력 → 구조 절점력 파이프라인(체이닝 API)."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.source: Optional[ForceField] = None
        self.target: Optional[TargetMesh] = None
        self.mapper: Optional[BaseMapper] = None
        self.result: Optional[MappingResult] = None
        self._report: Optional[ConservationReport] = None

    def _log(self, *a):
        if self.verbose:
            print("[em2struct]", *a, flush=True)

    # ------------------------------------------------------------- inputs
    def load_source(self, field: ForceField) -> "EMStructMapper":
        self.source = field
        self._log(f"source: n={field.n} quantity={field.quantity.value} "
                  f"ncols={field.ncols} dim={field.dim}")
        return self

    def set_target(self, target: TargetMesh) -> "EMStructMapper":
        self.target = target
        self._log(f"target: m={target.m} dim={target.dim}")
        return self

    def extrude(self, z_stations, **kw) -> "EMStructMapper":
        """2D 소스를 3D 로 축방향 분배(axial.extrude_field 래퍼)."""
        if self.source is None:
            raise RuntimeError("extrude() 전에 load_source() 하세요.")
        self.source = extrude_field(self.source, z_stations, **kw)
        self._log(f"extruded → n={self.source.n} over {len(z_stations)} axial stations")
        return self

    # ------------------------------------------------------------- mapping
    def map(self, mapper="lsq", **kw) -> "EMStructMapper":
        """맵핑 실행. mapper: 'nearest'|'idw'|'lsq'|'rbf' 또는 BaseMapper 인스턴스."""
        if self.source is None or self.target is None:
            raise RuntimeError("map() 전에 load_source()·set_target() 하세요.")
        self.mapper = mapper if isinstance(mapper, BaseMapper) else make_mapper(mapper, **kw)
        self._log(f"mapping with '{self.mapper.name}' "
                  f"(conservative={self.mapper.conservative}) ...")
        self.result = self.mapper.fit_apply(self.source, self.target)
        self._log("mapping done.")
        return self

    # ------------------------------------------------------------- diagnostics
    def report(self, about=None, echo=True) -> "EMStructMapper":
        if self.result is None:
            raise RuntimeError("report() 전에 map() 하세요.")
        self._report = conservation_report(self.source, self.result, about=about)
        if echo:
            print(self._report.summary())
        return self

    @property
    def conservation(self) -> ConservationReport:
        return self._report

    # ------------------------------------------------------------- export
    def export(self, path, solver="ansys_mechanical", **kw):
        """맵핑 결과를 솔버 파일로. solver: ansys_mechanical|lsdyna|ansys_motion."""
        if self.result is None:
            raise RuntimeError("export() 전에 map() 하세요.")
        if solver not in WRITERS:
            raise ValueError(f"unknown solver '{solver}', choose {list(WRITERS)}")
        out = WRITERS[solver](self.result, path, **kw)
        self._log(f"exported [{solver}] → {out}")
        return out


def map_forces(
    source: ForceField,
    target: TargetMesh,
    mapper: str = "lsq",
    z_stations: Optional[Sequence[float]] = None,
    extrude_kw: Optional[dict] = None,
    verbose: bool = True,
    **mapper_kw,
) -> MappingResult:
    """함수형 원샷 헬퍼. 필요시 축방향 분배 후 맵핑까지 수행, 결과 반환."""
    p = EMStructMapper(verbose=verbose).load_source(source).set_target(target)
    if z_stations is not None:
        p.extrude(z_stations, **(extrude_kw or {}))
    p.map(mapper, **mapper_kw)
    return p.result
