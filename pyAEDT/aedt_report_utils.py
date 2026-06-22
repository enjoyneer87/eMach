import ansys.aedt.core
from typing import List, Dict, Optional, Any

# 모듈 수준 캐시: COM 왕복을 최소화한다.
# key: id(post_processor), value: (report_type, categories, {category: [expressions]})
_POST_CACHE: Dict[int, Dict] = {}


def _get_cached_report_type(post_processor: Any) -> str:
    """available_report_types COM 콜을 최초 1회만 수행하고 결과를 캐시한다."""
    pid = id(post_processor)
    if pid not in _POST_CACHE:
        _POST_CACHE[pid] = {"report_type": None, "categories": None, "expressions": {}}
    entry = _POST_CACHE[pid]
    if entry["report_type"] is None:
        report_types = post_processor.available_report_types
        entry["report_type"] = report_types[0] if report_types else ""
    return entry["report_type"]


def clear_post_cache(post_processor: Any = None) -> None:
    """캐시를 강제 초기화한다. post_processor가 None이면 전체 초기화."""
    if post_processor is None:
        _POST_CACHE.clear()
    else:
        _POST_CACHE.pop(id(post_processor), None)


def get_available_categories(post_processor: Any, report_type: str = None) -> List[str]:
    """
    Get available report categories (e.g., 'Torque', 'Loss') for a given report type.
    
    Args:
        post_processor: ansys.aedt.core.modules.post_general.PostProcessor object (e.g., m2d.post)
        report_type: Specific report type (e.g., 'Transient'). If None, the first available is used.
        
    Returns:
        List of available category names.
    """
    pid = id(post_processor)
    if report_type is None:
        report_type = _get_cached_report_type(post_processor)
    if not report_type:
        return []

    entry = _POST_CACHE.setdefault(pid, {"report_type": report_type, "categories": None, "expressions": {}})
    if entry.get("categories") is None:
        entry["categories"] = post_processor.available_quantities_categories(report_category=report_type)
    return entry["categories"]


def get_report_expressions(
    post_processor: Any,
    category: str,
    report_type: str = None
) -> List[str]:
    """
    Get available expressions (quantities) for a specific category.
    
    Args:
        post_processor: ansys.aedt.core.modules.post_general.PostProcessor object (e.g., m2d.post)
        category: The category name (e.g., 'Loss', 'Torque')
        report_type: Specific report type (e.g., 'Transient'). If None, the first available is used.
        
    Returns:
        List of expressions that can be used in get_solution_data(expressions=...).
    """
    pid = id(post_processor)
    if report_type is None:
        report_type = _get_cached_report_type(post_processor)
    if not report_type:
        return []

    entry = _POST_CACHE.setdefault(pid, {"report_type": report_type, "categories": None, "expressions": {}})
    if category not in entry["expressions"]:
        entry["expressions"][category] = post_processor.available_report_quantities(
            report_category=report_type,
            quantities_category=category,
        )
    return entry["expressions"][category]

def print_expressions_in_category(post_processor: Any, category: str, report_type: str = None) -> None:
    """
    Utility to quickly print available expressions for a target category.
    """
    expressions = get_report_expressions(post_processor, category, report_type)
    if expressions:
        print(f"=== Expressions for '{category}' ===")
        for expr in expressions:
            print(f" - {expr}")
    else:
        print(f"No expressions found for category '{category}'.")

def find_expressions(
    post_processor: Any, 
    category: str, 
    search_keyword: str, 
    report_type: str = None
) -> List[str]:
    """
    Filter expressions within a specific category by a search keyword.
    The resulting list can be passed directly to 'get_solution_data(expressions=...)'.
    
    Args:
        post_processor: ansys.aedt.core.modules.post_general.PostProcessor object
        category: The category name (e.g., 'Loss')
        search_keyword: Substring to filter by (case-insensitive)
        report_type: Specific report type. If None, uses the first available.
        
    Returns:
        List of matching expressions.
    """
    expressions = get_report_expressions(post_processor, category, report_type)
    
    # Case-insensitive substring match
    keyword_lower = search_keyword.lower()
    return [expr for expr in expressions if keyword_lower in expr.lower()]
