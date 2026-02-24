import ast
import os
import re
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from data_engine.tushare_api import TushareDataEngine


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


class ConfigSecurityTest(unittest.TestCase):
    def test_sensitive_environment_values_have_no_default(self):
        assignments = load_assignments("common/config.py")

        for name in ("TUSHARE_TOKEN", "FEISHU_BOT_WEBHOOK"):
            with self.subTest(name=name):
                call = assignments[name]
                self.assertIsInstance(call, ast.Call)
                self.assertEqual(len(call.args), 1)

    def test_env_example_documents_required_credentials(self):
        content = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("TUSHARE_TOKEN=", content)
        self.assertIn("FEISHU_BOT_WEBHOOK=", content)

    def test_custom_tushare_gateway_is_opt_in(self):
        assignments = load_assignments("common/config.py")
        call = assignments["TUSHARE_HTTP_URL"]

        self.assertIsInstance(call, ast.Call)
        self.assertEqual(len(call.args), 2)
        self.assertIsInstance(call.args[1], ast.Constant)
        self.assertEqual(call.args[1].value, "")
        env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("TUSHARE_HTTP_URL=\n", env_example.replace("\r\n", "\n"))

    def test_data_engine_rejects_cleartext_custom_gateway(self):
        with patch("data_engine.tushare_api.ts.pro_api"):
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                TushareDataEngine(token="test-token", http_url="http://example.com")

    def test_tracked_text_files_do_not_contain_live_credentials(self):
        raw_paths = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=PROJECT_ROOT,
        )
        tracked_paths = [os.fsdecode(value) for value in raw_paths.split(b"\0") if value]
        patterns = {
            "Feishu webhook": re.compile(
                r"https://open\.feishu\.cn/open-apis/bot/v2/hook/"
                r"(?!your_webhook_id_here)[^\s`\"']{12,}"
            ),
            "Tushare token assignment": re.compile(
                r"TUSHARE_TOKEN\s*=\s*[\"']?[A-Za-z0-9]{20,}"
            ),
        }
        findings = []
        for relative_path in tracked_paths:
            path = PROJECT_ROOT / relative_path
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            for label, pattern in patterns.items():
                if pattern.search(content):
                    findings.append(f"{relative_path}: {label}")

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
