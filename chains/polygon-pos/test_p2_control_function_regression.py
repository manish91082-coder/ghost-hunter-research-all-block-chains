#!/usr/bin/env python3
import ast
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLYGON_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(POLYGON_DIR))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


VERIFIER = load_module(
    "p2_control_function_verifier",
    POLYGON_DIR / "polygon_p2_control_function_verifier.py",
)
RECONCILER = load_module(
    "p2_control_function_reconciliation",
    POLYGON_DIR / "polygon_p2_control_function_reconciliation.py",
)
READONLY = load_module(
    "polygon_readonly_verifier_test",
    POLYGON_DIR / "polygon_readonly_verifier.py",
)


class ControlFunctionRegressionTests(unittest.TestCase):
    def test_target_manifest(self):
        targets = VERIFIER.load_targets(
            str(POLYGON_DIR / "p2_control_function_targets.txt")
        )
        self.assertEqual(len(targets), 8)
        self.assertTrue(all(target["calldata"].startswith("0x") for target in targets))
        self.assertTrue(all(len(target["parent"]) == 42 for target in targets))

    def test_read_only_method_allowlist_contains_eth_call(self):
        self.assertIn("eth_call", READONLY.ALLOWED)
        self.assertNotIn("eth_sendTransaction", READONLY.ALLOWED)

    def test_no_stale_successful_name_reference(self):
        source = (POLYGON_DIR / "polygon_p2_control_function_verifier.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        loaded_successful = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and node.id == "successful"
            and isinstance(node.ctx, ast.Load)
        ]
        self.assertEqual(
            loaded_successful,
            [],
            "control verifier must use the observed evidence set, not stale successful[]",
        )

    def test_matching_success_fingerprint(self):
        a = {"outcome": {"ok": True, "result": "0x1234"}}
        b = {"outcome": {"ok": True, "result": "0x1234"}}
        self.assertEqual(RECONCILER.fingerprint(a), RECONCILER.fingerprint(b))

    def test_matching_error_fingerprint(self):
        a = {"outcome": {"ok": False, "error_code": -32000}}
        b = {"outcome": {"ok": False, "error_code": -32000}}
        self.assertEqual(RECONCILER.fingerprint(a), RECONCILER.fingerprint(b))


    def test_transport_failure_is_not_evidence(self):
        row = {"outcome": {"ok": False, "http_status": 403, "error_message": "Forbidden"}}
        self.assertIsNone(RECONCILER.fingerprint(row))

    def test_conflicting_outcomes_do_not_match(self):
        a = {"outcome": {"ok": True, "result": "0x1234"}}
        b = {"outcome": {"ok": False, "error_code": -32000}}
        self.assertNotEqual(RECONCILER.fingerprint(a), RECONCILER.fingerprint(b))


if __name__ == "__main__":
    unittest.main()
