import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_assignments(relative_path: str) -> dict[str, ast.AST]:
    source_path = PROJECT_ROOT / relative_path
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    assignments: dict[str, ast.AST] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name):
            assignments[target.id] = node.value
    return assignments


if __name__ == "__main__":
    unittest.main()
