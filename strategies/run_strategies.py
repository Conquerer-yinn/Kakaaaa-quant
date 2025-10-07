"""策略统一运行入口。

按注册表顺序执行 enabled 策略：每个策略模块约定暴露 `run(trade_date)`。
单个策略失败不影响其他策略继续执行。
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from strategies.registry import enabled_strategies, load_registry


def parse_args():
    parser = argparse.ArgumentParser(description="Run strategies listed in strategy_registry.yaml.")
    parser.add_argument("--all", action="store_true", help="列出全部策略（含未启用），不执行。")
    parser.add_argument("--trade-date", default=datetime.today().strftime("%Y%m%d"), help="交易日，格式 YYYYMMDD。")
    return parser.parse_args()


def _load_strategy_module(entry):
    script_path = os.path.join(PROJECT_ROOT, entry.script)
    spec = importlib.util.spec_from_file_location(f"strategies._runtime_{entry.name}", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_enabled(trade_date: str):
    """执行全部启用策略，返回逐策略结果列表。"""
    results = []
    for entry in enabled_strategies():
        try:
            module = _load_strategy_module(entry)
            if not hasattr(module, "run"):
                raise AttributeError(f"{entry.script} 未提供 run(trade_date) 入口。")
            output = module.run(trade_date)
            results.append({"name": entry.name, "success": True, "output": output, "error": None})
        except Exception as exc:
            results.append({"name": entry.name, "success": False, "output": None, "error": str(exc)})
    return results


def main():
    args = parse_args()
    if args.all:
        print("注册表中的全部策略：")
        for entry in load_registry():
            flag = "enabled" if entry.enabled else "disabled"
            print(f"- {entry.name} ({flag}, push={entry.push}) -> {entry.script}")
        return

    results = run_enabled(args.trade_date)
    if not results:
        print("当前没有启用的策略。可在 strategies/strategy_registry.yaml 中开启。")
        return

    print(f"策略运行完成（{args.trade_date}）：")
    for item in results:
        status = "OK " if item["success"] else "FAIL"
        detail = item["output"] if item["success"] else item["error"]
        print(f"[{status}] {item['name']}: {detail}")


if __name__ == "__main__":
    main()
