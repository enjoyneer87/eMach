"""MLDatasetPayload validator.

devplan Action 4의 최소 구현으로, 학습 데이터 계약의 필수 항목을 점검한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple


def _is_ratio(value: Any) -> bool:
    return isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0


def validate_ml_dataset_payload(
    payload: Dict[str, Any],
    check_source_path: bool = False,
) -> Tuple[bool, List[str]]:
    """MLDatasetPayload 최소 유효성 검증.

    Parameters
    ----------
    payload : dict
        검증 대상 payload dict
    check_source_path : bool
        True일 때 source.path 실제 존재 여부를 검사

    Returns
    -------
    (is_valid, errors)
        is_valid는 에러가 없으면 True
    """

    errors: List[str] = []

    if payload.get("contract_version") != "v1":
        errors.append("contract_version must be 'v1'")

    source = payload.get("source", {})
    source_type = source.get("source_type")
    source_path = source.get("path")

    if source_type not in {"h5", "txt"}:
        errors.append("source.source_type must be one of {'h5','txt'}")

    if not isinstance(source_path, str) or not source_path.strip():
        errors.append("source.path must be a non-empty string")
    elif check_source_path and not Path(source_path).exists():
        errors.append(f"source.path does not exist: {source_path}")

    graph = payload.get("graph", {})
    node_features = graph.get("node_features", [])
    edge_features = graph.get("edge_features", [])
    target_fields = graph.get("target_fields", [])

    if not isinstance(node_features, list) or not node_features:
        errors.append("graph.node_features must be a non-empty list")
    if not isinstance(edge_features, list) or not edge_features:
        errors.append("graph.edge_features must be a non-empty list")
    if not isinstance(target_fields, list) or not target_fields:
        errors.append("graph.target_fields must be a non-empty list")
    else:
        required_targets = {"Bx", "By"}
        missing = sorted(required_targets.difference(set(target_fields)))
        if missing:
            errors.append(f"graph.target_fields missing required targets: {missing}")

    split = payload.get("split", {})
    train = split.get("train")
    val = split.get("val")
    test = split.get("test")

    if not _is_ratio(train):
        errors.append("split.train must be in [0,1]")
    if not _is_ratio(val):
        errors.append("split.val must be in [0,1]")
    if not _is_ratio(test):
        errors.append("split.test must be in [0,1]")

    if _is_ratio(train) and _is_ratio(val) and _is_ratio(test):
        split_sum = float(train) + float(val) + float(test)
        if abs(split_sum - 1.0) > 1e-6:
            errors.append(f"split ratios must sum to 1.0, got {split_sum}")

    if payload.get("normalization") != "train_stat":
        errors.append("normalization must be 'train_stat'")

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dict")

    return (len(errors) == 0), errors
