#!/usr/bin/env python3
"""Kaynakçadaki DOI'leri çözümleyip metadata eşleşmesini raporlar.

Kaynak dosyaları değiştirilmez. Çıktılar JSON, Markdown ve bağımlılıksız XLSX'tir.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from html import unescape
import json
from pathlib import Path
import re
import ssl
import sys
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import zipfile


VERSION = "1.0.1"
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
SUPPORTED_TEXT = {".txt", ".md", ".bib", ".ris", ".json", ".csv", ".tsv"}


def verified_ssl_context() -> ssl.SSLContext:
    """Use Python's CA store, with the macOS system bundle as a verified fallback."""
    paths = ssl.get_default_verify_paths()
    if paths.cafile:
        return ssl.create_default_context()
    system_bundle = Path("/etc/ssl/cert.pem")
    if system_bundle.is_file():
        return ssl.create_default_context(cafile=str(system_bundle))
    return ssl.create_default_context()


@dataclass
class ReferenceRecord:
    doi: str
    source_file: str = ""
    source_context: str = ""
    source_title: str = ""
    source_authors: str = ""
    source_year: str = ""


def normalize_doi(value: str) -> str:
    value = unescape(value).strip()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)", "", value, flags=re.I)
    value = value.rstrip(".,;:")
    while value.endswith(")") and value.count(")") > value.count("("):
        value = value[:-1]
    return value.lower()


def normalize_text(value: str) -> str:
    value = (value or "").translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))
    value = unicodedata.normalize("NFKD", unescape(value or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[{}\\]", " ", value)
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value).lower()
    return " ".join(value.split())


def extract_dois(text: str) -> list[str]:
    seen: set[str] = set()
    dois: list[str] = []
    for match in DOI_PATTERN.finditer(text):
        doi = normalize_doi(match.group(0))
        if doi and doi not in seen:
            seen.add(doi)
            dois.append(doi)
    return dois


def _bib_entries(text: str) -> list[str]:
    entries: list[str] = []
    index = 0
    while True:
        match = re.search(r"@\w+\s*\{", text[index:], flags=re.I)
        if not match:
            break
        start = index + match.start()
        brace = index + match.end() - 1
        depth = 0
        end = None
        for position in range(brace, len(text)):
            if text[position] == "{":
                depth += 1
            elif text[position] == "}":
                depth -= 1
                if depth == 0:
                    end = position + 1
                    break
        if end is None:
            break
        entries.append(text[start:end])
        index = end
    return entries


def _bib_field(entry: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*", entry, flags=re.I)
    if not match:
        return ""
    index = match.end()
    if index >= len(entry):
        return ""
    opener = entry[index]
    if opener == "{":
        depth = 0
        for position in range(index, len(entry)):
            if entry[position] == "{":
                depth += 1
            elif entry[position] == "}":
                depth -= 1
                if depth == 0:
                    return entry[index + 1 : position].strip()
    if opener == '"':
        position = index + 1
        while position < len(entry):
            if entry[position] == '"' and entry[position - 1] != "\\":
                return entry[index + 1 : position].strip()
            position += 1
    end = entry.find(",", index)
    return entry[index : end if end >= 0 else len(entry)].strip()


def records_from_bib(text: str, source_file: str) -> list[ReferenceRecord]:
    records: list[ReferenceRecord] = []
    for entry in _bib_entries(text):
        doi_value = _bib_field(entry, "doi")
        dois = extract_dois(doi_value)
        if not dois:
            continue
        records.append(
            ReferenceRecord(
                doi=dois[0],
                source_file=source_file,
                source_context=" ".join(entry.split())[:500],
                source_title=_bib_field(entry, "title"),
                source_authors=_bib_field(entry, "author"),
                source_year=_bib_field(entry, "year"),
            )
        )
    return records


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    return unescape(re.sub(r"<[^>]+>", "", xml))


def records_from_file(path: Path) -> list[ReferenceRecord]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        text = read_docx_text(path)
    elif suffix in SUPPORTED_TEXT:
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"Desteklenmeyen dosya türü: {path.name}")
    if suffix == ".bib":
        return records_from_bib(text, str(path))

    records: list[ReferenceRecord] = []
    for line in text.splitlines() or [text]:
        for doi in extract_dois(line):
            years = YEAR_PATTERN.findall(line)
            records.append(
                ReferenceRecord(
                    doi=doi,
                    source_file=str(path),
                    source_context=" ".join(line.split())[:500],
                    source_year=years[0] if len(set(years)) == 1 else "",
                )
            )
    return records


def deduplicate(records: list[ReferenceRecord]) -> list[ReferenceRecord]:
    output: dict[str, ReferenceRecord] = {}
    for record in records:
        existing = output.get(record.doi)
        if existing is None:
            output[record.doi] = record
            continue
        for field in ("source_file", "source_context", "source_title", "source_authors", "source_year"):
            if not getattr(existing, field) and getattr(record, field):
                setattr(existing, field, getattr(record, field))
    return list(output.values())


def fetch_json(url: str, headers: dict[str, str], timeout: int = 25) -> tuple[int, str, object]:
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout, context=verified_ssl_context()) as response:
        body = response.read(5_000_000).decode("utf-8", errors="replace")
        return response.status, response.geturl(), json.loads(body)


def crossref_message(doi: str, mailto: str = "") -> dict:
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    if mailto:
        url += f"?mailto={quote(mailto, safe='@')}"
    headers = {"User-Agent": f"TurkishWritingSkills/{VERSION} DOI verifier"}
    status, _final_url, payload = fetch_json(url, headers)
    if status != 200 or not isinstance(payload, dict) or not isinstance(payload.get("message"), dict):
        raise ValueError("Crossref beklenen metadata biçimini döndürmedi.")
    return payload["message"]


def datacite_message(doi: str) -> dict:
    """Retrieve DataCite JSON API metadata as a minimal Crossref-style shape.

    DataCite's API is an independent alternate *registry lookup*, not a way
    to bypass an application's URL-approval or sandbox restrictions.
    """
    url = f"https://api.datacite.org/dois/{quote(doi, safe='')}"
    headers = {"User-Agent": f"TurkishWritingSkills/{VERSION} DOI verifier",
               "Accept": "application/vnd.api+json"}
    status, _url, payload = fetch_json(url, headers)
    attrs = payload.get("data", {}).get("attributes") if isinstance(payload, dict) else None
    if status != 200 or not isinstance(attrs, dict):
        raise ValueError("DataCite beklenen metadata biçimini döndürmedi.")
    actual = normalize_doi(str(attrs.get("doi", "")))
    if actual != normalize_doi(doi):
        raise ValueError("DataCite DOI alanı talep edilen DOI ile uyuşmuyor.")
    titles = [row.get("title", "") for row in attrs.get("titles", []) if isinstance(row, dict)]
    authors = []
    for author in attrs.get("creators", []) or []:
        if not isinstance(author, dict):
            continue
        given = author.get("givenName", "")
        family = author.get("familyName", "")
        if not given and not family:
            family = author.get("name", "")
        authors.append({"given": str(given), "family": str(family)})
    year = attrs.get("publicationYear")
    return {
        "DOI": actual, "title": titles, "author": authors,
        "published": {"date-parts": [[year]]} if isinstance(year, int) else {},
        "publisher": attrs.get("publisher", ""),
        "type": (attrs.get("types") or {}).get("resourceTypeGeneral", ""),
    }


def resolve_doi(doi: str) -> tuple[int, str]:
    headers = {
        "Accept": "application/vnd.citationstyles.csl+json, application/json;q=0.9, text/html;q=0.5",
        "User-Agent": f"TurkishWritingSkills/{VERSION} DOI verifier",
    }
    request = Request(f"https://doi.org/{quote(doi, safe='/')}", headers=headers)
    with urlopen(request, timeout=25, context=verified_ssl_context()) as response:
        response.read(4096)
        return response.status, response.geturl()


def metadata_year(message: dict) -> str:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        parts = message.get(key, {}).get("date-parts", []) if isinstance(message.get(key), dict) else []
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def metadata_authors(message: dict) -> str:
    authors = []
    for author in message.get("author", []) or []:
        if isinstance(author, dict):
            name = " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part)
            if name:
                authors.append(name)
    return "; ".join(authors)


def first_source_surname(authors: str) -> str:
    first = re.split(r"\s+and\s+|;", authors or "", maxsplit=1, flags=re.I)[0].strip()
    if not first:
        return ""
    if "," in first:
        return normalize_text(first.split(",", 1)[0])
    pieces = normalize_text(first).split()
    return pieces[-1] if pieces else ""


def update_notices(message: dict) -> list[dict]:
    notices: list[dict] = []
    for key in ("update-to", "updated-by"):
        values = message.get(key, []) or []
        if isinstance(values, dict):
            values = [values]
        for value in values:
            if not isinstance(value, dict):
                continue
            notices.append(
                {
                    "direction": key,
                    "type": str(value.get("type", "")),
                    "label": str(value.get("label", "")),
                    "source": str(value.get("source", "")),
                    "doi": normalize_doi(str(value.get("DOI", ""))),
                }
            )
    return notices


def match_value(source: str, registry: str, kind: str) -> str:
    if not source:
        return "KARSILASTIRILAMADI"
    if not registry:
        return "METADATA_EKSIK"
    if kind == "title":
        score = SequenceMatcher(None, normalize_text(source), normalize_text(registry)).ratio()
        return "ESLESIYOR" if score >= 0.85 else "UYUSMUYOR"
    if kind == "year":
        return "ESLESIYOR" if normalize_text(source) == normalize_text(registry) else "UYUSMUYOR"
    if kind == "author":
        surname = first_source_surname(source)
        return "ESLESIYOR" if surname and surname in normalize_text(registry).split() else "UYUSMUYOR"
    raise ValueError(kind)


def verify_record(record: ReferenceRecord, mailto: str = "", fixture: dict | None = None) -> dict:
    result = asdict(record)
    result.update({
        "resolver_status": "", "resolver_url": "", "registry_source": "",
        "registry_title": "", "registry_authors": "", "registry_year": "",
        "publisher": "", "type": "",
        "title_match": "KARSILASTIRILAMADI",
        "author_match": "KARSILASTIRILAMADI",
        "year_match": "KARSILASTIRILAMADI",
        "update_notice": "", "access_issues": "",
        "overall_status": "", "note": "",
    })
    item = fixture.get("records", {}).get(record.doi) if fixture is not None else None
    if fixture is not None and item is None:
        result["overall_status"] = "KONTROL_EDILEMEDI"
        result["note"] = "Bu DOI için test kaydı yok; kayıt yokluğundan geçersizlik çıkarılamaz."
        return result

    issues = []
    resolved = False
    resolver_missing = False

    def issue(where: str, detail: str) -> None:
        issues.append(f"{where}: {detail}")
        result["access_issues"] = "; ".join(issues)

    def http_error(code: int, url: str) -> HTTPError:
        return HTTPError(url, code, "fixture HTTP error", {}, None)

    # Resolver failure must NEVER prevent an independent registry lookup.
    try:
        if fixture is None:
            status, final_url = resolve_doi(record.doi)
        else:
            if item.get("network_error") or item.get("resolver_network_error"):
                raise URLError(item.get("network_error") or item["resolver_network_error"])
            if item.get("resolver_http_error"):
                raise http_error(int(item["resolver_http_error"]), record.doi)
            status = int(item.get("resolver_status", 200))
            final_url = item.get("resolver_url", f"https://doi.org/{record.doi}")
        if not 200 <= status < 400:
            raise http_error(status, record.doi)
        resolved = True
        result["resolver_status"] = f"HTTP {status}"
        result["resolver_url"] = final_url
    except HTTPError as error:
        result["resolver_status"] = f"HTTP {error.code}"
        resolver_missing = error.code == 404
        issue("DOI resolver", f"HTTP {error.code}")
    except (URLError, TimeoutError, OSError, ValueError) as error:
        result["resolver_status"] = "ERISIM_HATASI"
        issue("DOI resolver", f"erişim/yanıt hatası: {error}")

    # Prefer Crossref, but a 404 there only means NOT REGISTERED AT CROSSREF.
    message = None
    crossref_missing = False
    try:
        if fixture is None:
            message = crossref_message(record.doi, mailto)
        else:
            if item.get("crossref_network_error"):
                raise URLError(item["crossref_network_error"])
            if item.get("crossref_http_error"):
                raise http_error(int(item["crossref_http_error"]), record.doi)
            if "message" not in item:
                raise http_error(404, record.doi)
            message = item["message"]
        if not isinstance(message, dict):
            raise ValueError("Crossref metadata nesnesi bekleniyordu")
        recorded = normalize_doi(str(message.get("DOI", "")))
        if recorded != record.doi:
            raise ValueError("Crossref yanıtı istenen DOI ile uyuşmuyor")
        result["registry_source"] = "Crossref"
    except HTTPError as error:
        message = None
        crossref_missing = error.code == 404
        issue("Crossref", f"HTTP {error.code}")
    except (URLError, TimeoutError, OSError, ValueError) as error:
        message = None
        issue("Crossref", f"erişim/metadata hatası: {error}")

    # DataCite is a second registry, not an alternative claim of Crossref
    # retraction coverage. No inference of invalidity from inaccessible APIs.
    datacite_missing = False
    if message is None:
        try:
            if fixture is None:
                message = datacite_message(record.doi)
            else:
                if item.get("datacite_network_error"):
                    raise URLError(item["datacite_network_error"])
                if item.get("datacite_http_error"):
                    raise http_error(int(item["datacite_http_error"]), record.doi)
                if "datacite_attributes" not in item:
                    raise http_error(404, record.doi)
                attrs = item["datacite_attributes"]
                if normalize_doi(str(attrs.get("doi", ""))) != record.doi:
                    raise ValueError("DataCite DOI alanı istenen DOI ile uyuşmuyor")
                message = {
                    "DOI": record.doi,
                    "title": [x.get("title", "") for x in attrs.get("titles", [])],
                    "author": [{"given": x.get("givenName", ""),
                                "family": x.get("familyName", x.get("name", ""))}
                               for x in attrs.get("creators", [])],
                    "published": {"date-parts": [[attrs["publicationYear"]]]}
                                 if isinstance(attrs.get("publicationYear"), int) else {},
                    "publisher": attrs.get("publisher", ""),
                    "type": (attrs.get("types") or {}).get("resourceTypeGeneral", ""),
                }
            result["registry_source"] = "DataCite"
        except HTTPError as error:
            datacite_missing = error.code == 404
            issue("DataCite", f"HTTP {error.code}")
        except (URLError, TimeoutError, OSError, ValueError) as error:
            issue("DataCite", f"erişim/metadata hatası: {error}")

    if message is None:
        if resolved and crossref_missing and datacite_missing:
            result["overall_status"] = "GECERLI_DOI_CROSSREF_DISI_INCELENMELI"
            result["note"] = (
                "DOI yönlendiricisi çalıştı ancak iki kayıt servisinde metadata bulunmadı. "
                "Diğer kayıt ajansını/yayıncıyı elle inceleyin."
            )
        elif resolver_missing and crossref_missing and datacite_missing:
            result["overall_status"] = "COZUMLENEMEDI"
            result["note"] = (
                "DOI yönlendiricisi ve iki kayıt servisi 404 döndürdü; olası yazım "
                "hatasını ve asıl kaynağı kontrol edin. Bu, kesin geçersizlik hükmü değildir."
            )
        else:
            result["overall_status"] = "KONTROL_EDILEMEDI"
            result["note"] = (
                "Erişim, bağlantı izni veya servis yanıtı nedeniyle bibliyografik doğrulama "
                "tamamlanamadı. Bu sonuç DOI'nin geçersiz olduğunu göstermez."
            )
        return result

    title = (" ".join(message.get("title", [])[:1])
             if isinstance(message.get("title"), list)
             else str(message.get("title", "")))
    authors = metadata_authors(message)
    year = metadata_year(message)
    result.update({
        "registry_title": title, "registry_authors": authors,
        "registry_year": year, "publisher": str(message.get("publisher", "")),
        "type": str(message.get("type", "")),
        "title_match": match_value(record.source_title, title, "title"),
        "author_match": match_value(record.source_authors, authors, "author"),
        "year_match": match_value(record.source_year, year, "year"),
    })
    notices = update_notices(message) if result["registry_source"] == "Crossref" else []
    result["update_notice"] = "; ".join(
        f"{notice['type'] or notice['label']} ({notice['source'] or 'kaynak belirtilmemiş'}; {notice['doi'] or 'DOI yok'})"
        for notice in notices
    )
    notice_text = normalize_text(result["update_notice"])
    comparisons = [result[key] for key in ("title_match", "author_match", "year_match")]
    source = result["registry_source"]
    if any(word in notice_text for word in ("retraction", "withdrawal", "geri cek")):
        result["overall_status"] = "GERI_CEKME_UYARISI"
        result["note"] = "Crossref metadata kaydında geri çekme bildirimi bulundu; asıl bildirimi kontrol edin."
    elif result["update_notice"]:
        result["overall_status"] = "GUNCELLEME_UYARISI"
        result["note"] = "Güncelleme bildirimi bulundu; yayının asıl kaydını inceleyin."
    elif "UYUSMUYOR" in comparisons:
        result["overall_status"] = "UYUSMAZLIK"
        result["note"] = (
            f"Kaynakçadaki bibliyografik bilgi {source} metadata kaydıyla uyuşmuyor; "
            "asıl kaynağa bakmadan düzeltmeyin."
        )
    elif any(value == "ESLESIYOR" for value in comparisons):
        result["overall_status"] = "DOGRULANDI"
        result["note"] = (
            f"Sağlanan bibliyografik alanlar {source} kayıt bilgileriyle eşleşti. "
            + ("DOI yönlendirmesi de çalıştı." if resolved else
               "DOI yönlendiricisi bağımsız doğrulanamadı.")
        )
    else:
        result["overall_status"] = "GECERLI_DOI_METADATA_INCELENMELI"
        result["note"] = (
            f"{source} metadata kaydı bulundu; ancak karşılaştırılabilir yeterli "
            "kaynakça bilgisi yok."
        )
    if source == "DataCite":
        result["note"] += (
            " DataCite kaydı Crossref geri çekme/düzeltme taramasının yerini almaz; "
            "yayıncı ve güncel bildirimler ayrıca kontrol edilmelidir."
        )
    return result


REPORT_FIELDS = [
    ("DOI", "doi"),
    ("Genel_Durum", "overall_status"),
    ("Cozumleme", "resolver_status"),
    ("Kayit_Ajansi", "registry_source"),
    ("Erisim_Sorunlari", "access_issues"),
    ("Kaynak_Baslik", "source_title"),
    ("Kayit_Baslik", "registry_title"),
    ("Baslik_Eslesmesi", "title_match"),
    ("Kaynak_Yazar", "source_authors"),
    ("Kayit_Yazar", "registry_authors"),
    ("Yazar_Eslesmesi", "author_match"),
    ("Kaynak_Yil", "source_year"),
    ("Kayit_Yil", "registry_year"),
    ("Yil_Eslesmesi", "year_match"),
    ("Yayinci", "publisher"),
    ("Kayit_Turu", "type"),
    ("Guncelleme_Uyarisi", "update_notice"),
    ("Not", "note"),
    ("Kaynak_Dosya", "source_file"),
    ("Cozumlenen_URL", "resolver_url"),
]


def column_name(index: int) -> str:
    output = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        output = chr(65 + remainder) + output
    return output


def worksheet_xml(rows: list[list[object]]) -> str:
    row_xml = []
    for row_index, row in enumerate(rows, 1):
        cells = []
        for column_index, value in enumerate(row, 1):
            reference = f"{column_name(column_index)}{row_index}"
            style = ' s="1"' if row_index == 1 else ""
            cells.append(
                f'<c r="{reference}" t="inlineStr"{style}><is><t xml:space="preserve">{escape(str(value or ""))}</t></is></c>'
            )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        '<sheetData>' + "".join(row_xml) + '</sheetData><autoFilter ref="A1:'
        + column_name(len(rows[0]) if rows else 1) + str(len(rows) if rows else 1) + '"/></worksheet>'
    )


def write_xlsx(path: Path, sheets: list[tuple[str, list[list[object]]]]) -> None:
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    for index in range(1, len(sheets) + 1):
        content_types.append(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content_types.append("</Types>")

    workbook_sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, (name, _rows) in enumerate(sheets, 1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + workbook_sheets + "</sheets></workbook>"
    )
    relationships = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, len(sheets) + 1)
    )
    relationships += f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    workbook_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + relationships + "</Relationships>"
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    styles = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Arial"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF2F6B3C"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "".join(content_types))
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", styles)
        for index, (_name, rows) in enumerate(sheets, 1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", worksheet_xml(rows))


def write_reports(results: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "doi-dogrulama-sonuclari.json").write_text(
        json.dumps({"verifier_version": VERSION, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    counts: dict[str, int] = {}
    for result in results:
        counts[result["overall_status"]] = counts.get(result["overall_status"], 0) + 1
    markdown = ["# DOI doğrulama raporu", "", f"Toplam DOI: {len(results)}", ""]
    for status, count in sorted(counts.items()):
        markdown.append(f"- `{status}`: {count}")
    markdown.extend(["", "| DOI | Durum | Başlık | Yıl | Güncelleme |", "|---|---|---|---|---|"])
    for result in results:
        safe = lambda value: str(value or "").replace("|", "\\|").replace("\n", " ")
        markdown.append(
            f"| {safe(result['doi'])} | {safe(result['overall_status'])} | {safe(result['registry_title'])} | "
            f"{safe(result['registry_year'])} | {safe(result['update_notice'])} |"
        )
    markdown.extend(
        [
            "",
            "## Sınırlılık",
            "",
            "Uyarı bulunmaması, yayının kesinlikle düzeltilmediğini veya geri çekilmediğini kanıtlamaz. "
            "Crossref ve Retraction Watch kapsamı ile yayıncı metadata kalitesi değişebilir. Kritik kayıtları yayıncı sayfasından doğrulayın.",
        ]
    )
    (output_dir / "doi-dogrulama-raporu.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")

    detail_rows = [[header for header, _key in REPORT_FIELDS]]
    detail_rows.extend([[result.get(key, "") for _header, key in REPORT_FIELDS] for result in results])
    summary_rows = [["Durum", "Sayi"]] + [[status, count] for status, count in sorted(counts.items())]
    summary_rows.extend(
        [
            [],
            ["Not", "Uyarı bulunmaması kesin temiz kayıt anlamına gelmez; kritik sonuçları yayıncı sayfasından doğrulayın."],
        ]
    )
    write_xlsx(output_dir / "doi-dogrulama-raporu.xlsx", [("DOI_Kontrol", detail_rows), ("Ozet", summary_rows)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, help="TXT, MD, BIB, RIS, JSON, CSV, TSV veya DOCX kaynakça dosyaları")
    parser.add_argument("--doi", action="append", default=[], help="Doğrudan kontrol edilecek DOI; birden çok kez kullanılabilir")
    parser.add_argument("--output", type=Path, default=Path("doi-dogrulama"), help="Rapor klasörü")
    parser.add_argument("--mailto", default="", help="Crossref polite pool için isteğe bağlı e-posta")
    parser.add_argument("--fixture", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    records = [ReferenceRecord(doi=normalize_doi(value), source_context=value) for value in args.doi if normalize_doi(value)]
    failures = []
    for path in args.inputs:
        try:
            records.extend(records_from_file(path))
        except (OSError, ValueError, zipfile.BadZipFile, KeyError) as error:
            failures.append(f"{path}: {error}")
    records = deduplicate(records)
    if failures:
        for failure in failures:
            print(f"UYARI: {failure}", file=sys.stderr)
    if not records:
        print("HATA: Kontrol edilecek DOI bulunamadı.", file=sys.stderr)
        return 2

    fixture = json.loads(args.fixture.read_text(encoding="utf-8")) if args.fixture else None
    results = [verify_record(record, args.mailto, fixture) for record in records]
    write_reports(results, args.output)
    for result in results:
        print(f"{result['doi']}: {result['overall_status']}")
    print(f"Rapor: {args.output.resolve()}")
    critical = {
        "COZUMLENEMEDI",
        "GECERLI_DOI_CROSSREF_DISI_INCELENMELI",
        "UYUSMAZLIK",
        "GUNCELLEME_UYARISI",
        "GERI_CEKME_UYARISI",
        "KONTROL_EDILEMEDI",
    }
    return 1 if any(result["overall_status"] in critical for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
