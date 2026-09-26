import importlib.util
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "chains" / "ethereum-mainnet" / "ethereum_p2_bootstrap_verifier.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ethereum_p2_bootstrap_verifier", MOD_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EthereumP2BootstrapTests(unittest.TestCase):
    def test_only_https_and_no_embedded_credentials(self):
        m = load_module()
        m.validate_endpoint("https://eth.example")
        with self.assertRaises(ValueError):
            m.validate_endpoint("http://eth.example")
        with self.assertRaises(ValueError):
            m.validate_endpoint("https://user:pass@eth.example")

    def test_denied_methods_are_outside_allowlist(self):
        m = load_module()
        self.assertNotIn("eth_sendRawTransaction", m.ALLOWED_METHODS)
        self.assertIn("eth_sendRawTransaction", m.DENIED_METHODS)

    def test_best_head_quorum_uses_smallest_valid_span(self):
        m = load_module()
        heads = {"a": 100, "b": 101, "c": 110, "d": 102}
        chosen = m.best_head_quorum(heads, minimum=2, tolerance=2)
        self.assertEqual(chosen, ["a", "b"])

    def test_no_quorum_when_span_exceeds_tolerance(self):
        m = load_module()
        self.assertEqual(
            m.best_head_quorum({"a": 100, "b": 104}, minimum=2, tolerance=2),
            [],
        )

    def test_chain_id_parser_accepts_hex_only(self):
        m = load_module()
        self.assertEqual(m.parse_chain_id({"raw_result": "0x1"}), 1)
        self.assertIsNone(m.parse_chain_id({"raw_result": "not-hex"}))

    def test_report_is_not_overpromoted(self):
        m = load_module()
        rows = [
            {"endpoint_id": "a", "method": "eth_chainId", "classification": "SUCCESS", "raw_result": "0x1"},
            {"endpoint_id": "b", "method": "eth_chainId", "classification": "SUCCESS", "raw_result": "0x1"},
            {"endpoint_id": "a", "method": "eth_blockNumber", "classification": "SUCCESS", "raw_result": "0x64"},
            {"endpoint_id": "b", "method": "eth_blockNumber", "classification": "SUCCESS", "raw_result": "0x65"},
            {"endpoint_id": "a", "method": "eth_getBlockByNumber", "classification": "SUCCESS", "raw_result": {"number": "0x64"}},
            {"endpoint_id": "b", "method": "eth_getBlockByNumber", "classification": "SUCCESS", "raw_result": {"number": "0x65"}},
            {"endpoint_id": "a", "method": "eth_getCode", "classification": "SUCCESS", "raw_result": "0x6000"},
            {"endpoint_id": "b", "method": "eth_getCode", "classification": "SUCCESS", "raw_result": "0x6000"},
            {"endpoint_id": "a", "method": "eth_getStorageAt", "classification": "SUCCESS", "raw_result": "0x" + "00" * 32},
            {"endpoint_id": "b", "method": "eth_getStorageAt", "classification": "SUCCESS", "raw_result": "0x" + "00" * 32},
        ]
        report = m.build_report(rows, tolerance=2, min_identity=2, min_heads=2)
        self.assertEqual(report["promotion"]["sub_gate"], "CLOSED")
        self.assertEqual(report["promotion"]["overall_ethereum_p2"], "NOT_CLOSED")

    def test_capability_quorum_is_required_for_sub_gate(self):
        m = load_module()
        rows = [
            {"endpoint_id": "a", "method": "eth_chainId", "classification": "SUCCESS", "raw_result": "0x1"},
            {"endpoint_id": "b", "method": "eth_chainId", "classification": "SUCCESS", "raw_result": "0x1"},
            {"endpoint_id": "a", "method": "eth_blockNumber", "classification": "SUCCESS", "raw_result": "0x64"},
            {"endpoint_id": "b", "method": "eth_blockNumber", "classification": "SUCCESS", "raw_result": "0x65"},
            {"endpoint_id": "a", "method": "eth_getBlockByNumber", "classification": "SUCCESS", "raw_result": {"number": "0x64"}},
            {"endpoint_id": "b", "method": "eth_getBlockByNumber", "classification": "SUCCESS", "raw_result": {"number": "0x65"}},
            {"endpoint_id": "a", "method": "eth_getCode", "classification": "SUCCESS", "raw_result": "0x6000"},
            {"endpoint_id": "b", "method": "eth_getCode", "classification": "SUCCESS", "raw_result": "0x6000"},
            {"endpoint_id": "a", "method": "eth_getStorageAt", "classification": "SUCCESS", "raw_result": "0x" + "00" * 32},
        ]
        report = m.build_report(rows, tolerance=2, min_identity=2, min_heads=2)
        self.assertEqual(report["capability_quorum"]["eth_getCode"], ["a", "b"])
        self.assertEqual(report["capability_quorum"]["eth_getStorageAt"], ["a"])
        self.assertEqual(report["promotion"]["sub_gate"], "OPEN")

    def test_report_fails_closed_on_single_endpoint(self):
        m = load_module()
        rows = [
            {"endpoint_id": "a", "method": "eth_chainId", "classification": "SUCCESS", "raw_result": "0x1"},
            {"endpoint_id": "a", "method": "eth_blockNumber", "classification": "SUCCESS", "raw_result": "0x64"},
        ]
        report = m.build_report(rows, tolerance=2, min_identity=2, min_heads=2)
        self.assertEqual(report["promotion"]["sub_gate"], "OPEN")
        self.assertEqual(report["promotion"]["overall_ethereum_p2"], "NOT_CLOSED")

    def test_capability_error_is_not_chain_conflict(self):
        m = load_module()
        self.assertEqual(
            m.classify_method_observation({"transport_ok": True, "body": {"error": {"code": -32601}}}),
            "METHOD_UNAVAILABLE",
        )
        self.assertEqual(
            m.classify_method_observation({"transport_ok": False, "http_status": 429, "rate_limited": True}),
            "RATE_LIMITED",
        )


if __name__ == "__main__":
    unittest.main()
