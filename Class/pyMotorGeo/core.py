"""
pyMotorGeo.core
===============
핵심 데이터 클래스 및 유틸리티 함수.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class EntityInfo:
    """DXF 엔티티 하나의 핵심 정보를 담는 구조체."""
    etype: str               # LINE, ARC, CIRCLE, LWPOLYLINE, POLYLINE, ...
    layer: str
    points: List[Tuple[float, float]]   # 대표 좌표들
    radius: Optional[float] = None      # CIRCLE/ARC
    center: Optional[Tuple[float, float]] = None
    start_angle: Optional[float] = None  # ARC (degrees)
    end_angle: Optional[float] = None
    is_closed: bool = False              # LWPOLYLINE/POLYLINE/CIRCLE 닫힘 여부
    raw: object = field(default=None, repr=False)

    @property
    def coords(self) -> List[Tuple[float, float]]:
        """points의 별칭 (호환성)."""
        return self.points

    @property
    def r_min(self) -> float:
        """원점에서 가장 가까운 점까지의 거리."""
        return min(math.hypot(x, y) for x, y in self.points) if self.points else float('inf')

    @property
    def r_max(self) -> float:
        """원점에서 가장 먼 점까지의 거리."""
        return max(math.hypot(x, y) for x, y in self.points) if self.points else 0.0

    @property
    def angle_deg(self) -> float:
        """대표 좌표의 평균 각도(deg, 0~360)."""
        if not self.points:
            return 0.0
        angles = [math.degrees(math.atan2(y, x)) % 360 for x, y in self.points]
        return float(np.mean(angles))
    
    def get_area(self, origin: Tuple[float, float] = (0.0, 0.0)) -> float:
        """닫힌 폴리라인의 면적을 계산 (Shoelace formula)."""
        if not self.is_closed or len(self.points) < 3:
            return 0.0
        pts = self.points
        n = len(pts)
        area = 0.0
        for i in range(n):
            x1, y1 = pts[i][:2]
            x2, y2 = pts[(i + 1) % n][:2]
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0


@dataclass
class StatorRotorSplit:
    """고정자/회전자 분리 결과."""
    airgap_r_inner: float
    airgap_r_outer: float
    stator_entities: List[EntityInfo]
    rotor_entities: List[EntityInfo]
    motor_type: str


# ═══════════════════════════════════════════════════════════════
# 좌표 변환 유틸리티 함수
# ═══════════════════════════════════════════════════════════════

def rotate_point(x: float, y: float, angle_rad: float,
                 ox: float = 0.0, oy: float = 0.0) -> Tuple[float, float]:
    """점 (x,y)를 원점 (ox,oy) 기준으로 angle_rad만큼 회전."""
    dx, dy = x - ox, y - oy
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    return (ox + dx * cos_a - dy * sin_a,
            oy + dx * sin_a + dy * cos_a)


def mirror_point(x: float, y: float, axis_angle_rad: float,
                 ox: float = 0.0, oy: float = 0.0) -> Tuple[float, float]:
    """점 (x,y)를 원점 (ox,oy)을 지나는 axis_angle_rad 각도 직선에 대해 대칭."""
    dx, dy = x - ox, y - oy
    cos2a = math.cos(2 * axis_angle_rad)
    sin2a = math.sin(2 * axis_angle_rad)
    mx = ox + dx * cos2a + dy * sin2a
    my = oy + dx * sin2a - dy * cos2a
    return (mx, my)


def transform_entity(ei: EntityInfo, transform_fn) -> EntityInfo:
    """
    EntityInfo를 좌표 변환 함수(transform_fn)로 변환한 새 EntityInfo를 반환.
    transform_fn: (x, y) -> (x', y')
    """
    new_points = [transform_fn(p[0], p[1]) for p in ei.points]
    new_center = transform_fn(*ei.center) if ei.center else None
    new_sa = ei.start_angle
    new_ea = ei.end_angle

    # ARC/CIRCLE의 각도도 변환해야 함
    if ei.etype == 'ARC' and ei.center and ei.radius:
        cx, cy = new_center
        r = ei.radius
        sa_rad = math.radians(ei.start_angle)
        ea_rad = math.radians(ei.end_angle)
        p_start = transform_fn(ei.center[0] + r * math.cos(sa_rad),
                               ei.center[1] + r * math.sin(sa_rad))
        p_end = transform_fn(ei.center[0] + r * math.cos(ea_rad),
                             ei.center[1] + r * math.sin(ea_rad))
        new_sa = math.degrees(math.atan2(p_start[1] - cy, p_start[0] - cx)) % 360
        new_ea = math.degrees(math.atan2(p_end[1] - cy, p_end[0] - cx)) % 360

    return EntityInfo(
        etype=ei.etype,
        layer=ei.layer,
        points=new_points,
        radius=ei.radius,
        center=new_center,
        start_angle=new_sa,
        end_angle=new_ea,
        raw=None,
    )


def rotate_entity(ei: EntityInfo, angle_deg: float,
                  origin: Tuple[float, float] = (0.0, 0.0)) -> EntityInfo:
    """EntityInfo를 angle_deg만큼 회전."""
    ox, oy = origin
    rad = math.radians(angle_deg)
    return transform_entity(ei, lambda x, y: rotate_point(x, y, rad, ox, oy))


def mirror_entity(ei: EntityInfo, axis_angle_deg: float,
                  origin: Tuple[float, float] = (0.0, 0.0)) -> EntityInfo:
    """EntityInfo를 원점을 지나는 axis_angle_deg 직선에 대해 대칭."""
    ox, oy = origin
    rad = math.radians(axis_angle_deg)
    mirrored = transform_entity(ei, lambda x, y: mirror_point(x, y, rad, ox, oy))

    # ARC의 경우 미러링하면 방향이 반전됨 (start/end 교환)
    if mirrored.etype == 'ARC' and mirrored.start_angle is not None:
        mirrored.start_angle, mirrored.end_angle = mirrored.end_angle, mirrored.start_angle
        mirrored.points = list(reversed(mirrored.points))

    return mirrored


def endpoint_key(x: float, y: float, tol_digits: int = 2) -> Tuple[float, float]:
    """좌표를 tol_digits 자릿수로 반올림하여 해시 키 생성."""
    return (round(x, tol_digits), round(y, tol_digits))


def entity_angle(ei: EntityInfo, origin: Tuple[float, float] = (0.0, 0.0)) -> float:
    """엔티티의 대표 각도(deg, 0~360) — 원점 기준."""
    ox, oy = origin
    if ei.center and ei.etype in ('ARC', 'CIRCLE'):
        return math.degrees(math.atan2(ei.center[1] - oy, ei.center[0] - ox)) % 360
    if ei.points:
        mx = np.mean([p[0] for p in ei.points]) - ox
        my = np.mean([p[1] for p in ei.points]) - oy
        return math.degrees(math.atan2(my, mx)) % 360
    return 0.0
