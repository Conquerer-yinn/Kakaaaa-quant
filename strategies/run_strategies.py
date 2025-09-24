"""策略统一运行入口（第一版：只做计划展示，不执行）。

先把“注册表 -> 运行清单”的骨架搭起来，执行逻辑等首个策略稳定后再接。
"""
from __future__ import annotations

import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from strategies.registry import enabled_strategies, load_registry


def parse_args():
    parser = argparse.ArgumentParser(description="Run strategies listed in strategy_registry.yaml.")
    parser.add_argument("--all", action="store_true", help="列出全部策略（含未启用）。")
    return parser.parse_args()


def main():
    args = parse_args()
    entries = load_registry() if args.all else enabled_strategies()
    if not entries:
        print("当前没有启用的策略。可在 strategies/strategy_registry.yaml 中开启。")
        return

    print("计划运行的策略：")
    for entry in entries:
        flag = "enabled" if entry.enabled else "disabled"
        print(f"- {entry.name} ({flag}, push={entry.push}) -> {entry.script}")


if __name__ == "__main__":
    main()
