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

- DOI'lerin `doi.org` üzerinden çözümlenip çözümlenmediğini denetler.
- Crossref kaydındaki başlık, ilk yazar ve yılı kaynakça girdisiyle karşılaştırır.
- Crossref ve Retraction Watch metadata alanlarında görülen geri çekme, düzeltme, endişe ifadesi ve diğer güncellemeleri uyarı olarak raporlar.
- Geçerli fakat Crossref dışında kayıtlı olabilecek DOI'leri, çözümlenemeyen DOI'lerden ayırır.
- Sonuçları düzenlenebilir `XLSX` tablosu ile `Markdown` ve `JSON` raporları olarak verir.
- Kaynakçayı kendiliğinden değiştirmez; uyumsuzluğu ve belirsizliği inceleme için işaretler.

### İstatistiksel analiz ve bilimsel şekiller (v0.7.0)

- Akademik iş akışında istatistik veya şekil gereksinimini veri ve deney desenine göre değerlendirir; sıradan metin düzenleme için analiz çalıştırmaz.
- Gerçek ham veri ve bağımsız deney birimi tanımı varsa tek faktörlü gruplarda betimsel analiz, ANOVA + Tukey HSD, Welch ANOVA + Holm düzeltilmiş ikili Welch testleri veya Kruskal–Wallis uygulanabilir.
- Ham noktaları gösteren kutu grafiklerini 300 DPI PNG, vektör PDF ve SVG olarak kaydeder; `results.json` analiz kaydı oluşturur.
- Tekrarlı, bloklu, faktöriyel veya iç içe geçmiş veri için tek faktörlü aracı **kullanmaz**; uygun modeli belirlemek üzere tasarımı denetler.
- Ham veri olmadan p değeri, Tukey harfi veya örneklem icat etmez; kaynak [Figures for Papers](https://github.com/ChenLiu-1996/figures4papers) kodunu kopyalamadan yayın tasarım ilkelerinden yararlanır.

İsteğe bağlı bağımlılıkları yükleyin:

```bash
python3 -m pip install -r skills/turkish-clear-writing/requirements-statistics.txt
python3 skills/turkish-clear-writing/scripts/analyze_and_plot.py deney.csv --group uygulama --value bitki_boyu_cm --unit saksi_id --analysis anova --output sonuclar
```

Tekrarlı ölçümler, alt örnekler ve deney birimi bağımsızlığı için [istatistik ve şekil kılavuzunu](skills/turkish-clear-writing/references/statistics-and-figures.md) okuyun. Betik, tasarım doğrulamasının yerini almaz.

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
│   └── analyze_and_plot.py
├── requirements-statistics.txt
└── references/
    ├── style-audit.md
    ├── doi-verification.md
    ├── evidence-and-limitations.md
    ├── evaluation.md
    ├── examples.md
    ├── statistics-and-figures.md
    ├── academic-article-workflow.md
    ├── research-ethics-and-reporting.md
    ├── tdk-writing-and-punctuation.md
    └── turkish-guidelines.md
scripts/check_examples.py
scripts/check_behavioral_outputs.py
scripts/check_doi_verifier.py
scripts/check_style_audit.py
scripts/check_statistical_analysis.py
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
