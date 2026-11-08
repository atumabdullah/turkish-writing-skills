#!/usr/bin/env python3
"""Conservative methodology consistency audit for structured research protocols.

Not a substitute for peer review, ethics approval, design validation, source
verification, power analysis or re-analysis of original research data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

VERSION = "1.0.0"
DESIGNS = {
    "single_factor_experiment", "factorial_experiment", "repeated_measures_experiment",
    "randomized_trial", "observational_cross_sectional", "observational_cohort",
    "case_control", "systematic_review", "qualitative", "other",
}
EXPERIMENTS = {
    "single_factor_experiment", "factorial_experiment",
    "repeated_measures_experiment", "randomized_trial",
}
OBSERVATIONAL = {"observational_cross_sectional", "observational_cohort", "case_control"}
STATUS = {"yes", "no", "unknown", "not_applicable"}
INDEPENDENT_TESTS = {"one_way_anova", "factorial_anova", "t_test", "welch_anova"}
DEPENDENCE_AWARE = {"mixed_model", "multilevel_model", "gee", "cluster_robust_regression"}
GUIDELINES = {
    "randomized_trial": ("CONSORT", "https://www.consort-spirit.org/"),
    "observational_cross_sectional": ("STROBE", "https://www.strobe-statement.org/"),
    "observational_cohort": ("STROBE", "https://www.strobe-statement.org/"),
    "case_control": ("STROBE", "https://www.strobe-statement.org/"),
    "systematic_review": ("PRISMA", "https://www.prisma-statement.org/"),
    "qualitative": ("SRQR/COREQ", "https://www.equator-network.org/"),
}


def args_parser() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("protocol", type=Path, help="Structured JSON protocol, not free-form PDF or Word")
    p.add_argument("--analysis-results", type=Path, help="Optional advanced_statistics.py results.json")
    p.add_argument("--figure-metadata", type=Path, help="Optional interaction_metadata.json")
    p.add_argument("--output", type=Path, default=Path("methodology-audit"))
    p.add_argument("--fail-on-high", action="store_true", help="Exit code 3 for high-severity findings")
    return p.parse_args()


def read_json(path: Path, label: str) -> tuple[dict, str]:
    if not path.is_file() or path.suffix.lower() != ".json":
        raise ValueError(f"{label}: existing JSON file required")
    content = path.read_bytes()
    try:
        data = json.loads(content.decode("utf-8-sig"),
                          parse_constant=lambda val: (_ for _ in ()).throw(ValueError(val)))
    except (UnicodeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid strict UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label}: JSON root must be an object")
    return data, hashlib.sha256(content).hexdigest()


def section(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def string(parent: dict, key: str) -> str | None:
    val = parent.get(key)
    if val is None or val == "":
        return None
    if not isinstance(val, str):
        raise ValueError(f"{key} must be string or null")
    return val.strip() or None


def yesno(parent: dict, key: str) -> str:
    val = parent.get(key, "unknown")
    if val is None:
        val = "unknown"
    if not isinstance(val, str) or val not in STATUS:
        raise ValueError(f"{key} must be yes, no, unknown or not_applicable")
    return val


def boolean(parent: dict, key: str) -> bool | None:
    val = parent.get(key)
    if val is None or val == "unknown":
        return None
    if not isinstance(val, bool):
        raise ValueError(f"{key} must be boolean or unknown/null")
    return val


def integer(parent: dict, key: str) -> int | None:
    val = parent.get(key)
    if val is None:
        return None
    if isinstance(val, bool) or not isinstance(val, int) or val < 1:
        raise ValueError(f"{key} must be positive integer or null")
    return val


def string_list(parent: dict, key: str) -> list[str]:
    val = parent.get(key, [])
    if val is None:
        val = []
    if not isinstance(val, list) or any(not isinstance(x, str) or not x.strip() for x in val):
        raise ValueError(f"{key} must be an array of nonempty strings")
    values = [x.strip() for x in val]
    if len(set(values)) != len(values):
        raise ValueError(f"{key} contains duplicate values")
    return values


def parse_factors(sampling: dict) -> list[dict]:
    raw = sampling.get("factors", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise ValueError("sampling.factors must be an array")
    result = []
    for i, factor in enumerate(raw):
        if not isinstance(factor, dict) or not string(factor, "name"):
            raise ValueError(f"sampling.factors[{i}] needs a name")
        levels = string_list(factor, "levels")
        if len(levels) == 1:
            raise ValueError(f"sampling.factors[{i}].levels needs 0 or >=2 levels")
        result.append({"name": string(factor, "name"), "levels": levels})
    if len({x["name"] for x in result}) != len(result):
        raise ValueError("sampling factor names must be distinct")
    return result


def finding(report: dict, code: str, severity: str, kind: str, domain: str,
            title: str, paths: list[str], rationale: str, recommendation: str) -> None:
    assert severity in {"high", "medium", "info"}
    assert kind in {"confirmed_inconsistency", "documentation_gap", "review_point"}
    report["findings"].append({
        "id": code, "severity": severity, "classification": kind, "domain": domain,
        "title": title, "evidence_paths": paths, "rationale": rationale,
        "recommended_action": recommendation,
    })


def audit(protocol: dict, filename: str, fingerprint: str, linked: dict | None = None,
          linked_sha: str | None = None, figure: dict | None = None,
          figure_sha: str | None = None) -> dict:
    if protocol.get("schema_version") != "1.0":
        raise ValueError("schema_version must equal '1.0'")
    study, sampling, procedures, measurement, analysis, ethics, reporting = [
        section(protocol, name) for name in
        ("study", "sampling", "procedures", "measurements", "analysis", "ethics", "reporting")
    ]
    design = string(study, "design")
    if design and design not in DESIGNS:
        raise ValueError("study.design is not a recognized design enum")
    factors = parse_factors(sampling)
    methods = string_list(analysis, "methods")
    unit = string(sampling, "unit_of_analysis")
    assignment = string(sampling, "unit_of_randomization")
    observation = string(sampling, "unit_of_observation")
    n = integer(sampling, "independent_units")
    reps = integer(sampling, "replicates_per_cell")
    subsamples = integer(sampling, "technical_subsamples_per_unit")
    repeated = boolean(sampling, "repeated_measurements")
    clustered = boolean(sampling, "clustered")
    human = boolean(ethics, "human_participants")
    animal = boolean(ethics, "animal_research")
    randomization = yesno(procedures, "randomization")
    timepoints = measurement.get("timepoints", [])
    if not isinstance(timepoints, list) or any(
        isinstance(t, bool) or not isinstance(t, (str, int, float)) or
        (isinstance(t, float) and not math.isfinite(t)) for t in timepoints
    ):
        raise ValueError("measurements.timepoints must contain strings or finite numbers")
    if len({str(x) for x in timepoints}) != len(timepoints):
        raise ValueError("measurements.timepoints cannot contain duplicates")

    result = {
        "engine_version": VERSION, "input_filename": filename,
        "protocol_sha256": fingerprint, "analysis_results_sha256": linked_sha,
        "figure_metadata_sha256": figure_sha, "study_design": design,
        "design_verified": False, "quality_score": None, "findings": [],
        "scope": {"protocol": True, "linked_statistics": linked is not None,
                  "linked_interaction_figure": figure is not None},
        "limitations": [
            "Rules only inspect supplied structured claims and internal consistency.",
            "Unknown or absent information is not proof of misconduct or invalid methods.",
            "Randomization, ethics, measurements, raw data, model adequacy and causal validity were not independently verified.",
            "Reporting checklists support transparent reporting; they are not design-quality assessment instruments.",
            "No statistical tests, power calculations, p-values or new scientific results are computed.",
        ],
    }

    def add(code, severity, kind, domain, title, paths, why, action):
        finding(result, code, severity, kind, domain, title, paths, why, action)

    if not string(study, "research_question"):
        add("M001", "medium", "documentation_gap", "design",
            "Araştırma sorusu eksik.", ["study.research_question"],
            "Study goals cannot be reconciled with outcomes.", "Soruyu ve hedeflenen karşılaştırmayı açıkça yazın.")
    if not design:
        add("M002", "high", "documentation_gap", "design",
            "Araştırma deseni belirtilmemiş.", ["study.design"],
            "Analysis choices cannot be checked without the study design.", "Gerçek araştırma desenini tanımlayın.")
    if not unit:
        add("M003", "high", "documentation_gap", "sampling",
            "Bağımsız analiz birimi tanımlanmamış.", ["sampling.unit_of_analysis"],
            "Pseudoreplication cannot be checked without a unit definition.",
            "Saksı, parsel, katılımcı veya bağımsız küme düzeyini belirtin.")
    if n is None:
        add("M004", "medium", "documentation_gap", "sampling",
            "Bağımsız birim sayısı eksik.", ["sampling.independent_units"],
            "Measured values need not equal independent replicates.", "Ölçüm sayısından ayrı gerçek bağımsız n değerini yazın.")

    if design in EXPERIMENTS:
        if randomization in {"no", "not_applicable"}:
            hard = design == "randomized_trial"
            add("M010", "high" if hard else "medium",
                "confirmed_inconsistency" if hard else "review_point", "internal_validity",
                "Deneyde randomizasyon yapılmadığı bildirilmiş.",
                ["study.design", "procedures.randomization"],
                "Allocation bias or an incorrect randomized-trial claim is possible.",
                "Randomizasyon iddiasını düzeltin veya eksik randomizasyonu sınırlılık olarak açıklayın.")
        elif randomization == "unknown":
            add("M011", "medium", "documentation_gap", "internal_validity",
                "Randomizasyon durumu belirtilmemiş.", ["procedures.randomization"],
                "Allocation reproducibility cannot be assessed.",
                "Randomizasyonun yapılıp yapılmadığını ve nasıl uygulandığını açıklayın.")
        elif not string(procedures, "randomization_method"):
            add("M012", "medium", "documentation_gap", "internal_validity",
                "Randomizasyon uygulama yöntemi eksik.", ["procedures.randomization_method"],
                "A yes flag does not document allocation generation.",
                "Rastgele sayı üretimini, kısıtları ve tahsis yöntemini açıklayın.")
        if yesno(procedures, "control_group") in {"no", "unknown"}:
            add("M013", "medium", "review_point", "design",
                "Karşılaştırma veya kontrol koşulu net değil.", ["procedures.control_group"],
                "Some active comparator studies are valid without untreated controls.",
                "Kontrol grubu yerine aktif karşılaştırma varsa gerekçelendirin.")
        if not string(procedures, "sample_size_justification"):
            add("M014", "medium", "documentation_gap", "sampling",
                "Tekerrür veya örneklem gerekçesi eksik.",
                ["procedures.sample_size_justification"],
                "Replication count alone does not establish precision or power.",
                "Güç, duyarlılık, önceki çalışma veya kaynak sınırını belgeleyin.")
        if yesno(procedures, "blinding") == "unknown":
            add("M015", "info", "documentation_gap", "internal_validity",
                "Körleme durumu belirtilmemiş.", ["procedures.blinding"],
                "Observer blinding can matter when feasible.",
                "Körleme durumunu veya uygulanamama nedenini açıklayın.")
    if design == "randomized_trial" and yesno(procedures, "allocation_concealment") == "unknown":
        add("M016", "medium", "documentation_gap", "internal_validity",
            "Tahsis gizliliği bildirilmemiş.", ["procedures.allocation_concealment"],
            "Selection bias assessment requires details of allocation concealment.",
            "Tahsis gizliliğinin nasıl korunduğunu veya uygulanamadığını açıklayın.")

    if assignment and unit and assignment != unit:
        aware = clustered is True and any(m in DEPENDENCE_AWARE for m in methods)
        add("M020", "info" if aware else "high", "review_point", "pseudoreplication",
            "Tahsis birimi ile analiz birimi farklı.",
            ["sampling.unit_of_randomization", "sampling.unit_of_analysis", "analysis.methods"],
            "Data may be dependent within assigned clusters.",
            "Küme düzeyi ve kovaryans/serbestlik derecesi modellemesini doğrulayın.")
    if subsamples and subsamples > 1 and observation and unit and observation != unit:
        if not string(sampling, "subsample_handling"):
            add("M021", "high", "documentation_gap", "pseudoreplication",
                "Teknik alt örnekler için bağımsızlık düzeltmesi belirtilmemiş.",
                ["sampling.technical_subsamples_per_unit", "sampling.subsample_handling"],
                "Subsamples must not be counted as independent replicates.",
                "Birim ortalaması veya uygun hiyerarşik modelin nasıl kullanıldığını gösterin.")
    if clustered and any(m in INDEPENDENT_TESTS for m in methods) and not any(
        m in DEPENDENCE_AWARE for m in methods
    ):
        add("M022", "high", "confirmed_inconsistency", "statistics",
            "Kümelenmiş veri için bağımsız örneklem testi seçilmiş.",
            ["sampling.clustered", "analysis.methods"],
            "Within-cluster correlations can invalidate standard errors.",
            "Uygun kümeli analiz veya küme düzeyinde özetleme kullanın.")
    if repeated and any(m in INDEPENDENT_TESTS for m in methods) and not any(
        m in DEPENDENCE_AWARE | {"repeated_measures_anova"} for m in methods
    ):
        add("M023", "high", "confirmed_inconsistency", "statistics",
            "Tekrarlı ölçümlere bağımsız grup testi planlanmış.",
            ["sampling.repeated_measurements", "analysis.methods"],
            "Observations from the same unit are correlated.",
            "Tekrarlı ölçümleri hesaba katan modeli kullanın.")
    if design == "repeated_measures_experiment" and repeated is not True:
        add("M024", "high" if repeated is False else "medium",
            "confirmed_inconsistency" if repeated is False else "documentation_gap", "design",
            "Tekrarlı desenle ölçüm yapısı uyuşmuyor.",
            ["study.design", "sampling.repeated_measurements"],
            "Repeated measurements require a consistent unit-time structure.",
            "Tekrar eden birimi ve ölçüm zamanlarını tanımlayın.")
    if repeated and len(timepoints) < 2:
        add("M025", "medium", "documentation_gap", "measurement",
            "Tekrarlı ölçümlerin zaman/koşulları belirtilmemiş.",
            ["measurements.timepoints"],
            "Time and subject matching cannot be assessed.",
            "En az iki ölçüm zamanı ve eşleştirme anahtarı belirtin.")
    if design == "factorial_experiment":
        if len(factors) < 2:
            add("M026", "high", "documentation_gap", "design",
                "Faktöriyel deneyde faktörler eksik.", ["sampling.factors"],
                "Interaction effects require declared factors and levels.",
                "Faktörleri ve tüm düzeylerini yazın.")
        if "one_way_anova" in methods and not any(
            m in {"factorial_anova", "mixed_model", "multilevel_model"} for m in methods
        ):
            add("M027", "high", "review_point", "statistics",
                "Faktöriyel tasarım için yalnız tek yönlü ANOVA seçilmiş.",
                ["study.design", "analysis.methods"],
                "Factor interaction can be lost in a single-factor test.",
                "Ana ve etkileşim etkilerini içeren uygun model planlayın.")
    if design == "single_factor_experiment" and len(factors) > 1:
        add("M028", "medium", "confirmed_inconsistency", "design",
            "Tek faktörlü denilen çalışmada birden fazla faktör tanımlanmış.",
            ["study.design", "sampling.factors"],
            "Design naming and planned analyses may be inconsistent.",
            "Gerçek faktör yapısını açıklayın.")
    if factors and reps and n:
        cells = math.prod(len(f["levels"]) for f in factors if f["levels"])
        if cells and n != cells * reps:
            add("M029", "medium", "review_point", "sampling",
                "Beklenen faktöriyel hücre sayıları ve bağımsız n farklı.",
                ["sampling.factors", "sampling.replicates_per_cell", "sampling.independent_units"],
                "Attrition, controls or empty cells may explain this discrepancy.",
                "Kontrolleri, kayıpları ve tam hücre sayılarını belgeleyin.")
    if n is not None and n < 3:
        add("M030", "medium", "review_point", "sampling",
            "Bağımsız n çok küçük; hassasiyet değerlendirilmeli.",
            ["sampling.independent_units"],
            "Small samples can limit uncertainty assessment; this is not a universal validity threshold.",
            "Duyarlılık ve örneklem gerekçesini raporlayın.")

    if not string(measurement, "primary_outcome"):
        add("M040", "medium", "documentation_gap", "measurement",
            "Birincil ölçüm değişkeni eksik.", ["measurements.primary_outcome"],
            "Pre-specified outcomes prevent selective reporting.",
            "Birincil ölçümü ve analiz planını belirtin.")
    elif not string(measurement, "unit"):
        add("M041", "medium", "documentation_gap", "measurement",
            "Birincil ölçüm birimi/ölçeği eksik.", ["measurements.unit"],
            "Results require interpretable units or scale boundaries.",
            "Fiziksel birimi veya ölçek aralığını yazın.")
    if not string(measurement, "method"):
        add("M042", "medium", "documentation_gap", "measurement",
            "Ölçüm/cihaz yöntemi açıklanmamış.", ["measurements.method"],
            "Reproducibility requires a documented measurement procedure.",
            "Yöntem, cihaz ve örnek hazırlığını yazın.")
    if design in EXPERIMENTS and yesno(measurement, "calibration") == "unknown":
        add("M043", "info", "documentation_gap", "measurement",
            "Kalibrasyon/kalite kontrolünün uygulanabilirliği belirsiz.",
            ["measurements.calibration"],
            "Calibration requirements depend on assay and instrument.",
            "Uygunsa kalibrasyon ve kalite kontrol kayıtlarını belirtin.")

    if not methods and design not in {"qualitative", "systematic_review"}:
        add("M050", "medium", "documentation_gap", "statistics",
            "İstatistiksel analiz planı belirtilmemiş.", ["analysis.methods"],
            "Without an analysis plan, method alignment cannot be checked.",
            "İstatistiksel yöntemi tasarım ve hipoteze göre seçin.")
    if "factorial_anova" in methods and repeated:
        add("M051", "high", "confirmed_inconsistency", "statistics",
            "Tekrarlı ölçümlere bağımsız faktöriyel ANOVA seçilmiş.",
            ["analysis.methods", "sampling.repeated_measurements"],
            "The implemented factorial ANOVA assumes independent units.",
            "Tekrarları hesaba katan model kullanın.")
    if "factorial_anova" in methods and len(factors) > 2:
        add("M052", "medium", "review_point", "statistics",
            "Mevcut faktöriyel ANOVA aracı yalnız iki faktörü destekliyor.",
            ["sampling.factors", "analysis.methods"],
            "The available implementation is not a general multi-factor engine.",
            "Daha fazla faktör için bağımsız uzman modeli kullanın.")
    if design in OBSERVATIONAL and boolean(study, "causal_claim") is True:
        add("M053", "high", "review_point", "interpretation",
            "Gözlemsel tasarım için doğrudan nedensellik iddiası bulunuyor.",
            ["study.design", "study.causal_claim"],
            "Association alone does not establish causal identification.",
            "Karıştırıcılar, zamansallık ve nedensel varsayımları gerekçelendirin.")
    if design in OBSERVATIONAL and not string(analysis, "confounder_plan"):
        add("M054", "medium", "documentation_gap", "statistics",
            "Karıştırıcı değişken planı eksik.", ["analysis.confounder_plan"],
            "Confounders can bias association estimates.",
            "Önceden belirlenen karıştırıcıları ve ayarlama yöntemini yazın.")
    if methods and not string(analysis, "missing_data_plan"):
        add("M055", "medium", "documentation_gap", "statistics",
            "Eksik veriler için analiz planı yok.", ["analysis.missing_data_plan"],
            "Missingness handling may alter estimates.",
            "Eksik veri, dışlama ve duyarlılık yaklaşımını açıklayın.")
    if any(m in {"factorial_anova", "one_way_anova", "t_test", "regression", "mixed_model"} for m in methods):
        if not string(analysis, "assumption_checks"):
            add("M056", "medium", "documentation_gap", "statistics",
                "Model varsayım kontrolleri planlanmamış.",
                ["analysis.assumption_checks"],
                "Residual and dependence assumptions affect inference.",
                "Uygun artık, varyans ve bağımlılık kontrollerini planlayın.")
    if len(methods) > 1 and not string(analysis, "multiple_comparisons"):
        add("M057", "info", "review_point", "statistics",
            "Çoklu hipotez/testler için düzeltme planı belirsiz.",
            ["analysis.multiple_comparisons"],
            "Multiple testing can inflate false-positive findings.",
            "Birincil sonuç ve test ailesini tanımlayıp düzeltme gereksinimini değerlendirin.")

    if human is True or animal is True:
        approval = yesno(ethics, "approval")
        if approval != "yes":
            add("M060", "medium" if approval == "unknown" else "high",
                "documentation_gap" if approval == "unknown" else "review_point", "ethics",
                "Etik inceleme/onay veya muafiyet gerekçesi belgelenmeli.",
                ["ethics.human_participants", "ethics.animal_research", "ethics.approval"],
                "Approval or exemption requirements depend on study and jurisdiction.",
                "Yetkili kurul onayı, muafiyet ve tarih/karar kaydını doğrulayın.")
        if human and yesno(ethics, "consent") != "yes":
            add("M061", "medium", "review_point", "ethics",
                "Onam veya etik/yasal istisna gerekçesi açıklanmalı.",
                ["ethics.human_participants", "ethics.consent"],
                "Consent requirements depend on protocol and jurisdiction.",
                "Onam/feragat/muafiyet sürecini doğru belgelendirin.")
    if human is None and animal is None:
        add("M062", "medium", "documentation_gap", "ethics",
            "İnsan/hayvan araştırması kapsamı belirtilmemiş.",
            ["ethics.human_participants", "ethics.animal_research"],
            "Ethics applicability cannot be evaluated.",
            "Katılımcı veya deney hayvanı kullanımını açık belirtin.")

    guideline = string(reporting, "guideline")
    if design in GUIDELINES:
        expected, url = GUIDELINES[design]
        if not guideline:
            add("M070", "info", "documentation_gap", "reporting",
                f"Raporlama kılavuzu belirtilmemiş (başlangıç: {expected}).",
                ["reporting.guideline"],
                "Reporting checklists improve transparency but do not validate design quality.",
                f"Güncel kılavuz/uzantı ve dergi talimatlarını inceleyin: {url}")
        elif not any(part in guideline.upper() for part in expected.upper().split("/")):
            add("M071", "info", "review_point", "reporting",
                f"Beyan edilen kılavuz tasarımla karşılaştırılmalı ({expected}).",
                ["study.design", "reporting.guideline"],
                "Journal requirements or a specialized extension may apply.",
                f"Hedef dergide geçerli kılavuzu doğrulayın: {url}")
    for key, code, title in (
        ("funding_statement", "M072", "Finansman"),
        ("conflicts_statement", "M073", "Çıkar çatışması"),
        ("data_sharing_statement", "M074", "Veri erişimi/paylaşımı"),
    ):
        if yesno(reporting, key) == "unknown":
            add(code, "info", "documentation_gap", "reporting",
                f"{title} beyanı eksik.", [f"reporting.{key}"],
                "Required transparency information is absent from supplied fields.",
                "Var/yok/kısıtlı durumunu ve ilgili kaynakları açıkça belirtin.")

    if linked is not None:
        map_method = {"factorial": "factorial_anova", "mixed": "mixed_model",
                      "regression": "regression", "correlation": "correlation"}
        which = linked.get("analysis")
        if which not in map_method:
            raise ValueError("Linked results must use factorial, mixed, regression or correlation")
        result["scope"]["linked_analysis_type"] = which
        if methods and map_method[which] not in methods:
            add("M080", "high", "confirmed_inconsistency", "integration",
                "Çalıştırılmış analiz protokolde planlanan yöntemle eşleşmiyor.",
                ["analysis.methods", "linked_results.analysis"],
                "Unreported analysis deviations weaken interpretability.",
                "Yöntem sapmasını gerekçelendirin ve protokol/raporu düzeltin.")
        if unit and linked.get("experimental_unit") != unit:
            add("M081", "high", "confirmed_inconsistency", "integration",
                "Analiz raporu ve protokolün deney birimleri farklı.",
                ["sampling.unit_of_analysis", "linked_results.experimental_unit"],
                "An incorrect unit can invalidate n and standard errors.",
                "Analiz birimini kaynak deney düzenine göre yeniden belirleyin.")
        model = linked.get("model")
        if not isinstance(model, dict):
            raise ValueError("Linked analysis model must be an object")
        if which == "factorial" and factors and model.get("factors") != [x["name"] for x in factors]:
            add("M082", "medium", "review_point", "integration",
                "Model faktörleri protokoldeki faktörlerle eşleşmiyor.",
                ["sampling.factors", "linked_results.model.factors"],
                "Factors and contrasts may represent different comparisons.",
                "Faktör adlarını ve karşılaştırma hedefini denetleyin.")
        outcome = string(measurement, "primary_outcome")
        actual_outcome = model.get("response_column")
        if which in {"factorial", "mixed"} and outcome and actual_outcome and outcome != actual_outcome:
            add("M083", "medium", "review_point", "integration",
                "Model yanıtı protokoldeki birincil sonuçtan farklı.",
                ["measurements.primary_outcome", "linked_results.model.response_column"],
                "A secondary analysis can be valid but must be correctly labelled.",
                "İkincil sonuçları ve plan değişikliklerini işaretleyin.")
        if which == "factorial" and (repeated is True or clustered is True):
            add("M084", "high", "confirmed_inconsistency", "integration",
                "Bağımsız hücre faktöriyel ANOVA tekrarlı/kümeli tasarımla eşleşmiyor.",
                ["sampling.repeated_measurements", "sampling.clustered", "linked_results.analysis"],
                "The available factorial model assumes independent units.",
                "Tekrarlı/kümeli model için yeniden analiz yapın.")
        if which == "mixed" and repeated is False:
            add("M085", "medium", "review_point", "integration",
                "Karma model ile tekrarlı ölçüm yok beyanı farklı.",
                ["sampling.repeated_measurements", "linked_results.analysis"],
                "Mixed-model grouping requires checking the actual data structure.",
                "Birim, grup ve tekrar tanımını doğrulayın.")

    if figure is not None:
        if linked is None:
            raise ValueError("--figure-metadata requires --analysis-results")
        actual_hash = linked.get("input_sha256")
        if not isinstance(actual_hash, str) or len(actual_hash) != 64:
            raise ValueError("Linked results need a valid input_sha256")
        if figure.get("data_sha256") != actual_hash:
            add("M090", "high", "confirmed_inconsistency", "integration",
                "Şekil ve analizdeki ham verilerin SHA-256 özetleri farklı.",
                ["figure_metadata.data_sha256", "linked_results.input_sha256"],
                "Scientific figures must refer to the analyzed dataset.",
                "Doğru kaynak dosyasıyla şekli yeniden oluşturun.")
        if figure.get("experimental_unit") != linked.get("experimental_unit"):
            add("M091", "high", "confirmed_inconsistency", "integration",
                "Grafikteki deney birimi analiz raporuyla eşleşmiyor.",
                ["figure_metadata.experimental_unit", "linked_results.experimental_unit"],
                "Interpretation of sample size depends on the experimental unit.",
                "Birim ve veri eşleşmesini yeniden doğrulayın.")
        if figure.get("model_results_reused") is not True or figure.get(
            "new_inferential_tests_performed"
        ) is not False:
            add("M092", "medium", "review_point", "integration",
                "Grafik metadatasında modelin yeniden kullanımı doğrulanamıyor.",
                ["figure_metadata.model_results_reused",
                 "figure_metadata.new_inferential_tests_performed"],
                "Untracked recalculation undermines reproducibility.",
                "Görsel/analiz sürüm bağlantısını doğrulayın.")
        correct_kind = {"factorial": "factorial_interaction", "mixed": "mixed_interaction"}.get(
            linked.get("analysis"))
        if figure.get("kind") != correct_kind:
            add("M093", "high", "confirmed_inconsistency", "integration",
                "Grafik türü analiz raporuyla eşleşmiyor.",
                ["figure_metadata.kind", "linked_results.analysis"],
                "Graph error representation depends on the model.",
                "Uyumlu modelin etkileşim grafiğini kullanın.")

    result["findings"].sort(key=lambda f: (
        {"high": 0, "medium": 1, "info": 2}[f["severity"]], f["id"]))
    severity = Counter(f["severity"] for f in result["findings"])
    kinds = Counter(f["classification"] for f in result["findings"])
    result["summary"] = {
        "status": "review_required" if result["findings"] else "no_flags_in_supplied_fields",
        "finding_count": len(result["findings"]), "severity_counts": dict(severity),
        "classification_counts": dict(kinds), "expert_review_required": True,
    }
    return result


def markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Bilimsel yöntem denetimi — v1.0.0", "",
        "Bu bir otomatik tutarlılık ön taramasıdır; bilimsel kalite onayı değildir.", "",
        "Kaynak: " + report["input_filename"],
        "SHA-256: " + report["protocol_sha256"],
        "Bildirilen desen: " + str(report["study_design"] or "unknown"),
        f"Toplam bulgu: {summary['finding_count']}",
        f"Yüksek: {summary['severity_counts'].get('high',0)}; "
        f"orta: {summary['severity_counts'].get('medium',0)}; "
        f"bilgi: {summary['severity_counts'].get('info',0)}",
        "", "## Bulgular", "",
    ]
    if not report["findings"]:
        lines += ["Sunulan alanlarda kural ihlali görülmedi. Bu bulgu araştırmanın doğruluğunu kanıtlamaz.", ""]
    for f in report["findings"]:
        lines += [
            "### " + f["id"] + " — " + f["title"],
            "- Düzey / sınıf: " + f["severity"] + " / " + f["classification"],
            "- İncelenen alanlar: " + ", ".join(f["evidence_paths"]),
            "- Gerekçe: " + f["rationale"],
            "- Öneri: " + f["recommended_action"], "",
        ]
    lines += ["## Yöntemsel sınırlar", ""] + [
        "- " + item for item in report["limitations"]
    ] + ["", "Ham veri, özgün protokol, ölçüm kayıtları ve etik belgeler ayrıca uzman tarafından karşılaştırılmalıdır.", ""]
    return "\n".join(lines)


def main() -> int:
    opts = args_parser()
    try:
        protocol, sha = read_json(opts.protocol, "Protocol")
        linked = linked_sha = figure = figure_sha = None
        if opts.analysis_results:
            linked, linked_sha = read_json(opts.analysis_results, "Analysis results")
        if opts.figure_metadata:
            figure, figure_sha = read_json(opts.figure_metadata, "Figure metadata")
        result = audit(protocol, opts.protocol.name, sha, linked, linked_sha, figure, figure_sha)
        opts.output.mkdir(parents=True, exist_ok=True)
        (opts.output / "methodology_report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8")
        (opts.output / "methodology_report.md").write_text(
            markdown(result), encoding="utf-8")
    except (ValueError, OSError, TypeError) as exc:
        raise SystemExit(f"Methodology audit stopped: {exc}") from exc
    print(f"PASS: {result['summary']['finding_count']} findings -> {opts.output}")
    return 3 if opts.fail_on_high and result["summary"]["severity_counts"].get("high", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
