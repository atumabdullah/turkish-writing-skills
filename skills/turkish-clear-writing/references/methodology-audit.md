# Bilimsel yöntem denetimi — v1.0.0

Bu sürüm, önceden belgelenmiş araştırma protokolü alanlarını **yapılandırılmış kurallarla** denetler. Araştırmanın doğru tasarlandığını kanıtlamaz; etik kurul onayı, bağımsız hakem incelemesi, gerçek ölçüm doğrulaması, güç analizi veya ham veri üzerinden istatistiksel analiz yerine geçmez. Bilinmeyen bilgi bilinmeyen olarak tutulur.

## Kullanım

1. Protokol veya yöntem bölümünden yalnızca doğrulanabilen bilgileri çıkarın. Bilgi bulunmuyorsa boş/null/unknown kullanın. Bu betik PDF/DOCX metnini otomatik olarak okumaz; dosyalar başka araçla okunup **kanıta dayalı** JSON'a aktarılır.
2. Kurulum paketinin assets/methodology-protocol-template.json dosyasını kopyalayın. Örnekler: depo kökündeki examples/methodology-factorial-pot.json ve examples/methodology-cross-sectional.json. Her iki örnek de sentetiktir, gerçek araştırma verisi değildir.
3. JSON protokolünü, varsa aynı çalışmaya ait istatistik ve grafik sonuçlarını denetleyin.

Komut örneği (Python 3.11+, üçüncü taraf bağımlılık gerekmez):

    python3 skills/turkish-clear-writing/scripts/audit_methodology.py examples/methodology-factorial-pot.json --output denetim/faktoriyel

İstatistik ve grafikle bağlantılı tam denetim:

    python3 skills/turkish-clear-writing/scripts/audit_methodology.py protokol.json --analysis-results analiz/results.json --figure-metadata grafik/interaction_metadata.json --output denetim/sonuc

Çıktılar: methodology_report.json ve methodology_report.md. Kaynak JSON SHA-256, varsa istatistik ve grafik dosyaları SHA-256, bulgu ID, şiddet, tür, etkilenen alan ve düzeltme önerileri kaydedilir. Ham kişisel gözlem verileri rapora aktarılmaz.

## JSON sözleşmesi

schema_version kesinlikle "1.0" olmalıdır. Kök alanlar:

| Alan grubu | İçerik |
| --- | --- |
| study | design, research_question, causal_claim |
| sampling | unit_of_analysis, unit_of_randomization, unit_of_observation, independent_units, replicates_per_cell, technical_subsamples_per_unit, subsample_handling, repeated_measurements, clustered, factors |
| procedures | randomization, randomization_method, control_group, blinding, sample_size_justification, allocation_concealment |
| measurements | primary_outcome, unit, method, calibration, timepoints |
| analysis | methods, assumption_checks, missing_data_plan, multiple_comparisons, confounder_plan |
| ethics | human_participants, animal_research, approval, consent |
| reporting | guideline, funding_statement, conflicts_statement, data_sharing_statement |

Tasarım (study.design) seçenekleri: single_factor_experiment, factorial_experiment, repeated_measures_experiment, randomized_trial, observational_cross_sectional, observational_cohort, case_control, systematic_review, qualitative, other.

Bool alanları true, false veya bilinmiyorsa null olmalıdır. Onam, randomizasyon, kalibrasyon ve ilgili beyan **durum** alanları yes, no, unknown veya not_applicable değerlerini alır. Boş alan bilinmeyen sayılır. Örneğin etik kurul kaydının verilmemesi, onayın bulunmadığını ispatlamaz.

sampling.factors listesinde her faktörün name alanı ve sıfır veya en az iki düzeyli levels listesi bulunur. independent_units gerçekten bağımsız saksı/parsel/birey sayısını belirtir; aynı saksıdan alınan teknik alt ölçümler bu sayıya eklenmez.

İstatistiksel yöntem etiketleri: one_way_anova, factorial_anova, t_test, welch_anova, repeated_measures_anova, mixed_model, multilevel_model, gee, cluster_robust_regression, regression, correlation. Başka etiketler girilebilir, ancak kural motoru bunları otomatik değerlendiremeyebilir.

## Bulguların sınıfları

- confirmed_inconsistency: JSON'daki iki açık beyan birbiriyle çelişiyor; örneğin tekrarlı ölçümlere yalnız bağımsız grup ANOVA'sı seçilmiş.
- documentation_gap: yöntem, randomizasyon, bağımsız birim, ölçüm birimi veya etik belgenin bulunup bulunmadığı açıklanmamış. Eksiklik, kusurlu uygulamanın kanıtı değildir.
- review_point: küme tahsisi ve birey düzeyindeki analiz gibi, özel koşullarda uygun olabilecek fakat uzman gerekçesi isteyen durumlar.

Öncelik high, medium ve info olarak gösterilir. Sayısal bilimsel kalite puanı veya otomatik "onay" yoktur. Hiç bulgu olmadığında bile rapor yalnızca "sunulan alanlarda uyarı bulunmadı" der. --fail-on-high bayrağı, yüksek öncelikli bir bulguda raporları yazar ve exit code 3 ile sonlanır.

## Tasarım ve analiz kapsamı

**Tarımsal deneyler:** gerçek deney birimi ve tekerrür, randomizasyon, faktörler ve dozlar, teknik alt örnekler, hücre sayısı ve uygun istatistiksel model.

**Tekrarlı ölçüm:** aynı saksı/katılımcının ölçüm zamanları, basit bağımsız grup testleriyle çelişkiler ve kümelenme.

**Gözlemsel araştırma:** nedensellik dili, karıştırıcılar, eksik veri, etik/onam ve raporlama.

**Analiz ve grafik uyumu:** isteğe bağlı v0.9.x results.json ile protokolün model türü, yanıt/faktör ve deney birimi kontrol edilir. v0.9.1 interaction_metadata.json bağlanırsa grafikteki ham veri SHA-256, analiz birimi ve model türü de karşılaştırılır. Kontrol, gerçek veriyi bağımsız olarak doğrulamaz.

**Etik ve şeffaflık:** insan/hayvan araştırmalarında kurul onayı, geçerli muafiyet ve onam belgeleri uzman tarafından değerlendirilmelidir. Yalnız rapor alanının boşluğu üzerinden usulsüzlük iddia edilmez.

## Raporlama kılavuzu ile yöntem kalitesi farklıdır

EQUATOR Network'e göre raporlama kılavuzları çalışmayı eksiksiz anlatmaya yardımcı olur; **çalışma tasarımının kalitesini değerlendirme aracı değildir**. Güncel sürüm ve hedef dergi uzantıları ayrı doğrulanmalıdır:

- [EQUATOR kılavuz dizini](https://equator-network.org/reporting-guidelines/)
- [CONSORT 2025: randomize çalışmalar](https://www.consort-spirit.org/)
- [STROBE: gözlemsel çalışmalar](https://equator-network.org/reporting-guidelines/strobe/)
- [PRISMA 2020: sistematik derlemeler](https://www.prisma-statement.org/)

Bu denetim araçları kılavuz maddelerini otomatik imzalamaz veya raporlama standardına tam uyum sertifikası vermez.

## Regresyon testleri

    python3 scripts/check_methodology_audit.py

Test paketi; sentetik temiz protokoller, sahte tekerrür, tekrarlı ölçümler, faktöriyel model uyumu, eksik yöntem bilgileri, etik uyarılar, nedensellik, geçersiz JSON, protokol–analiz çakışmaları ve yanlış grafik SHA-256 eşleştirmeleri için çalışır.
