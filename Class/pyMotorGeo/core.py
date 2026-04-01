"""
pyMotorGeo.core
===============

모터 지오메트리 파싱 및 변환을 위한 핵심 데이터 전송 객체(DTO) 및 수학적 기하 변환 유틸리티를 제공합니다.
DXF 엔티티를 정규화하여 `EntityInfo` 데이터 클래스로 추상화하며, 점/선/원의 회전 및 대칭 이동과 같은 
공간 변환 함수(`rotate_entity`, `mirror_entity`) 등을 포함합니다.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable


@dataclass
class EntityInfo:
    """DXF 도면의 개별 기하학적 요소(Entity) 정보를 담는 추상화된 데이터 구조체.

    Attributes:
        etype (str): 엔티티의 종류 (예: 'LINE', 'ARC', 'CIRCLE', 'LWPOLYLINE' 등).
        layer (str): 엔티티가 속한 도면의 레이어 이름.
        points (List[Tuple[float, float]]): 엔티티를 구성하는 최소 2D 혹은 3D 좌표점 리스트.
        radius (Optional[float]): 'CIRCLE' 또는 'ARC' 엔티티의 반지름. 기본값은 None.
        center (Optional[Tuple[float, float]]): 'CIRCLE' 또는 'ARC' 기하의 중심 좌표 (x, y). 기본값은 None.
        start_angle (Optional[float]): 'ARC' 시작 각도 (도 단위, 0~360). x축 양의 방향 기준. 기본값은 None.
        end_angle (Optional[float]): 'ARC' 종료 각도 (도 단위, 0~360). x축 양의 방향 기준. 기본값은 None.
        is_closed (bool): 'LWPOLYLINE', 'POLYLINE', 'CIRCLE'의 폐곡선 연속성 여부. 기본값은 False.
        raw (object): 파싱 원본인 ezdxf 객체. 직렬화를 피하기 위해 repr 출력 및 기본값에서는 제외됨.
    """
    etype: str
    layer: str
    points: List[Tuple[float, float]]
    radius: Optional[float] = None
    center: Optional[Tuple[float, float]] = None
    start_angle: Optional[float] = None
    end_angle: Optional[float] = None
    is_closed: bool = False
    raw: object = field(default=None, repr=False)

    @property
    def coords(self) -> List[Tuple[float, float]]:
        """호환성과 편의성을 위해 points 리스트를 반환하는 Alias 속성.

        Returns:
            List[Tuple[float, float]]: 내부 좌표점 리스트.
        """
        return self.points

    @property
    def r_min(self) -> float:
        """원점(0.0, 0.0)으로부터 엔티티를 구성하는 점들 중 가장 가까운 최단 거리를 반환.

        Returns:
            float: 최소 이격 반경 거리. 데이터가 없으면 무한대(inf) 반환.
        """
        return min(math.hypot(x, y) for x, y in self.points) if self.points else float('inf')

    @property
    def r_max(self) -> float:
        """원점(0.0, 0.0)으로부터 엔티티를 구성하는 점들 중 가장 먼 최대 거리를 반환.

        Returns:
            float: 최대 이격 반경 거리. 데이터가 없으면 0.0 반환.
        """
        return max(math.hypot(x, y) for x, y in self.points) if self.points else 0.0

    @property
    def angle_deg(self) -> float:
        """대표 좌표점들의 평균 방위각(도 단위, 0~360)을 반환.

        Returns:
            float: 360도로 정규화된 평균 각도값 (degree).
        """
        if not self.points:
            return 0.0
        angles = [math.degrees(math.atan2(y, x)) % 360 for x, y in self.points]
        return float(np.mean(angles))
    
    def get_area(self, origin: Tuple[float, float] = (0.0, 0.0)) -> float:
        """단순 닫힌 다각형(Simple closed polygon)의 면적을 Shoelace 공식으로 계산.

        Args:
            origin (Tuple[float, float]): (미사용, 호환성 유지) 면적 기준이 될 원점 좌표.

        Returns:
            float: 해당 닫힌 다각형이 이루는 절대 면적. 닫혀 있지 않거나 점이 3개 미만이면 0.0을 반환.
        """
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
    """고정자(Stator)와 회전자(Rotor) 분리 알고리즘의 결과를 담는 데이터 객체.

    Attributes:
        airgap_r_inner (float): 에어갭의 내경 (회전자 쪽 반경).
        airgap_r_outer (float): 에어갭의 외경 (고정자 쪽 반경).
        stator_entities (List[EntityInfo]): 분리된 고정자 요소 리스트.
        rotor_entities (List[EntityInfo]): 분리된 회전자 요소 리스트.
        motor_type (str): 분리된 모터의 물리적 구조 형식 (예: 'inner_rotor', 'outer_rotor').
    """
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
    """기준점을 축으로 일정 각도만큼 회전 변환을 적용한 좌표를 반환.

    Args:
        x (float): 회전시킬 점의 x 좌표.
        y (float): 회전시킬 점의 y 좌표.
        angle_rad (float): 회전할 각도 (라디안 단위). 반시계 방향이 양수 체계.
        ox (float): 회전 중심의 x 좌표. 기본값은 0.0.
        oy (float): 회전 중심의 y 좌표. 기본값은 0.0.

    Returns:
        Tuple[float, float]: 회전이 적용된 새로운 2D 좌표 (x', y').
    """
    dx, dy = x - ox, y - oy
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    return (ox + dx * cos_a - dy * sin_a,
            oy + dx * sin_a + dy * cos_a)


def mirror_point(x: float, y: float, axis_angle_rad: float,
                 ox: float = 0.0, oy: float = 0.0) -> Tuple[float, float]:
    """단일 2D 점을 특정 각도를 지나는 중심축에 대해 반사 이동(Reflection) 변환.

    Args:
        x (float): 대칭 이동시킬 점의 x 좌표.
        y (float): 대칭 이동시킬 점의 y 좌표.
        axis_angle_rad (float): 반사 기준축이 x축과 이루는 각도 (라디안 단위).
        ox (float): 반사축이 통과하는 원점의 x 좌표. 기본값은 0.0.
        oy (float): 반사축이 통과하는 원점의 y 좌표. 기본값은 0.0.

    Returns:
        Tuple[float, float]: 대칭 이동이 완료된 새로운 좌표 (x', y').
    """
    dx, dy = x - ox, y - oy
    cos2a = math.cos(2 * axis_angle_rad)
    sin2a = math.sin(2 * axis_angle_rad)
    mx = ox + dx * cos2a + dy * sin2a
    my = oy + dx * sin2a - dy * cos2a
    return (mx, my)


def transform_entity(ei: EntityInfo, transform_fn: Callable[[float, float], Tuple[float, float]]) -> EntityInfo:
    """콜백 기반 좌표 변환을 통하여 단일 EntityInfo의 내부 속성(포인트, 중점, 각도) 매핑을 수행.

    회전이나 대칭 등의 임의의 변환 함수를 받아, 해당 함수를 `ei`의 point와 ARC/CIRCLE의 
    center 및 angle에 일괄 적용하여 깊이 복사(deep copy)된 새 엔티티를 반환합니다.

    Args:
        ei (EntityInfo): 변환을 적용할 원본 엔티티 객체.
        transform_fn (Callable): 2D(x, y) 입력을 받아 변환된 좌표계인 (x', y') 튜플을 반환하는 콜백 함수.

    Returns:
        EntityInfo: 모든 기하 정보가 새로운 좌표계로 변환된 새 엔티티 객체.
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
    """단일 엔티티 객체를 지정된 원점 기준으로 회전시킵니다.

    Args:
        ei (EntityInfo): 회전시킬 대상 엔티티.
        angle_deg (float): 회전 각도 (도 단위, 반시계 양수).
        origin (Tuple[float, float]): 회전 중심의 좌표. 기본값은 원점(0.0, 0.0).

    Returns:
        EntityInfo: 회전이 완료된 새로운(deep copy) 엔티티 객체.
    """
    ox, oy = origin
    rad = math.radians(angle_deg)
    return transform_entity(ei, lambda x, y: rotate_point(x, y, rad, ox, oy))


def mirror_entity(ei: EntityInfo, axis_angle_deg: float,
                  origin: Tuple[float, float] = (0.0, 0.0)) -> EntityInfo:
    """단일 엔티티 객체를 지정된 원점을 지나는 선을 기준으로 대칭 이동(반사)시킵니다.

    'ARC' 형상의 경우 구조가 반전되므로 시작 각도와 종료 각도를 바꾸어 정상 형상을 유지합니다.

    Args:
        ei (EntityInfo): 대칭 이동시킬 대상 엔티티.
        axis_angle_deg (float): 대칭의 기준이 되는 축의 각도 (도 단위).
        origin (Tuple[float, float]): 대칭 축이 통과하는 임의의 점 좌표. 기본값은 원점(0.0, 0.0).

    Returns:
        EntityInfo: 대칭 이동이 완료된 새로운(deep copy) 엔티티 객체.
    """
    ox, oy = origin
    rad = math.radians(axis_angle_deg)
    mirrored = transform_entity(ei, lambda x, y: mirror_point(x, y, rad, ox, oy))

    # ARC의 경우 미러링하면 방향이 반전됨 (start/end 교환)
    if mirrored.etype == 'ARC' and mirrored.start_angle is not None:
        mirrored.start_angle, mirrored.end_angle = mirrored.end_angle, mirrored.start_angle
        mirrored.points = list(reversed(mirrored.points))

    return mirrored


def endpoint_key(x: float, y: float, tol_digits: int = 2) -> Tuple[float, float]:
    """부동소수점(float) 오차를 무시하고 일관된 점 비교/해싱을 할 수 있게 키를 생성합니다.

    Args:
        x (float): 대상 x 좌표.
        y (float): 대상 y 좌표.
        tol_digits (int): 일치 여부를 판단할 소수점 이하 반올림 자릿수. 기본값은 2.

    Returns:
        Tuple[float, float]: 일관성을 보장하기 위해 반올림 처리된 좌푯값 (단위: 지정된 정밀도).
    """
    return (round(x, tol_digits), round(y, tol_digits))


def entity_angle(ei: EntityInfo, origin: Tuple[float, float] = (0.0, 0.0)) -> float:
    """특정 엔티티가 원점 기준 어느 각도 위치(위상)에 놓여 있는지 대푯값을 계산합니다.
    
    ARC나 CIRCLE의 경우 중심점 각도를 반환하며, POLYLINE 등의 선 형태는 외곽 점들의 평균 위치를 사용합니다.

    Args:
        ei (EntityInfo): 대상 엔티티.
        origin (Tuple[float, float]): 방위각 산출 기준점. 기본값은 원점(0.0, 0.0).

    Returns:
        float: 엔티티의 대표 방위각 (도 단위, 0~360).
    """
    ox, oy = origin
    if ei.center and ei.etype in ('ARC', 'CIRCLE'):
        return math.degrees(math.atan2(ei.center[1] - oy, ei.center[0] - ox)) % 360
    if ei.points:
        mx = np.mean([p[0] for p in ei.points]) - ox
        my = np.mean([p[1] for p in ei.points]) - oy
        return math.degrees(math.atan2(my, mx)) % 360
    return 0.0
