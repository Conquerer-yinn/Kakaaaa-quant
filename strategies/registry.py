"""策略注册表加载器。

注册表只回答一个问题：哪些策略参与日常运行、运行后是否推送。
策略内容本身仍然由各自脚本负责。
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

REGISTRY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategy_registry.yaml")


@dataclass(frozen=True)
class StrategyEntry:
    name: str
    script: str
    enabled: bool
    push: bool
    notes: str | None


def load_registry(registry_file: str | None = None) -> list[StrategyEntry]:
    path = registry_file or REGISTRY_FILE
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    entries = []
    seen_names = set()
    for item in data.get("strategies", []):
        if not item.get("name") or not item.get("script"):
            raise ValueError(f"Registry entry missing name/script: {item!r}")
        name = str(item["name"])
        if name in seen_names:
            raise ValueError(f"Duplicate strategy name in registry: {name}")
        seen_names.add(name)
        entries.append(
            StrategyEntry(
                name=name,
                script=str(item["script"]),
                enabled=bool(item.get("enabled", False)),
                push=bool(item.get("push", False)),
                notes=item.get("notes"),
            )
        )
    return entries


def enabled_strategies(registry_file: str | None = None) -> list[StrategyEntry]:
    return [entry for entry in load_registry(registry_file) if entry.enabled]


def push_enabled_strategies(registry_file: str | None = None) -> list[StrategyEntry]:
    """既启用又需要推送摘要的策略。"""
    return [entry for entry in enabled_strategies(registry_file) if entry.push]
