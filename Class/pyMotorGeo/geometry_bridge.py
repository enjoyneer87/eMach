import json
import logging
from pathlib import Path
import sys

# 상위 디렉터리( pyMotorGeo )로의 모듈 접근 허용
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from reader import read_entity_list, EntityInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeometryBridge:
    """
    다양한 형식의 도면(DXF, JSON 등)을 pyMotorGeo의 표준 Contract인 GeometryPayload(v1) 형식으로 변환하는 브릿지 모듈
    """
    
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
            
            # EntityInfo 객체를 딕셔너리로 변환 (Contract에 맞춤)
            entities.append({
                "entity_type": getattr(ei, 'etype', 'UNKNOWN').lower(),
                "points": list(getattr(ei, 'points', [])),
                "layer": mapped_layer,
                "radius": getattr(ei, 'radius', None),
                "center": list(ei.center) if getattr(ei, 'center', None) else None,
                "start_angle": getattr(ei, 'start_angle', None),
                "end_angle": getattr(ei, 'end_angle', None),
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
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        elif ext == '.dxf':
            return GeometryBridge.parse_dxf_to_payload(path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")
