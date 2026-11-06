#!/usr/bin/env python3
"""Regression tests for the non-destructive Turkish editorial audit."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "turkish-clear-writing"
sys.path.insert(0, str(SKILL / "scripts"))
from audit_turkish import audit_text, compare_anchors, visible_text  # noqa: E402


class TestEditorialAudit(unittest.TestCase):
    def codes(self, text: str, register: str = "academic") -> list[str]:
        return [f["code"] for f in audit_text(text, register)["findings"]]

    def test_detects_high_confidence_spelling(self) -> None:
        self.assertTrue({"TDK001", "TDK003", "TDK004", "TDK005"}.issubset(
            self.codes("Bir çok bulgu var. Herşey yanısıra işbirliği sürüyor.")))

    def test_no_false_ai_verdict_for_scientific_prose(self) -> None:
        report = audit_text("Bununla birlikte sonuçlar anlamlı değildi (p = 0,08).", "academic")
        self.assertIn("TR004", [f["code"] for f in report["findings"]])
        self.assertNotIn("AI", [f["category"] for f in report["findings"]])
        self.assertIn("yazarlığını saptamaz", report["notice"])

    def test_flags_not_bans_rhetorical_structure(self) -> None:
        self.assertIn("TR003", self.codes("Sonuç sadece hızlı değil, aynı zamanda güvenilirdi."))
        self.assertEqual(self.codes("Sadece iki kişi geldi; bu sayı örneklemle sınırlıdır."), [])

    def test_preserves_markdown_code_and_urls(self) -> None:
        text = "```text\nbir çok\n```\n`bir çok` https://ornek.org/bir%20çok\nMetinde bir çok var."
        findings = audit_text(text)["findings"]
        self.assertEqual([f["code"] for f in findings], ["TDK001"])
        self.assertEqual(findings[0]["line"], 5)
        self.assertEqual(len(visible_text(text)), len(text))

    def test_reports_line_and_column(self) -> None:
        finding = audit_text("Önsöz.\nBir çok konu var.")["findings"][0]
        self.assertEqual((finding["line"], finding["column"]), (2, 1))

    def test_maktadir_repetition_only_is_note(self) -> None:
        text = "Çalışma yürütülmektedir. Sonuçlar değerlendirilmektedir. Yöntem incelenmektedir."
        findings = [f for f in audit_text(text)["findings"] if f["code"] == "TR006"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "note")
        self.assertEqual(self.codes("Çalışma yürütülmektedir."), [])

    def test_numeric_and_doi_compare(self) -> None:
        source = "Biyokütle %20 arttı (p = 0,04; DOI: 10.5555/example.1)."
        revision = "Biyokütle %25 arttı (p = 0,04; DOI: 10.5555/example.2)."
        report = compare_anchors(source, revision)
        self.assertIn("20", report["numbers"]["missing"])
        self.assertIn("25", report["numbers"]["added"])
        self.assertIn("10.5555/example.1", report["dois"]["missing"])

    def test_equal_tokens_do_not_prove_fidelity(self) -> None:
        comp = compare_anchors("Süre %38 arttı.", "Hız %38 arttı.")
        self.assertEqual(comp["numbers"], {"missing": [], "added": []})
        self.assertIn("doğrulamaz", comp["notice"])

    def test_cli_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.md"
            source.write_text("Bir çok örnek.", encoding="utf-8")
            p = subprocess.run(
                [sys.executable, str(SKILL / "scripts" / "audit_turkish.py"), str(source), "--json"],
                capture_output=True, text=True, check=True,
            )
            report = json.loads(p.stdout)
            self.assertEqual(report["stats"]["finding_count"], 1)
            self.assertEqual(report["findings"][0]["code"], "TDK001")


if __name__ == "__main__":
    unittest.main(verbosity=2)
