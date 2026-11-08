# Turkish Writing Skills

Türkçe akademik, kurumsal ve bilgilendirici metinleri daha doğal ve anlaşılır hâle getirirken anlamı, kanıt düzeyini, sayıları ve atıfları koruyan bir Agent Skill projesi.

## Özellikler

### Doğal ve açık Türkçe

- İngilizce söz dizimini taklit eden cümleleri doğal Türkçe akışına dönüştürür.
- Uzun isim zincirlerini, aşırı adlaştırmayı ve gereksiz edilgenliği azaltır.
- Belirsiz özne ve gönderimleri görünür kılar; çözülemeyen belirsizliği tahmin etmek yerine işaretler.
- Bağdaşıklığı, terim tutarlılığını ve paragraf içindeki bilgi akışını güçlendirir.
- Metni yalnızca kısaltmaz; hedef okura göre tanım, açıklama ve örnekleme gereksinimini değerlendirir.

### Akademik makale desteği

- Başlık, özet, giriş, yöntem, bulgular ve tartışma bölümlerini kendi işlevlerine göre düzenler.
- Araştırma amacı, örneklem, temel sonuç ve istatistiklerin bölümler arasında tutarlı kalmasını denetler.
- Karşılaştırmalı özetlerde amaç veya yöntemde tanıtılan her grubun temel bulgularda temsil edilip edilmediğini denetler; eksik sonucu uydurmaz.
- Bulguları yorumdan; korelasyonu nedensellikten; veri sonucunu yazar yorumundan ayırır.
- Hedef derginin yazar rehberini genel biçim tercihlerinden üstün tutar.
- Sağlık araştırmalarında gerçek çalışma tasarımına göre CONSORT, STROBE, PRISMA, SRQR, CARE, STARD, TRIPOD+AI, ARRIVE, SQUIRE veya CHEERS gibi uygun raporlama kılavuzunu seçmeye yardımcı olur.

### Bilimsel içeriği koruma

- Sayı, yüzde, tarih, birim, p değeri, güven aralığı, DOI ve atıfları korur.
- “Gösterir”, “ilişkilidir”, “olabilir” ve “kanıtlamaz” gibi farklı kesinlik düzeylerini birbirine dönüştürmez.
- Etik kurul, onam, kayıt, ORCID, finansman ve çıkar çatışması bilgilerini kaynak belge olmadan tamamlamaz.
- Eksik veya doğrulanması gereken bilgiyi görünür biçimde işaretler; kaynak ve bulgu uydurmaz.

### Türkçe yazım ve noktalama

- `da/de`, `ki`, soru eki, özel adlar, kurum adları, kısaltmalar ve sayı eklerini denetler.
- Virgül, noktalı virgül, iki nokta, tırnak, parantez, kısa çizgi, eğik çizgi ve kesme işaretini bağlama göre değerlendirir.
- TDK tercihleriyle hedef derginin teknik gösterimi çatıştığında dergi kuralını korur.

### Kaynak ve etik farkındalığı

- Fredrick & Craven, Kang, Murphy Odo, Watanabe ve Gibson ve ark. çalışmalarını bilimsel sınırlılıklarıyla birlikte kullanır.
- İngilizce okunabilirlik bulgularını Türkçeye doğrudan kanıtlanmış kural olarak genellemez.
- TDK, YÖK yayın etiği, TR Dizin, TÜBİTAK ULAKBİM ve EQUATOR kaynaklarının farklı rollerini ayırır.
- Otomatik okunabilirlik puanını gerçek okur anlama başarısının yerine koymaz.

### Türkçe üslup denetimi (v0.6.0)

- Üç açık çalışma modu: `write` (yaz), `rewrite` (düzenle) ve `audit` (değiştirmeden incele).
- Akademik, kurumsal, teknik ve genel metin profilleri; bilimsel terimler, anlam ve hedef dergi önceliği korunur.
- Bağımlılıksız `audit_turkish.py`, belirli dil ve yazım örüntülerini satır/sütun bilgisiyle ve **bağlamsal inceleme önerisi** olarak bildirir.
- `--compare` seçeneği düzenlenen metinde sayısal değer/DOI kaybı veya eklenmesini ön kontrol olarak gösterir; anlam eşitliğini veya atıf bağlarını doğrulamaz.
- Kod blokları, satır içi kod, bağlantılar ve DOI'ler üslup taramasında korunur.
- Betik bir yapay zekâ yazarlık dedektörü değildir; kelime/bağlaç yasakları veya "insanlık" eşikleri uygulamaz.

### DOI doğrulama katmanı

**v1.0.1:** Claude'da URL okuma izni engeli, HTTP 403/429 veya internet kesintisi geçersiz DOI sayılmaz. DOI çözümlenemese de Crossref, gerekirse DataCite metadata sorguları denenir. Erişilen güvenilir metadata bibliyografik alanlarla eşleşirse DOGRULANDI; çelişirse UYUSMAZLIK; erişilemiyorsa KONTROL_EDILEMEDI. Kaynak ajansı ve bağlantı hataları rapora eklenir. Yalnızca erişim nedeniyle doğrulanamayan kayıtlar, konsol uyarısıyla raporlanır; komut gerçek kaynak hatası varmış gibi başarısız sayılmaz. DataCite Crossref geri çekme taramasının yerini almaz; web izinleri atlatılmaz.



- DOI'lerin `doi.org` üzerinden çözümlenip çözümlenmediğini denetler.
- Crossref kaydındaki başlık, ilk yazar ve yılı kaynakça girdisiyle karşılaştırır.
- Crossref ve Retraction Watch metadata alanlarında görülen geri çekme, düzeltme, endişe ifadesi ve diğer güncellemeleri uyarı olarak raporlar.
- Geçerli fakat Crossref dışında kayıtlı olabilecek DOI'leri, çözümlenemeyen DOI'lerden ayırır.
- Sonuçları düzenlenebilir `XLSX` tablosu ile `Markdown` ve `JSON` raporları olarak verir.
- Kaynakçayı kendiliğinden değiştirmez; uyumsuzluğu ve belirsizliği inceleme için işaretler.

### İstatistiksel analiz ve bilimsel şekiller (v0.7.1)

- Akademik iş akışında istatistik veya şekil gereksinimini veri ve deney desenine göre değerlendirir; sıradan metin düzenleme için analiz çalıştırmaz.
- Gerçek ham veri ve bağımsız deney birimi tanımı varsa tek faktörlü gruplarda betimsel analiz, ANOVA + Tukey HSD, Welch ANOVA + Holm düzeltilmiş ikili Welch testleri veya Kruskal–Wallis uygulanabilir.
- Ham noktaları gösteren kutu grafiklerini 300 DPI PNG, vektör PDF ve SVG olarak kaydeder; `results.json` analiz kaydı oluşturur. Tanı testi hesaplanamıyorsa raporda `null` ve bir uyarı kullanır (v0.7.1).
- Tekrarlı, bloklu, faktöriyel veya iç içe geçmiş veri için tek faktörlü aracı **kullanmaz**; uygun modeli belirlemek üzere tasarımı denetler.
- Ham veri olmadan p değeri, Tukey harfi veya örneklem icat etmez; kaynak [Figures for Papers](https://github.com/ChenLiu-1996/figures4papers) kodunu kopyalamadan yayın tasarım ilkelerinden yararlanır.

İsteğe bağlı bağımlılıkları yükleyin:

```bash
python3 -m pip install -r skills/turkish-clear-writing/requirements-statistics.txt
python3 skills/turkish-clear-writing/scripts/analyze_and_plot.py deney.csv --group uygulama --value bitki_boyu_cm --unit saksi_id --analysis anova --output sonuclar
```

Tekrarlı ölçümler, alt örnekler ve deney birimi bağımsızlığı için [istatistik ve şekil kılavuzunu](skills/turkish-clear-writing/references/statistics-and-figures.md) okuyun. Betik, tasarım doğrulamasının yerini almaz.

### Bilimsel grafik motoru (v0.8.0)

- Beş çalıştırılabilir betimsel grafik türü: `box_jitter` (kutu + ham noktalar), `grouped_bar` (iki faktörlü grup ortalamaları), `line_plot` (sayısal doz/zaman çizgileri), `correlation_heatmap` (Pearson/Spearman), `multi_panel` (2–4 bağımsız panel).
- CSV ve XLSX verilerini okur. Seçilen sütunların veri türlerini ve eksik ölçümleri kontrol eder; isteğe bağlı `--unit` ile tekrar eden deney birimi ID'lerini yakalar.
- 300 DPI PNG, vektörel PDF/SVG ve grup/örneklem bilgilerini, korelasyon katsayılarını, çift bazında n değerlerini ve veri dosyası özetini saklayan `plot_metadata.json` üretir.
- Matplotlib ve renk körlüğünü dikkate alan ortak stil, sayısal doz sıralaması, doğru eksen/etiket, hata çubuğu türü ve kaynak doğrulaması içerir.
- **Henüz çıkarımsal test, otomatik anlamlılık harfi veya karma model üretmez**; istatistik modülüyle karıştırılmaz. Şablonlar özgündür; Figures for Papers kodu kopyalanmamıştır.

Kurulum ve beş örnek komut için [bilimsel grafik kullanım kılavuzuna](skills/turkish-clear-writing/references/publication-figures.md) bakın. Kısa örnek:

```bash
python3 -m pip install -r skills/turkish-clear-writing/requirements-statistics.txt
python3 skills/turkish-clear-writing/scripts/plot_scientific.py deneme.xlsx \
  --kind box_jitter --group uygulama --y bitki_boyu_cm \
  --unit saksi_id --output figurler/bitki_boyu
```

Sentetik örnek veriler `examples/figures-demo.csv` içindedir; gerçek araştırma sonuçları değildir.

### Gelişmiş istatistiksel analiz (v0.9.0)

- **İki faktörlü bağımsız gruplar:** Type III (sum-kontrastlı) ANOVA; iki ana etki, etkileşim, F/p, kısmi eta-kare, Levene ve artık normalliği.
- **Korelasyon:** Pearson/Spearman, ikili örneklem sayısı, Holm veya FDR-BH düzeltmeli çoklu karşılaştırmalar; sabit değişken ve eksik veri uyarıları.
- **Regresyon:** 1–8 sayısal yordayıcı ile çoklu OLS; HC3 heteroskedastisiteye dayanıklı standart hatalar, %95 güven aralıkları, R², VIF ve Breusch–Pagan.
- **Tekrarlı ölçümler:** Aynı deney biriminin zaman içindeki verisi için ML rastgele kesişimli karma etkili model; doğrusal zaman, isteğe bağlı grup ve zaman × grup etkileşimi.
- **Tasarım güvenceleri:** deney birimi zorunlu, faktöriyel hücre eksikliği, ölçüm tekrarları, kollinearite, yetersiz birim sayısı, yakınsamayan model ve yinelenen kaynak sütun başlıkları için korumalar.
- Çıktılar: `results.json`, `table.csv`, `results.md`; kaynak SHA-256, varsayımlar ve uyarılar raporlanır.

Bu **tasarım sınırlı** modül, araştırma planını kendiliğinden doğrulamaz. Karma modelde rastgele eğim/karmaşık blok yoktur; faktöriyel analiz post-hoc anlamlılık harfleri üretmez. Aynı saksı/katılımcıdan gelen alt örnekleri bağımsız saymayın. Ayrıntılar için [gelişmiş istatistik kılavuzu](skills/turkish-clear-writing/references/advanced-statistics.md).

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py deney.xlsx \
  --analysis factorial --unit saksi_id --value kuru_agirlik_g \
  --factor-a uygulama --factor-b doz --output analiz/iki_faktor
```

### İstatistiksel modellerle bağlantılı etkileşim grafikleri (v0.9.1)

- **Uygulama × doz:** Faktöriyel ANOVA'daki iki kategorik faktörü birbirine karşı çizer. Gerçek sayısal doz aralıklarını korur; ham birim noktalarını, hücre ortalamalarını ve seçilen SD/SEM/%95 t güven aralığını sunar.
- **Zaman × uygulama:** Rastgele kesişimli karma modelde tahmin edilen **sabit etkili popülasyon ortalamalarını**, her grubun ölçülmüş zaman aralığındaki 101 noktada ayrı hesaplanan asimptotik %95 güven bantlarını ve gözlenen grup ortalamalarını gösterir.
- **Model-veri denetimi:** Kaynak CSV/XLSX SHA-256 ve satır sayısı, bağımsız birim, değişken adları, faktöriyel hücre istatistikleri veya karma tahmin ızgarası uyumsuzsa grafik üretmez.
- **Yayın çıktısı:** 300 DPI PNG, vektörel PDF/SVG, `interaction_table.csv`, karma modelde `interaction_curve.csv`, `interaction_metadata.json` ve yorum sınırlarını belirten `interaction_caption.md`.
- Var olan v0.8.0 genel grafik motoru ve v0.9.0 istatistik modülü korunur; **grafik betiği hiçbir p değeri veya post-hoc anlamlılık harfi üretmez**.

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py deneme.xlsx \
  --analysis factorial --unit saksi_id --value kuru_agirlik_g \
  --factor-a uygulama --factor-b doz --output analiz/faktoriyel

python3 skills/turkish-clear-writing/scripts/plot_interactions.py deneme.xlsx \
  --results analiz/faktoriyel/results.json --output figurler/etkilesim
```

Karma model için örnekler ve belirsizlik türlerinin açıklaması [etkileşim grafikleri kılavuzunda](skills/turkish-clear-writing/references/interaction-figures.md).

### Bilimsel yöntem denetimi (v1.0.0)

- **Yapılandırılmış protokol denetimi:** araştırma sorusu, deney birimi, uygulama ve doz faktörleri, randomizasyon, kontrol, ölçüm tekniği, tekrarlı ölçüm, eksik veri ve yöntem raporunu sistematik inceler.
- **Üç farklı bulgu tipi:** beyanlar arasında kesin tutarsızlık, belgede eksik bilgi ve uzman değerlendirmesi gereken durumları ayrı sınıflandırır. Kanıt yolu, öncelik ve önerilen düzeltmeyi raporlar.
- **İstatistik ve grafik bütünlüğü:** isteğe bağlı v0.9.x results.json ve v0.9.1 interaction_metadata.json raporlarını protokol ile karşılaştırır; analiz birimi, model yöntemi, yanıt/faktör, kaynak veri SHA-256 ve grafiğin üretildiği **tam sonuç JSON'unun SHA-256** eşleşmelerini kontrol eder.
- **Etik/raporlama farkındalığı:** insan veya hayvan çalışması kapsamı, etik kurul ve onam durumunun raporlanmasını, STROBE/CONSORT/PRISMA seçimini ve finansman/çıkar çatışması beyanlarını gözden geçirir.
- **Ölçülü sonuçlar:** otomatik bilimsel kalite puanı, etik onayı, gerçek protokol doğrulaması veya p değeri üretmez. Eksik bilgi otomatik olarak yöntem hatası kabul edilmez.
- **Çıktılar:** methodology_report.json ve methodology_report.md; JSON kaynak özeti ve ilgili model/şekil izleri.

Üçüncü taraf bağımlılık gerektirmeyen örnek:

    python3 skills/turkish-clear-writing/scripts/audit_methodology.py examples/methodology-factorial-pot.json --output denetim/sonuc

Kendi protokolünü oluşturmak için skill içindeki assets/methodology-protocol-template.json dosyasını kullan. [Kapsam ve kullanım kılavuzu](skills/turkish-clear-writing/references/methodology-audit.md). Aracın kendisi PDF/DOCX okumaz; belgeyi inceleyip doğrulanabilen alanların JSON'a aktarılması gerekir.

### Test ve doğrulama

- Sayı, atıf ve etik tanımlayıcı koruması için otomatik örnek testleri içerir.
- On bir kontrollü davranış vakasıyla belirsizlik, nedensellik, karşılaştırma kapsamı, bölüm ayrımı, TDK yazımı ve raporlama kılavuzu seçimini sınar.
- GitHub Actions üzerinden her gönderimde paket yapısını ve davranış değişmezlerini denetler.
- DOI doğrulayıcısını ağ gerektirmeyen sentetik kayıtlarla sınar.

## Kurulum

`skills/turkish-clear-writing` klasörünü Agent Skills destekleyen ortamınızın skills dizinine kopyalayın. Codex için tipik hedef `~/.codex/skills/turkish-clear-writing` dizinidir.

## Kullanım

Örnek istem:

> `$turkish-clear-writing` kullanarak bu akademik metni genel okur için düzenle. Teknik terimleri ilk kullanımda kısa biçimde tanımla; iddiaları, sayıları ve atıfları değiştirme.

Skill şu işleri yapar:

1. Var olan Türkçe metni açık ve doğal biçimde düzenler.
2. İngilizceden çevrilmiş gibi duran Türkçe söz dizimini düzeltir.
3. Metni hedef okura göre açıklar veya sadeleştirir.
4. Akademik iddia gücünü, sayıları ve kaynakları koruyarak yapay zekâ üslubunu azaltır.
5. Akademik makalede etik/şeffaflık alanlarını ve çalışma türüne uygun raporlama eksiklerini görünür kılar.
6. İstenirse DOI'leri, bibliyografik eşleşmeleri ve yayın sonrası güncelleme kayıtlarını denetler.

Üslup denetimi için skill klasöründe kullanım:

```bash
python3 scripts/audit_turkish.py makale.md --register academic
python3 scripts/audit_turkish.py duyuru.md --register institutional --json
python3 scripts/audit_turkish.py kaynak.md --compare duzeltilmis.md --json
```

Birinci komut metni değiştirmeden bulguları gösterir. Karşılaştırma komutu yalnızca sayı ve DOI belirteçlerini kontrol eder.

DOI kontrolü için skill klasöründe örnek kullanım:

```bash
python3 scripts/verify_dois.py kaynakca.bib --output doi-dogrulama
python3 scripts/verify_dois.py kaynakca.docx --output doi-dogrulama
python3 scripts/verify_dois.py --doi 10.1234/ornek --output doi-dogrulama
```

Çıktı klasöründe `doi-dogrulama-raporu.xlsx`, `doi-dogrulama-raporu.md` ve `doi-dogrulama-sonuclari.json` oluşur. Çevrimiçi kontrol, kesin hüküm değil bir ön doğrulama katmanıdır; kritik uyarılar yayıncı sayfasından incelenmelidir.

## Proje yapısı

```text
skills/turkish-clear-writing/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   ├── audit_turkish.py
│   ├── verify_dois.py
│   ├── analyze_and_plot.py
│   ├── advanced_statistics.py
│   ├── plot_interactions.py
│   ├── plot_scientific.py
│   └── figure_style.py
├── requirements-statistics.txt
└── references/
    ├── style-audit.md
    ├── doi-verification.md
    ├── evidence-and-limitations.md
    ├── evaluation.md
    ├── examples.md
    ├── statistics-and-figures.md
    ├── publication-figures.md
    ├── advanced-statistics.md
    ├── interaction-figures.md
    ├── academic-article-workflow.md
    ├── research-ethics-and-reporting.md
    ├── tdk-writing-and-punctuation.md
    └── turkish-guidelines.md
scripts/check_examples.py
scripts/check_behavioral_outputs.py
scripts/check_doi_verifier.py
scripts/check_style_audit.py
scripts/check_statistical_analysis.py
scripts/check_publication_figures.py
scripts/check_advanced_statistics.py
scripts/validate_package.py
tests/cases.json
tests/behavioral-cases.json
tests/behavioral-outputs.json
tests/behavioral-report.md
tests/doi-fixtures.json
```

## Doğrulama

Örnek koruma testini çalıştırın:

```bash
python3 scripts/check_examples.py
python3 scripts/check_behavioral_outputs.py
python3 scripts/check_doi_verifier.py
python3 scripts/check_style_audit.py
python3 scripts/check_statistical_analysis.py
python3 scripts/check_publication_figures.py
python3 scripts/check_advanced_statistics.py
python3 scripts/validate_package.py
```

Agent Skill yapısını doğrulamak için Skill Creator paketindeki `quick_validate.py` kullanılabilir.

## Bilimsel kapsam

Öncelikli çalışmaların çoğu İngilizce metinleri veya İngilizce öğrenen okurları inceler. Bu proje, sonuçları Türkçeye doğrudan “kanıtlanmış kural” olarak aktarmıyor. Araştırmaların desteklediği genel ilkeleri, Türkçenin eklemeli ve büyük ölçüde baş-sonlu yapısına göre temkinli editoryal yönergelere dönüştürüyor.

Otomatik okunabilirlik puanları gerçek anlamayı ölçmez. Benzer biçimde, DOI yönlendirmesinin çalışması kaynakça girdisinin bütünüyle doğru olduğunu; uyarı bulunmaması da yayının kesinlikle sorunsuz olduğunu kanıtlamaz. Crossref/Retraction Watch kapsamı ve yayıncı metadata kalitesi değişebilir. Yüksek önem taşıyan akademik, hukuki, tıbbi veya kamusal metinlerde hedef okur denemesi, asıl kaynak kontrolü ve alan uzmanı incelemesi gerekir.

Kaynaklar, tarihler ve DOI notları için [kanıt haritasına](skills/turkish-clear-writing/references/evidence-and-limitations.md) bakın.

TDK PDF’si, Google Books kitabı ve çevrimiçi kaynak PDF’leri telif ve boyut nedenleriyle pakete kopyalanmamıştır; pakette yalnızca kaynaklardan türetilen, yeniden kullanılabilir uygulama notları bulunur. Google Books kaynağı sınırlı ön izleme olduğu için yalnızca erişilebilen içerik kullanılmıştır. Çevrimiçi etik, dizin ve raporlama kuralları gönderimden önce güncel resmî sayfalarından yeniden doğrulanmalıdır.

## Lisans

MIT
