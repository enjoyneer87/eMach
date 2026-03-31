"""
pyMotorGeo.analysis_base
========================

고정자/회전자 공통 분석 기반 클래스 및 인터페이스입니다.

슬롯/극 개수 추정, 기하학적 특성 분석 등 반복되는 로직을 추상화합니다.
"""

from abc import ABC, abstractmethod
import math
import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import Counter

from core import EntityInfo


class ComponentCounter(ABC):
    """
    모터 부품(고정자/회전자)의 개수를 다양한 방법으로 추정하는 추상 기클래스입니다.
    
    하위 클래스는 고정자(슬롯)와 회전자(극)의 개수를 추정하는 구체적인 알고리즘을 
    구현합니다. 공통 인터페이스를 통해 분석 로직이 통일됩니다.
    """

    component_type: str  # "stator" 또는 "rotor"
    count_keyword: str   # "slots" 또는 "poles"
    
    def __init__(self, component_type: str, count_keyword: str):
        """
        Args:
            component_type (str): 부품 타입 ('stator' 또는 'rotor').
            count_keyword (str): 개수 용어 ('slots' 또는 'poles').
        """
        self.component_type = component_type
        self.count_keyword = count_keyword

    @abstractmethod
    def count(self, 
              entities: List[EntityInfo],
              origin: Tuple[float, float] = (0.0, 0.0),
              **kwargs) -> int:
        """
        방사형 선분(LINE) 기반 개수 추정 메서드 (구현 필수).
        
        고정자 슬롯이면 count_slots 로직, 회전자 극이면 count_poles 로직을 구현합니다.
        
        Args:
            entities (List[EntityInfo]): 부품 도면 엔티티.
            origin (Tuple[float, float]): 반경 계산 원점. 기본값 (0.0, 0.0).
            **kwargs: 부품별 추가 매개변수 (tol_angle 등).
        
        Returns:
            int: 추정된 개수. 측정 실패 시 0.
        """
        pass

    @abstractmethod
    def count_by_regions(self,
                        entities: List[EntityInfo],
                        origin: Tuple[float, float] = (0.0, 0.0),
                        **kwargs) -> Dict:
        """
        닫힌 영역(폐곡선) 기반 개수 추정 메서드 (구현 필수).
        
        고정자는 권선 영역, 회전자는 자석/배리어 영역을 분석합니다.
        
        Args:
            entities (List[EntityInfo]): 부품 도면 엔티티.
            origin (Tuple[float, float]): 반경 계산 원점. 기본값 (0.0, 0.0).
            **kwargs: 부품별 추가 매개변수 (airgap_r, r_outer 등).
        
        Returns:
            Dict: 분석 결과 {'n_count': int, 'method': str, ...}.
        """
        pass

    @abstractmethod
    def estimate_robust(self,
                       entities: List[EntityInfo],
                       origin: Tuple[float, float] = (0.0, 0.0),
                       verbose: bool = True,
                       **kwargs) -> Dict:
        """
        여러 알고리즘의 교차 검증으로 최종 개수 판별 (구현 필수).
        
        count()와 count_by_regions() 결과를 비교하여 가장 신뢰할 수 있는 개수를 선정합니다.
        
        Args:
            entities (List[EntityInfo]): 부품 도면 엔티티.
            origin (Tuple[float, float]): 반경 계산 원점. 기본값 (0.0, 0.0).
            verbose (bool): 진행 과정 로깅 여부. 기본값 True.
            **kwargs: 부품별 추가 매개변수.
        
        Returns:
            Dict: 최종 결과 {'n_count': int, 'results': [...], 'agreement': bool, ...}.
        """
        pass

    def _get_radial_lines(self,
                         entities: List[EntityInfo],
                         origin: Tuple[float, float],
                         min_span_ratio: float = 0.8) -> List[Tuple[float, float]]:
        """
        공통 헬퍼: 방사형 선분(LINE)을 필터링하고 각도를 추출합니다.
        
        Args:
            entities (List[EntityInfo]): 엔티티 리스트.
            origin (Tuple[float, float]): 원점.
            min_span_ratio (float): 선분이 방사형으로 간주되는 반경 범위 비율. 기본값 0.8.
        
        Returns:
            List[Tuple[float, float]]: [(angle1, radius_span1), ...] 리스트.
        """
        ox, oy = origin
        radial_lines = []
        
        for ei in entities:
            if ei.etype != 'LINE' or len(ei.points) < 2:
                continue
            
            p1, p2 = ei.points[0], ei.points[1]
            r1 = math.hypot(p1[0] - ox, p1[1] - oy)
            r2 = math.hypot(p2[0] - ox, p2[1] - oy)
            
            span = abs(r2 - r1)
            length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            
            if length < 1e-6:
                continue
            
            # 방사형 판정: span이 전체 길이의 min_span_ratio 이상
            if span / length >= min_span_ratio:
                mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                angle = math.degrees(math.atan2(mid_y - oy, mid_x - ox)) % 360
                radial_lines.append((angle, span))
        
        return radial_lines

    def _get_closed_regions(self,
                           entities: List[EntityInfo],
                           origin: Tuple[float, float]) -> List[Dict]:
        """
        공통 헬퍼: 닫힌 폴리라인(권선/자석 영역)을 추출합니다.
        
        Args:
            entities (List[EntityInfo]): 엔티티 리스트.
            origin (Tuple[float, float]): 원점.
        
        Returns:
            List[Dict]: 각 영역의 {'entity': EntityInfo, 'r_avg': float, 'angle': float, ...}.
        """
        ox, oy = origin
        regions = []
        
        for ei in entities:
            if not ei.is_closed or ei.etype not in ('LWPOLYLINE', 'POLYLINE', 'SPLINE'):
                continue
            
            radii = [math.hypot(p[0] - ox, p[1] - oy) for p in ei.points]
            r_min, r_max, r_avg = min(radii), max(radii), np.mean(radii)
            
            angles = [math.degrees(math.atan2(p[1] - oy, p[0] - ox)) % 360 for p in ei.points]
            angle_avg = float(np.mean(angles))
            
            area = abs(ei.get_area(origin)) if hasattr(ei, 'get_area') else 0.0
            
            regions.append({
                'entity': ei,
                'r_min': r_min,
                'r_max': r_max,
                'r_avg': r_avg,
                'angle': angle_avg,
                'area': area,
            })
        
        return regions
