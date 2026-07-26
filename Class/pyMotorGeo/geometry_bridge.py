import json
import logging
import math
from pathlib import Path
import sys

# 상위 디렉터리( pyMotorGeo )로의 모듈 접근 허용
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from reader import read_entity_list

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeometryBridge:
    """
    다양한 형식의 도면(DXF, JSON 등)을 pyMotorGeo의 표준 Contract인 GeometryPayload(v1) 형식으로 변환하는 브릿지 모듈
    """
    
    @staticmethod
    def _normalize_arc_angles(start_angle, end_angle) -> tuple[float, float]:
        """Matplotlib/DXF 간 경계 케이스를 줄이기 위한 각도 정규화."""
        sa = float(start_angle if start_angle is not None else 0.0) % 360.0
        ea = float(end_angle if end_angle is not None else 360.0) % 360.0
        if abs(ea - sa) < 1e-9:
            ea = sa + 360.0
        elif ea <= sa:
            ea += 360.0
        return sa, ea

    @staticmethod
    def _sample_arc_points(
        center: tuple[float, float],
        radius: float,
        start_angle: float,
        end_angle: float,
    ) -> list[list[float]]:
        sa, ea = GeometryBridge._normalize_arc_angles(start_angle, end_angle)
        span = max(1.0, ea - sa)
        n_points = max(24, int(span / 2.0) + 1)
        cx, cy = center

        points = []
        for i in range(n_points):
            t = sa + span * (i / (n_points - 1))
            rad = math.radians(t)
            points.append([cx + radius * math.cos(rad), cy + radius * math.sin(rad)])
        return points

    @staticmethod
    def _sample_circle_points(center: tuple[float, float], radius: float) -> list[list[float]]:
        cx, cy = center
        n_points = 181
        points = []
        for i in range(n_points):
            t = (2.0 * math.pi) * (i / (n_points - 1))
            points.append([cx + radius * math.cos(t), cy + radius * math.sin(t)])
        return points

    @staticmethod
    def _bbox_from_points(points: list[list[float]]) -> list[float] | None:
        if not points:
            return None
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return [min(xs), min(ys), max(xs), max(ys)]

    @staticmethod
    def parse_dxf_to_payload(dxf_path: str | Path) -> dict:
        """
        pyMotorGeo 내부의 읽기 모듈(read_entity_list)을 사용하여 DXF를 읽고 
        GeometryPayload 형식의 딕셔너리로 정확하게 반환합니다.
        """
        # pyMotorGeo core parser 사용
        entities_info, doc = read_entity_list(str(dxf_path), expand_inserts=True, verbose=False)
        
        entities = []
        layer_mapping = {}
        
        for ei in entities_info:
            layer = getattr(ei, 'layer', '(no_layer)').lower()
            
            # 레이어 맵핑 이름 단순 통일
            if "rotor" in layer: mapped_layer = "rotor"
            elif "stator" in layer: mapped_layer = "stator"
            elif "magnet" in layer: mapped_layer = "magnet"
            else: mapped_layer = layer
            layer_mapping[layer] = mapped_layer
            
            ent_type = getattr(ei, 'etype', 'UNKNOWN').lower()
            center = list(ei.center) if getattr(ei, 'center', None) else None
            radius = getattr(ei, 'radius', None)
            start_angle = getattr(ei, 'start_angle', None)
            end_angle = getattr(ei, 'end_angle', None)
            base_points = list(getattr(ei, 'points', []))

            # 렌더링 품질을 위해 ARC/CIRCLE은 샘플 포인트를 추가 제공
            render_points = base_points
            if ent_type == 'arc' and center and radius is not None:
                render_points = GeometryBridge._sample_arc_points(
                    center=(float(center[0]), float(center[1])),
                    radius=float(radius),
                    start_angle=float(start_angle if start_angle is not None else 0.0),
                    end_angle=float(end_angle if end_angle is not None else 360.0),
                )
            elif ent_type == 'circle' and center and radius is not None:
                render_points = GeometryBridge._sample_circle_points(
                    center=(float(center[0]), float(center[1])),
                    radius=float(radius),
                )

            # EntityInfo 객체를 딕셔너리로 변환 (Contract에 맞춤)
            entities.append({
                "entity_type": ent_type,
                "points": base_points,
                "render_points": render_points,
                "bbox": GeometryBridge._bbox_from_points(render_points),
                "layer": mapped_layer,
                "radius": radius,
                "center": center,
                "start_angle": start_angle,
                "end_angle": end_angle,
                "is_closed": getattr(ei, 'is_closed', False)
            })

        return {
            "contract_version": "v1",
            "unit": "mm", 
            "origin": [0.0, 0.0],
            "periodicity": "full",
            "entities": entities,
            "layer_mapping": layer_mapping,
            "provenance": {
                "source_package": "pyMotorGeo",
                "source_file": Path(dxf_path).name,
            }
        }

    @staticmethod
    def convert_to_payload(file_path: str | Path) -> dict:
        """
        파일 확장자에 따라 적절한 파서를 호출하여 표준 Payload로 변환합니다.
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.json':
            with open(path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                return data
        elif ext == '.dxf':
            return GeometryBridge.parse_dxf_to_payload(path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")
