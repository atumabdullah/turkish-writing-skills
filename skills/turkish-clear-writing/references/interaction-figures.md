# Model sonuçlarına bağlı etkileşim grafikleri — v0.9.1

Bu modül, v0.9.0'da çalıştırılan **iki faktörlü bağımsız gruplar ANOVA** veya **rastgele kesişimli doğrusal karma model** sonuçlarını, doğrulanmış ham veriye bağlı yayın görsellerine dönüştürür. Yeni istatistiksel test **çalıştırmaz**; önceden hesaplanan raporu tekrar kullanır.

## Analizi ve grafiği aynı veriye bağlama

Önce gerçek **bağımsız deney birimi** ve doğru deney tasarımı teyit edilir. Aynı veri dosyası önce `advanced_statistics.py` ile analiz edilir, sonra `plot_interactions.py` tarafından kullanılır. Grafik betiği:

- Kaynak verinin SHA-256 özetini ve satır sayısını `results.json` ile karşılaştırır; eşleşmezse hata verir.
- Analiz raporunun `experimental_unit` ve `model.response_column` alanlarını kullanır.
- Faktöriyel analizde raporlanan her hücrenin **n, ortalama ve SD** değerlerini ham veriden yeniden doğrular.
- Karma modelde raporlanmış popülasyon düzeyindeki tahmin ızgarasının **birim sayısını, gözlenen ortalamalarını ve zaman/grup kapsamını** doğrular.
- Model sonucu ve ham veri uyumsuzsa grafik üretmez; `p` veya post-hoc harflerini asla uydurmaz.

## 1. Faktöriyel ANOVA: uygulama × doz

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py deneme.xlsx \
  --analysis factorial --unit saksi_id --value kuru_agirlik_g \
  --factor-a uygulama --factor-b doz --output analiz/faktoriyel

python3 skills/turkish-clear-writing/scripts/plot_interactions.py deneme.xlsx \
  --results analiz/faktoriyel/results.json --uncertainty ci95 \
  --output figurler/uygulama_doz
```

Faktöriyel grafik:
- X ekseninde **ikinci faktörün düzeyleri** (örn. 0, 50, 100 mg Zn L⁻¹); sayısal dozda **gerçek sayısal aralıklar** korunur. Sayısal dozlarda seri ortalamaları **hiç kaydırılmaz**; yalnızca ham noktaların küçük yatay saçılımı en yakın iki doz arasındaki farkla sınırlandırılır (0, 1, 1000 gibi düzensiz dozlar dâhil).
- Her çizgi birinci faktörü (örn. kimyasal, yeşil sentez), büyük işaretler hücre ortalamasını, küçük yarı saydam noktalar **bağımsız deney birimlerini** gösterir.
- Hata çubuğu varsayılan olarak **hücre ortalaması için ayrı ayrı Student t tabanlı %95 güven aralığıdır**. `--uncertainty sd`, `sem` veya `none` tercih edilebilir. Bu aralıklar iki ortalamanın farkı için güven aralığı değildir.
- Type III ANOVA modelinin etkileşim F ve p değerleri **bağlı analiz raporunda** kalır; şekle anlamlılık yıldızı, harf veya doğrulanmamış karşılaştırma eklenmez. Farklı veya örtüşen güven aralıkları tek başına etkileşimin anlamlılığına karar vermez.
- En fazla 7 çizgi, 12 x düzeyi ve hücre başına en az 2 bağımsız birim. Eksik faktöriyel hücrelerin grafiğini analiz yürütmeden üretmeyin.

## 2. Karma model: zaman × uygulama

```bash
python3 skills/turkish-clear-writing/scripts/advanced_statistics.py spad_zaman.xlsx \
  --analysis mixed --unit saksi_id --time gun --value spad \
  --group uygulama --interaction --output analiz/karma

python3 skills/turkish-clear-writing/scripts/plot_interactions.py spad_zaman.xlsx \
  --results analiz/karma/results.json --output figurler/zaman_uygulama
```

Karma model grafiği:
- Sürekli çizgiler **modelin popülasyon düzeyindeki sabit etki kestirimleridir**, yarı saydam bölgeler **bu kestirimlere ait asimptotik %95 güven aralıklarıdır**, küçük simgeler ise her zaman–grup için **gözlenen aritmetik ortalamalardır**.
- Aralıklar **bireysel gözlem tahmin aralığı değildir** ve saksı/deneklerin gelecekteki değişkenliğini temsil etmez.
- Model yalnızca **sayısal, doğrusal zaman** ve **rastgele kesişim** içerir. Rastgele eğim, seri otokorelasyon, bloklama, doğrusal olmayan eğilim ve karmaşık eksik veri mekanizmaları hâlen tasarım dışıdır.
- Tahmin noktaları, **ilgili grupta gerçekten ölçüm yapılmış zamanlarla** sınırlıdır; grup gözlemleri dışında görünmez ekstrapolasyon yapılmaz. Noktalar arasındaki çizgiler, önceden kurulmuş doğrusal modelin kestirimidir.
- Tekrarlı gözlemler bağımsız birimler gibi gösterilmez. Bir gruptan diğerine farklı görünen eğimler, otomatik ikili anlamlılık karşılaştırması değildir.

## Çıktı ve yeniden üretilebilirlik

`--output` klasöründe:
- `figure.png` (varsayılan 300 DPI; desteklenen 200–600), `figure.pdf` ve `figure.svg` (vektör);
- `interaction_table.csv` (grafikte çizilen bütün hücre veya kestirim sayıları);
- `interaction_caption.md` (hangi ortalama/CI'nin gösterildiğini ve sınırları açıklayan alt yazı);
- `interaction_metadata.json` (kaynak veri ve raporun SHA-256 özeti, analiz türü, kullanılan belirsizlik ölçüsü, satır sayısı, sürüm ve uyarılar).

Metadatalar kişi/saksı ID listeleri veya ham ölçümler içermez. Çıktı klasörü daha önce kullanıldıysa aynı dosyalar üzerine yazılır; her yeni analiz için ayrı yol seçin.

## Bilimsel kalite kontrolü

Veriyi ve tasarımı görmeden etkileşim testini “anlamlı” olarak ilan etmeyin. Hücre CI'leri ve karma model çizgi/bantları iki farklı belirsizlik kavramı taşır. Bireysel analiz p değerleri yalnızca çalıştırılmış model raporundadır; grafiğin kendisi p hesabı yapmaz.

Bütün x/y birimleri, etiketler, lejant, renk/grup uyumu ve kırpılma ayrıca görsel incelenmelidir. Hedef derginin şekil gereksinimleri genel stile üstün gelir.

Burada özgün Matplotlib/Statsmodels uygulaması kullanılır; Chen Liu'nun CC BY-NC lisanslı kaynak kodu aktarılmamıştır. Otomatik basit etki post-hoc karşılaştırmaları ve karmaşık araştırma deseni denetimi sonraki sürümlerin konusudur.

## Test

```bash
python3 scripts/check_interaction_graphs.py
```

Sentetik iki faktörlü ve tekrarlı veri üretilir; ileri analiz betiği gerçek test modelini hesaplar, etkileşim betiği modeli kaynağa bağlayarak PNG/PDF/SVG üretir. Değiştirilmiş kaynak özeti, bozulmuş model hücreleri, mükerrer CSV sütunu, bozulmuş karma tahmin ızgarası ve yanlış analiz türleri reddedilir.
