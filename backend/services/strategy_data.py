from __future__ import annotations

from backend.schemas.frontend import StrategyItemResponse, StrategyListResponse
from strategies.registry import load_registry


def build_strategy_list() -> StrategyListResponse:
    """把策略注册表原样暴露给前端，前端不需要理解 yaml。"""
    try:
        entries = load_registry()
    except Exception as exc:
        return StrategyListResponse(success=False, strategies=[], error_message=str(exc))

    items = [
        StrategyItemResponse(
            name=entry.name,
            script=entry.script,
            enabled=entry.enabled,
            push=entry.push,
            notes=entry.notes,
        )
        for entry in entries
    ]
    return StrategyListResponse(success=True, strategies=items, error_message=None)
