"""
pyMotorGeo.contracts
====================

Contract-first development을 위한 공통 payload 정의 모듈.

이 모듈은 다음 5종 contract를 dataclass로 정의한다.
- GeometryPayload
- SemanticPayload
- ExecutionPayload
- CommonResult
- MLDatasetPayload
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

ContractVersion = Literal["v1"]
SourceType = Literal["h5", "txt"]


@dataclass
class Provenance:
    """데이터 생성 출처 정보를 표현한다."""

    source_package: str
    source_version: str
    created_at: str


@dataclass
class GeometryEntity:
    """정규화된 단일 기하 엔티티."""

    entity_type: Literal["line", "arc", "circle", "polyline"]
    points: List[List[float]]
    layer: str
    radius: Optional[float] = None
    center: Optional[List[float]] = None


@dataclass
class GeometryPayload:
    """기하학 표준 payload."""

    contract_version: ContractVersion
    unit: Literal["mm"]
    origin: List[float]
    periodicity: Literal["full", "half", "quarter"]
    entities: List[GeometryEntity]
    layer_mapping: Dict[str, str]
    provenance: Provenance


@dataclass
class SemanticRegion:
    """토폴로지/영역 의미론 정보."""

    name: str
    confidence: float


@dataclass
class SemanticPayload:
    """선택적 의미론 payload."""

    contract_version: ContractVersion
    topology_type: str
    regions: List[SemanticRegion]
    fallback_reason_code: Optional[str] = None


@dataclass
class RunProfile:
    """솔버 실행 옵션."""

    setup: str
    mesh: str
    sweep: str


@dataclass
class ExecutionPayload:
    """솔버 실행 요청 payload."""

    contract_version: ContractVersion
    target_solver: Literal["motorcad", "maxwell", "twinbuilder"]
    run_profile: RunProfile
    exported_artifacts: List[str]
    retry_count: int = 0


@dataclass
class CommonResult:
    """공통 결과 payload."""

    contract_version: ContractVersion
    geometry_metrics: Dict[str, float]
    solver_kpi: Dict[str, float]
    provenance: Provenance


@dataclass
class DatasetSource:
    """MLDataset 입력 소스 정의."""

    source_type: SourceType
    path: str


@dataclass
class GraphFeatureSpec:
    """그래프 입력/타깃 정의."""

    node_features: List[str]
    edge_features: List[str]
    target_fields: List[str]


@dataclass
class SplitSpec:
    """학습/검증/테스트 분할 정의."""

    train: float
    val: float
    test: float


@dataclass
class MLDatasetPayload:
    """SciML 학습 데이터 계약 payload."""

    contract_version: ContractVersion
    source: DatasetSource
    graph: GraphFeatureSpec
    split: SplitSpec
    normalization: Literal["train_stat"]
    metadata: Dict[str, Any] = field(default_factory=dict)


def payload_to_dict(payload: Any) -> Dict[str, Any]:
    """dataclass payload를 dict로 변환한다."""

    if not is_dataclass(payload):
        raise TypeError("payload must be a dataclass instance")
    return asdict(payload)


def dump_payload_json(payload: Any, output_path: str) -> None:
    """payload를 JSON으로 저장한다."""

    data = payload_to_dict(payload)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_payload_json(input_path: str) -> Dict[str, Any]:
    """JSON payload를 dict로 로드한다."""

    path = Path(input_path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
