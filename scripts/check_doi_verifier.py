#!/usr/bin/env python3
"""DOI doğrulayıcısının ağsız ve deterministik testleri."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import zipfile
from unittest.mock import patch
from urllib.error import HTTPError


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

    # A web-tool URL-approval failure is NOT evidence of a bad DOI. Continue
    # with registry checks after a blocked DOI redirect and do not invent
    # invalidity when every external endpoint is inaccessible.
    standard_message = fixture["records"]["10.1000/ornek.1"]["message"]
    datacite_attrs = {
        "doi": valid.doi,
        "titles": [{"title": valid.source_title}],
        "creators": [{"givenName": "Ayşe", "familyName": "Yılmaz"}],
        "publicationYear": 2025,
        "publisher": "DataCite test publisher",
        "types": {"resourceTypeGeneral": "JournalArticle"},
    }
    cases = [
        ("blocked_resolver_crossref_ok",
         {"resolver_http_error": 403, "message": standard_message},
         "DOGRULANDI", "Crossref"),
        ("crossref_blocked_datacite_fallback",
         {"resolver_status": 200, "crossref_http_error": 403,
          "datacite_attributes": datacite_attrs},
         "DOGRULANDI", "DataCite"),
        ("crossref_404_datacite_found",
         {"resolver_status": 200, "crossref_http_error": 404,
          "datacite_attributes": datacite_attrs},
         "DOGRULANDI", "DataCite"),
        ("all_blocked",
         {"resolver_http_error": 403, "crossref_http_error": 403,
          "datacite_http_error": 429},
         "KONTROL_EDILEMEDI", ""),
        ("all_missing",
         {"resolver_http_error": 404, "crossref_http_error": 404,
          "datacite_http_error": 404},
         "COZUMLENEMEDI", ""),
        ("resolver_ok_both_registries_404",
         {"resolver_status": 200, "crossref_http_error": 404,
          "datacite_http_error": 404},
         "GECERLI_DOI_CROSSREF_DISI_INCELENMELI", ""),
        ("all_network_unavailable",
         {"resolver_network_error": "URL approval denied",
          "crossref_network_error": "URL approval denied",
          "datacite_network_error": "URL approval denied"},
         "KONTROL_EDILEMEDI", ""),
        ("crossref_wrong_doi",
         {"resolver_status": 200,
          "message": {**standard_message, "DOI": "10.1000/wrong-doi"},
          "datacite_http_error": 404},
         "KONTROL_EDILEMEDI", ""),
    ]
    for label, case, expected_status, registry in cases:
        got = module.verify_record(
            valid, fixture={"records": {valid.doi: case}}
        )
        if got["overall_status"] != expected_status:
            failures.append(f"{label}: expected {expected_status}, got {got['overall_status']}")
        if got["registry_source"] != registry:
            failures.append(f"{label}: unexpected registry {got['registry_source']}")
        if expected_status == "KONTROL_EDILEMEDI" and not got["access_issues"]:
            failures.append(f"{label}: access errors must be reported")
        if label == "crossref_blocked_datacite_fallback" and "geri çekme" not in got["note"]:
            failures.append(f"{label}: DataCite must not imply Crossref retraction clearance")

    # Exercise actual DataCite JSON:API parser with a mocked response; never
    # issue any external network request during regression tests.
    response = {"data": {"attributes": datacite_attrs}}
    with patch.object(module, "fetch_json", return_value=(200, "https://api.datacite.org", response)):
        parsed = module.datacite_message(valid.doi)
        if parsed["DOI"] != valid.doi or parsed["title"] != [valid.source_title]:
            failures.append("DataCite JSON:API parsing incorrect")
    with patch.object(module, "fetch_json", return_value=(200, "https://api.datacite.org",
                                                          {"data": {"attributes": {**datacite_attrs, "doi": "10.0000/other"}}})):
        try:
            module.datacite_message(valid.doi)
            failures.append("DataCite DOI mismatch was accepted")
        except ValueError:
            pass

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
    print("PASS: DOI metadata, Crossref/DataCite fallback, URL approval denial, non-invalidity, retraction and XLSX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
