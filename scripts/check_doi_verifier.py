#!/usr/bin/env python3
"""DOI doğrulayıcısının ağsız ve deterministik testleri."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "turkish-clear-writing" / "scripts" / "verify_dois.py"
FIXTURE_PATH = ROOT / "tests" / "doi-fixtures.json"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_dois", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("verify_dois modülü yüklenemedi")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []

    if module.extract_dois("DOI: 10.1000/Ornek.1.") != ["10.1000/ornek.1"]:
        failures.append("DOI ayıklama/normalleştirme başarısız")

    valid = module.ReferenceRecord(
        doi="10.1000/ornek.1",
        source_title="Toprak verimliliğinde örnek bir yaklaşım",
        source_authors="Yılmaz, Ayşe and Kaya, Mehmet",
        source_year="2025",
    )
    mismatch = module.ReferenceRecord(
        doi="10.1000/ornek.2",
        source_title="Başka bir başlık",
        source_authors="Başka, Yazar",
        source_year="2020",
    )
    retracted = module.ReferenceRecord(doi="10.1000/ornek.3")
    network = module.ReferenceRecord(doi="10.1000/ornek.4")
    results = [module.verify_record(record, fixture=fixture) for record in [valid, mismatch, retracted, network]]
    statuses = [result["overall_status"] for result in results]
    expected = ["DOGRULANDI", "UYUSMAZLIK", "GERI_CEKME_UYARISI", "KONTROL_EDILEMEDI"]
    if statuses != expected:
        failures.append(f"durumlar beklenenden farklı: {statuses}")

    with tempfile.TemporaryDirectory(prefix="doi-dogrulama-test-") as tmp:
        output = Path(tmp)
        module.write_reports(results, output)
        required = {
            "doi-dogrulama-sonuclari.json",
            "doi-dogrulama-raporu.md",
            "doi-dogrulama-raporu.xlsx",
        }
        if not required.issubset({path.name for path in output.iterdir()}):
            failures.append("rapor dosyalarından biri üretilmedi")
        xlsx = output / "doi-dogrulama-raporu.xlsx"
        try:
            with zipfile.ZipFile(xlsx) as archive:
                names = set(archive.namelist())
                if "xl/worksheets/sheet1.xml" not in names or "xl/worksheets/sheet2.xml" not in names:
                    failures.append("XLSX çalışma sayfaları eksik")
                archive.testzip()
        except zipfile.BadZipFile:
            failures.append("XLSX geçerli bir OOXML paketi değil")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: DOI extraction, metadata matching, retraction warning, network uncertainty, and XLSX reports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
