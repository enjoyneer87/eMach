"""
pyMotorGeo.topology_base
========================

고정자/회전자 공통 토폴로지 분류 기반 클래스 및 인터페이스입니다.

엔티티 분류, 영역 태깅, 토폴로지 판별 등 반복되는 로직을 추상화합니다.
"""

from abc import ABC, abstractmethod
import math
import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

from core import EntityInfo


class ComponentTopologyClassifier(ABC):
    """
    모터 부품(고정자/회전자)의 토폴로지를 분석 및 분류하는 추상 기클래스입니다.
    
    엔티티를 기하학적 특성(반경, 각도, 닫힘 여부)에 따라 분류하고, 
    부품별 특화된 토폴로지(e.g., SPM/IPM/SynRM 또는 슬롯/티스/요크)를 판별합니다.
    """

    component_type: str  # "stator" 또는 "rotor"
    region_names: Dict[str, str]  # 영역 타입 → 표시명
    region_colors: Dict[str, str]  # 영역 타입 → 색상
    
    def __init__(self, 
                 component_type: str,
                 region_names: Dict[str, str],
                 region_colors: Dict[str, str]):
        """
        Args:
            component_type (str): 부품 타입 ('stator' 또는 'rotor').
            region_names (Dict[str, str]): 영역 타입 → 표시명 매핑.
            region_colors (Dict[str, str]): 영역 타입 → 색상 매핑.
        """
        self.component_type = component_type
        self.region_names = region_names
        self.region_colors = region_colors

    @staticmethod
    def entity_radii(ei: EntityInfo,
                     origin: Tuple[float, float]) -> List[float]:
        """
        공유 헬퍼: 엔티티의 모든 점에 대한 반경 리스트를 반환합니다.
        
        Args:
            ei (EntityInfo): 분석할 엔티티.
            origin (Tuple[float, float]): 반경 계산 원점.
        
        Returns:
            List[float]: 각 점의 반경 값들.
        """
        ox, oy = origin
        return [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]

    @staticmethod
    def entity_avg_angle(ei: EntityInfo,
                        origin: Tuple[float, float]) -> float:
        """
        공유 헬퍼: 엔티티의 대표 각도(도, 0-360)를 반환합니다.
        
        Args:
            ei (EntityInfo): 분석할 엔티티.
            origin (Tuple[float, float]): 각도 계산 원점.
        
        Returns:
            float: 모든 점들의 평균 각도(도).
        """
        ox, oy = origin
        if not ei.points:
            return 0.0
        
        angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360
                  for p in ei.points]
        return float(np.mean(angles))

    @abstractmethod
    def classify_entities(self,
                         component_entities: List[Dict],
                         origin: Tuple[float, float] = (0.0, 0.0),
                         **kwargs) -> Dict:
        """
        부품 내의 엔티티들을 분류하여 토폴로지를 판별합니다 (구현 필수).
        
        고정자는 슬롯/티스/요크 분류, 회전자는 자석/배리어/코어 분류를 수행합니다.
        
        Args:
            component_entities (List[Dict]): [{'entity': EntityInfo, ...}, ...].
            origin (Tuple[float, float]): 원점. 기본값 (0.0, 0.0).
            **kwargs: 부품별 추가 매개변수 (airgap_r, r_outer 등).
        
        Returns:
            Dict: 분류 결과 {'regions': [...], 'topology': str, ...}.
        """
        pass

    @abstractmethod
    def reassign_region(self,
                       regions: List[Dict],
                       new_assignment: Dict[int, str]) -> List[Dict]:
        """
        GUI 재지정을 위해 영역 태그를 변경합니다 (구현 필수).
        
        사용자가 자동 분류 결과 중 잘못된 부분을 수정할 수 있도록 합니다.
        
        Args:
            regions (List[Dict]): 분류된 영역들.
            new_assignment (Dict[int, str]): {region_index: new_tag} 매핑.
        
        Returns:
            List[Dict]: 업데이트된 영역들.
        """
        pass

    @abstractmethod
    def get_region_summary(self,
                          regions: List[Dict]) -> Dict:
        """
        분류된 영역들의 요약 통계를 반환합니다 (구현 필수).
        
        Args:
            regions (List[Dict]): 분류된 영역들.
        
        Returns:
            Dict: {'n_region': int, 'region_types': {...}, 'total_area': float, ...}.
        """
        pass

    def cluster_by_angle(self,
                        items: List[Dict],
                        origin: Tuple[float, float],
                        gap_deg: float = 5.0) -> List[List[Dict]]:
        """
        공유 헬퍼: 엔티티를 각도 기준으로 클러스터링합니다.
        
        인접 엔티티 사이 각도 차이가 gap_deg 이하이면 같은 그룹입니다.
        
        Args:
            items (List[Dict]): [{'entity': EntityInfo, ...}, ...].
            origin (Tuple[float, float]): 각도 계산 원점.
            gap_deg (float): 클러스터 병합 각도 한계(도). 기본값 5.0.
        
        Returns:
            List[List[Dict]]: 각도 순서로 정렬된 클러스터 리스트.
        """
        if not items:
            return []
        
        # 각 아이템의 대표 각도
        angles = [self.entity_avg_angle(item['entity'], origin) for item in items]
        
        # 각도 순 정렬
        idx_sorted = np.argsort(angles)
        
        # 클러스터링
        clusters: List[List[int]] = [[idx_sorted[0]]]
        for i in range(1, len(idx_sorted)):
            curr_idx = idx_sorted[i]
            prev_idx = idx_sorted[i - 1]
            diff = (angles[curr_idx] - angles[prev_idx]) % 360
            
            if diff < gap_deg or diff > (360 - gap_deg):  # wrap-around 고려
                clusters[-1].append(curr_idx)
            else:
                clusters.append([curr_idx])
        
        return [[items[j] for j in c] for c in clusters]

    def _get_entity_bounds(self,
                          entities: List[EntityInfo],
                          origin: Tuple[float, float]) -> Tuple[float, float, float, float]:
        """
        공유 헬퍼: 엔티티 그룹의 반경/각도 범위를 반환합니다.
        
        Args:
            entities (List[EntityInfo]): 엔티티 리스트.
            origin (Tuple[float, float]): 원점.
        
        Returns:
            Tuple: (r_min, r_max, angle_min, angle_max).
        """
        radii = []
        angles = []
        
        for ei in entities:
            radii.extend(self.entity_radii(ei, origin))
            angles.append(self.entity_avg_angle(ei, origin))
        
        if not radii or not angles:
            return 0.0, 0.0, 0.0, 360.0
        
        return min(radii), max(radii), min(angles), max(angles)
