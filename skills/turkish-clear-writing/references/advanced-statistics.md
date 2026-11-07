# Gelişmiş istatistiksel analiz: v0.9.0

Bu modül ham CSV/XLSX verilerinin **açıkça seçilen** dört çıkarımsal yönteme göre işlenmesine yarar. Analiz tek başına çalışmanın tasarımını doğrulamaz. Araştırmacı bağımsız deney birimini, zaman yapısını, randomizasyonu, varsayımları ve hipotezi önceden belirlemelidir.

## Kurulum

```bash
python3 -m pip install -r skills/turkish-clear-writing/requirements-statistics.txt
```

Çalıştırılabilir dosya: `skills/turkish-clear-writing/scripts/advanced_statistics.py`. Çalışma kipleri: `factorial`, `correlation`, `regression`, `mixed`.

Tüm yöntemlerde `--unit` zorunludur. Faktöriyel, korelasyon ve OLS regresyonda her bağımsız birim **bir satır** olmalıdır. Aynı birimin birden çok zaman ölçümü yalnızca `mixed` yönteminde kabul edilir; bu yöntemde tek birim-zaman eşleşmesinde birden fazla ölçüm bulunamaz. Teknik alt örnekler ayrı tekerrür değildir.

## Dört analiz türü

### 1. İki faktörlü ANOVA (bağımsız gruplar)

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py deneme.xlsx \
  --analysis factorial --unit saksi_id --value kuru_agirlik_g \
  --factor-a uygulama --factor-b doz --output analiz/faktoriyel
```

İki kategorik faktör, faktör başına 2–12 düzey, **bütün hücreler mevcut** ve her hücrede en az iki bağımsız deney birimi aranır. Model `OLS: C(faktor_a, Sum) * C(faktor_b, Sum)` ve Type III varyans analizi kullanır. Etkileşim, ana etkiler, serbestlik derecesi, F, p ve kısmi eta-kare raporlanır. Shapiro–Wilk artık normalliği ve hücre bazlı medyan merkezli Levene tanıları verilir.

Önemli: Ana etkiler **etkileşim varsa** doğrudan, koşulsuz doz/uygulama farkı şeklinde yorumlanmamalıdır. Dengesiz hücrelerde Type III sonuçlarının yorumu özellikle dikkat ister. Otomatik Tukey harfleri ve basit etki karşılaştırmaları **hesaplanmaz**. Bloklu, bölünmüş parseller veya aynı saksıdan tekrarlı ölçümler **bu modele uygun değildir**.

### 2. Korelasyon

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py deneme.xlsx \
  --analysis correlation --unit saksi_id \
  --columns bitki_boyu_cm,spad,doku_zn \
  --method pearson --adjust holm --output analiz/korelasyon
```

İki–on iki sayısal sütun arasında Pearson veya Spearman ilişki katsayısı, ikili örneklem sayısı, ham p ve seçilen Holm/FDR-BH düzeltilmiş p hesaplanır. Varsayılan **Holm** düzeltmesidir; `--adjust none` isteğe bağlıdır ve çoklu test riskini ortadan kaldırmaz. Eksik veri yalnızca **ilgili çiftte** dışlanır; veri silme işlemi sessiz yapılmaz. Sabit değişken veya 3'ten az eşleşme olduğunda katsayı/p değeri `null` ve uyarı üretilir. Korelasyon nedensellik kanıtı değildir.

### 3. Sayısal yordayıcılarla OLS regresyon

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py deneme.xlsx \
  --analysis regression --unit saksi_id --value doku_zn \
  --predictors spad,kuru_agirlik_g \
  --output analiz/regresyon
```

1–8 sayısal yordayıcı ve kesişim terimiyle çoklu doğrusal regresyon. HC3 heteroskedastisiteye dayanıklı standart hatalar, %95 güven aralıkları, z ve iki taraflı p değerleri, R² / düzeltilmiş R², artık Shapiro–Wilk, Breusch–Pagan ve VIF tanıları hesaplanır. Tasarım matrisi tam sıralı değilse analiz durur. En az 10 birim ve terim başına en az 5 birim koşulu **yalnızca temel güvenlik eşiğidir**; güç analizi değildir. Gözlemsel regresyon sonuçları nedensellik olarak yazılamaz.

### 4. Tekrarlı ölçümler: rastgele kesişimli karma model

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py zaman.xlsx \
  --analysis mixed --unit saksi_id --value spad \
  --time gun --group uygulama --interaction \
  --output analiz/karma
```

Aynı birimden **en az iki farklı sayısal zamanda ölçüm** alınmış olmalıdır. En az 6 bağımsız birim, uygulama grubu veriliyorsa grup başına en az 3 bağımsız birim gerekir. Birim–zaman eşleşmeleri benzersiz olmalı; uygulama grubu birim içinde değişmemelidir. En az iki farklı zaman gereklidir. Model `MixedLM` ile **ML rastgele kesişim** ve sayısal doğrusal zaman eğilimi, tercihen isteğe bağlı uygulama ve zaman×uygulama etkileşimi sağlar. Yakınsamayan model reddedilir; sınır varyans kestirimleri uyarılır.

Model rastgele eğim, ek blok, seri otokorelasyon, doğrusal olmayan zaman, çapraz/çaprazlanmış tasarım, eşleştirilmiş müdahale ya da ileri eksik veri mekanizması analizi içermez. Çoğu gerçek araştırmada model seçimi ve tanılaması gerekebilir.

## Veri denetimi, rapor ve hesaplama sınırları

- Kaynak CSV/XLSX başlıkları pandas okumadan önce kontrol edilir. Mükerrer veya boş başlıklar reddedilir.
- Seçilen sayısal sütunlarda sonsuz değer, nonnumeric giriş ve uygun olmayan eksiklikler engellenir. Korelasyonda çift bazında eksik veri politikası farklıdır ve belirtilir.
- İstatistikler **yalnızca kullanıcı tarafından sağlanan gerçek ham veriden** hesaplanır. Anlamlılık p değeri, güven aralığı, Tukey harfi veya regresyon katsayısı uydurulmaz.
- Her çıktı klasöründe `results.json`, `table.csv` ve `results.md` bulunur. Veri dosyası SHA-256 özeti ve kütüphane sürümleri kaydedilir; kişisel ham veri ve birim ID'leri rapora dökülmez.
- `results.json` sıkı JSON olarak yazılır; hesaplanamayan sayısal tanılar `null` ile raporlanır.
- Çıktı dosyalarını açıp deney birimi, n, etki büyüklüğü, yön, birim, belirsizlik ve araştırma sorusuyla uyumunu manuel denetleyin.
- Aynı çıktı klasöründeki eski dosyalar üzerine yazılabilir; her veri analizi için ayrı klasör kullanılmalıdır.
- Dört kipin kapsamı sınırlıdır; bilimsel yöntem uzmanı incelemesinin ve önceden belirlenen istatistik planının yerini almaz.

## Sürüm yol haritası

- `v0.9.1`: faktör etkileşimlerini görselleştirme ve istatistiksel sonuçlarla grafiklerin bağlanması.
- `v1.0.0`: daha kapsamlı bilimsel yöntem/deney deseni denetimi ve otomatik denetim raporu.

Bu gelecek özellikler `v0.9.0` içinde mevcut değildir.

## Otomatik test

```bash
python3 scripts/check_advanced_statistics.py
```

Yalnızca **sentetik** veri ile dört modelin sonuçları, eksik hücre, tekrar eden birim, yetersiz örneklem, kollinearite, birim-zaman tekrarı, grup değişimi, duplicate dosya başlığı ve tanımsız korelasyon durumları doğrulanır.
