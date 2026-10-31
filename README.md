# Turkish Writing Skills

Türkçe akademik, kurumsal ve bilgilendirici metinleri daha doğal ve anlaşılır hâle getirirken anlamı, kanıt düzeyini, sayıları ve atıfları koruyan bir Agent Skill projesi.

## Neler değişti? — v0.4.1

- Fredrick & Craven (2025), Kang (2026), Murphy Odo (2025), Watanabe (2025) ve Gibson ve ark. (2019) için doğrulanmış kanıt haritası eklendi.
- İngilizce bulgular ile Türkçeye özgü editoryal uyarlamalar açıkça ayrıldı.
- Doğal Türkçe söz dizimi, eklemeli morfoloji, uzun isim zincirleri, açık gönderim, bağdaşıklık, bilgi yoğunluğu, tanımlama ve örnekleme için uygulanabilir yönergeler geliştirildi.
- Akademik kesinlik, sayı ve atıf koruma zorunlu son kontrol olarak tanımlandı.
- Önce–sonra örnekleri, değerlendirme rubriği ve otomatik koruma testleri eklendi.
- Kullanıcının sağladığı TDK yazım ve noktalama PDF’sinden akademik yazıya yönelik yüksek etkili denetimler eklendi.
- *Bilimsel Makale ve Yayıncılık Akademisyen El Kitabı* sınırlı ön izlemesinden doğrulanan makale planlama ve bölüm tutarlılığı iş akışı eklendi.
- Dergi yazar rehberi, teknik gösterim ve TDK varsayımları arasındaki öncelik sırası açıklandı.
- YÖK yayın etiği yönergesi, TR Dizin ölçütleri, TÜBİTAK ULAKBİM makale yazımı sunumu ve EQUATOR raporlama kılavuzları kaynak rolleri ayrılarak eklendi.
- Etik kurul/onam, kayıt, yazarlık, finansman, çıkar çatışması ve veri izni bilgileri korunacak tanımlayıcılar olarak tanımlandı.
- Sağlık araştırmalarında gerçek çalışma tasarımına göre raporlama kılavuzu seçimi ve eksik bilgi uydurmama denetimi eklendi.
- On kontrollü sentetik vaka, örnek skill çıktıları ve otomatik davranış koruma denetimi eklendi.
- Davranış testinin sonuçları ve bağımsızlık sınırlılığı ayrı raporda belgelendi.

## Kurulum

`skills/turkish-clear-writing` klasörünü Agent Skills destekleyen ortamınızın skills dizinine kopyalayın. Codex için tipik hedef `~/.codex/skills/turkish-clear-writing` dizinidir.

## Kullanım

Örnek istem:

> `$turkish-clear-writing` kullanarak bu akademik metni genel okur için düzenle. Teknik terimleri ilk kullanımda kısa biçimde tanımla; iddiaları, sayıları ve atıfları değiştirme.

Skill beş tür iş yapar:

1. Var olan Türkçe metni açık ve doğal biçimde düzenler.
2. İngilizceden çevrilmiş gibi duran Türkçe söz dizimini düzeltir.
3. Metni hedef okura göre açıklar veya sadeleştirir.
4. Akademik iddia gücünü, sayıları ve kaynakları koruyarak yapay zekâ üslubunu azaltır.
5. Akademik makalede etik/şeffaflık alanlarını ve çalışma türüne uygun raporlama eksiklerini görünür kılar.

## Proje yapısı

```text
skills/turkish-clear-writing/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── evidence-and-limitations.md
    ├── evaluation.md
    ├── examples.md
    ├── academic-article-workflow.md
    ├── research-ethics-and-reporting.md
    ├── tdk-writing-and-punctuation.md
    └── turkish-guidelines.md
scripts/check_examples.py
scripts/check_behavioral_outputs.py
scripts/validate_package.py
tests/cases.json
tests/behavioral-cases.json
tests/behavioral-outputs.json
tests/behavioral-report.md
```

## Doğrulama

Örnek koruma testini çalıştırın:

```bash
python3 scripts/check_examples.py
python3 scripts/check_behavioral_outputs.py
python3 scripts/validate_package.py
```

Agent Skill yapısını doğrulamak için Skill Creator paketindeki `quick_validate.py` kullanılabilir.

## Bilimsel kapsam

Öncelikli çalışmaların çoğu İngilizce metinleri veya İngilizce öğrenen okurları inceler. Bu proje, sonuçları Türkçeye doğrudan “kanıtlanmış kural” olarak aktarmıyor. Araştırmaların desteklediği genel ilkeleri, Türkçenin eklemeli ve büyük ölçüde baş-sonlu yapısına göre temkinli editoryal yönergelere dönüştürüyor.

Otomatik okunabilirlik puanları gerçek anlamayı ölçmez. Yüksek önem taşıyan akademik, hukuki, tıbbi veya kamusal metinlerde hedef okur denemesi ve alan uzmanı incelemesi gerekir.

Kaynaklar, tarihler ve DOI notları için [kanıt haritasına](skills/turkish-clear-writing/references/evidence-and-limitations.md) bakın.

TDK PDF’si, Google Books kitabı ve çevrimiçi kaynak PDF’leri telif ve boyut nedenleriyle pakete kopyalanmamıştır; pakette yalnızca kaynaklardan türetilen, yeniden kullanılabilir uygulama notları bulunur. Google Books kaynağı sınırlı ön izleme olduğu için yalnızca erişilebilen içerik kullanılmıştır. Çevrimiçi etik, dizin ve raporlama kuralları gönderimden önce güncel resmî sayfalarından yeniden doğrulanmalıdır.

## Lisans

MIT
