#!/usr/bin/env python3
"""Context-aware Turkish editorial lint; it does NOT identify AI authorship."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

# Editorial patterns, not statistical classifiers. A match is a review prompt.
RULES = (
    ("TR001", "writing", "warning", r"\bgünümüzün\s+hızla\s+değişen\b", "Klişe açılış; konuya doğrudan girmeyi değerlendir."),
    ("TR002", "writing", "warning", r"\b(?:önemi\s+yadsınamaz|kritik\s+bir\s+rol\s+oynamaktadır)\b", "Genel/şişirilmiş ifade; somut, kanıta uygun bir yargı kur."),
    ("TR003", "syntax", "note", r"\b(?:sadece|yalnızca)\s+[^.!?\n]{2,100}?\s+değil\s*,\s*aynı\s+zamanda\b", "Karşıtlık veya ekleme anlamını koruyarak daha kısa söyleyip söyleyemeyeceğini incele."),
    ("TR004", "cohesion", "note", r"\b(?:bu\s+bağlamda|bu\s+doğrultuda|bununla\s+birlikte|öte\s+yandan)\b", "Bağlacın gerçek bir ilişki kurduğunu kontrol et; sırf kalıp diye silme."),
    ("TR005", "syntax", "note", r"\btarafından\s+(?:gerçekleştiril\w*|yapıl\w*|sağlan\w*)\b", "Eylemi kimin yaptığının açık olması gerekiyorsa etken çatıyı değerlendir."),
    ("TDK001", "spelling", "warning", r"\bbir\s+çok\b", "Bu anlamda 'birçok' bitişik yazılır."),
    ("TDK002", "spelling", "warning", r"\bbir\s+kaç\b", "Bu anlamda 'birkaç' bitişik yazılır."),
    ("TDK003", "spelling", "warning", r"\b(?:birşey|herşey|hiçbirşey)\b", "'Şey' ayrı yazılır: bir şey, her şey, hiçbir şey."),
    ("TDK004", "spelling", "warning", r"\byanısıra\b", "'Yanı sıra' ayrı yazılır."),
    ("TDK005", "spelling", "warning", r"\b(?:işbirliği|önyargı)\b", "TDK yazımını kontrol et: 'iş birliği', 'ön yargı'."),
    ("TDK006", "spelling", "warning", r"\b(?:ard\s+arda|yada)\b", "TDK yazımını kontrol et: 'art arda', 'ya da'."),
)
COMPILED = tuple((code, cat, sev, re.compile(pattern, re.IGNORECASE), advice)
                 for code, cat, sev, pattern, advice in RULES)
PROTECTED = re.compile(r"`[^`\n]*`|https?://[^\s<>]+|\b10\.\d{4,9}/[^\s,;()]+", re.IGNORECASE)
WORD = re.compile(r"\b[\wÇĞİÖŞÜçğıöşü]+\b", re.UNICODE)
MAKTADIR = re.compile(r"\b[\wçğıöşü]+m[ae]kt[ae]d[ıi]r\b", re.IGNORECASE)
NUMBER = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)*(?!\w)")
DOI = re.compile(r"\b10\.\d{4,9}/[^\s,;()]+", re.IGNORECASE)


def visible_text(source: str) -> str:
    """Mask fenced/inline code, URLs and DOIs while retaining offsets/line numbers."""
    lines = source.splitlines(keepends=True)
    result: list[str] = []
    fence: str | None = None
    for line in lines:
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            kind = marker.group(1)[0]
            if fence is None:
                fence = kind
            elif fence == kind:
                fence = None
            result.append(re.sub(r"[^\n]", " ", line))
            continue
        if fence is not None:
            result.append(re.sub(r"[^\n]", " ", line))
            continue
        result.append(line)
    masked = "".join(result)
    return PROTECTED.sub(lambda m: " " * len(m.group()), masked)


def audit_text(source: str, register: str = "academic") -> dict:
    if register not in {"academic", "institutional", "general", "technical"}:
        raise ValueError("unsupported register")
    visible = visible_text(source)
    findings: list[dict] = []
    for code, category, severity, pattern, advice in COMPILED:
        for match in pattern.finditer(visible):
            index = match.start()
            findings.append({
                "code": code, "category": category, "severity": severity,
                "line": source.count("\n", 0, index) + 1,
                "column": index - source.rfind("\n", 0, index),
                "match": source[match.start():match.end()], "advice": advice,
            })
    # Not a target for "human-like" prose. This is only a manual review prompt.
    words = WORD.findall(visible)
    verb_forms = list(MAKTADIR.finditer(visible))
    if len(verb_forms) >= 3 and len(verb_forms) / max(len(words), 1) > 0.025:
        first = verb_forms[0]
        index = first.start()
        findings.append({
            "code": "TR006", "category": "style", "severity": "note",
            "line": source.count("\n", 0, index) + 1,
            "column": index - source.rfind("\n", 0, index),
            "match": first.group(),
            "advice": "'-maktadır/-mektedir' tekrarını incele; akademik veya hukuki bağlamda doğru kullanımı koru.",
        })
    findings.sort(key=lambda f: (f["line"], f["column"], f["code"]))
    return {
        "schema_version": 1,
        "register": register,
        "notice": "Kural tabanlı editoryal ön taramadır; yapay zekâ yazarlığını saptamaz ve otomatik düzeltme yapmaz.",
        "stats": {"word_count": len(words), "maktadir_count": len(verb_forms), "finding_count": len(findings)},
        "findings": findings,
    }


def compare_anchors(source: str, revision: str) -> dict:
    """Compare only literal numerals/DOIs; matching tokens cannot prove semantic fidelity."""
    def diff(pattern: re.Pattern, a: str, b: str) -> dict:
        old = Counter(pattern.findall(a))
        new = Counter(pattern.findall(b))
        return {"missing": list((old - new).elements()), "added": list((new - old).elements())}

    return {
        "numbers": diff(NUMBER, source, revision),
        "dois": diff(DOI, source, revision),
        "notice": "Bu kontrol sözcük anlamı, nedensellik, yön, atıf kapsamı veya istatistiksel yorumu doğrulamaz; insan incelemesi gerekir.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="UTF-8 .txt/.md metni")
    parser.add_argument("--register", choices=["academic", "institutional", "general", "technical"], default="academic")
    parser.add_argument("--compare", type=Path, help="Düzenlenmiş metin: sayıları ve DOI'leri kaynakla karşılaştır")
    parser.add_argument("--json", action="store_true", help="Makinece okunabilir JSON çıktı")
    args = parser.parse_args()
    try:
        original = args.file.read_text(encoding="utf-8")
        report = audit_text(original, args.register)
        if args.compare:
            report["comparison"] = compare_anchors(original, args.compare.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as error:
        parser.error(str(error))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Türkçe editoryal denetim — {args.file.name} [{args.register}]")
        print(report["notice"])
        print(f"Kelime: {report['stats']['word_count']} | İnceleme önerisi: {report['stats']['finding_count']}")
        for f in report["findings"]:
            print(f"{f['line']}:{f['column']} {f['code']} ({f['severity']}): {f['match']!r} — {f['advice']}")
        if args.compare:
            print("Koruma kontrolü (sayısal değerler / DOI):")
            for kind in ("numbers", "dois"):
                print(f"  {kind}: {report['comparison'][kind]}")
            print(report["comparison"]["notice"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
