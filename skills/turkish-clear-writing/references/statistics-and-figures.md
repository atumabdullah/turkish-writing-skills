# İstatistiksel analiz ve bilimsel şekil üretimi

Bu modül, akademik yazım iş akışına **gerektiğinde** etkinleşen veri analizi ve bilimsel görselleştirme katmanı ekler. Sıradan metin düzeltmede analiz çalıştırma. Yalnızca doğrulanabilir veri ve araştırma bağlamı varsa hesapla; sonuç uydurma.

## Tetikleme ve karar

1. Önce görevi ayır: yalnızca metin düzenleme, yöntem/analiz planı, mevcut istatistik çıktısını yorumlama, ham veri analizi veya grafik üretimi.
2. Kullanıcı makale/tez bulguları, yöntem kontrolü, istatistik veya grafik istiyorsa analiz ve şekil ihtiyacını değerlendir. Veri mevcutsa gerekli olduğu ölçüde işlemi **gerçekten çalıştır**; yürütme aracı yoksa grafiği oluşturmuş gibi sunma, çalıştırılabilir betik ve engeli bildir.
3. Ham veri yoksa yalnızca verilen bulguların tutarlılığını denetle; ham veriden hesaplanması gereken F, p, güven aralığı, Tukey grupları ve hata çubuklarını üretme. Ortalama ve SD tablolarından bağımsız tekrarlar türetme.
4. Analiz istemi belirsizse eldeki tasarım bilgileriyle güvenli betimsel grafik üret; çıkarımsal test için deney deseninin eksik kalan kısmını belirt. Kullanıcı yalnızca `rewrite` veya `audit` istiyorsa veri üzerinde ek analiz yapma.

## Analiz öncesi zorunlu tasarım kontrolü

- Araştırma sorusu ve birincil sonuç değişkeni; kategorik/sürekli değişkenler; birimler ve ölçüm ölçekleri.
- Gerçek bağımsız **deney birimi** (ör. saksı, parsel, hayvan, kişi); grup sayısı, birim başına tekrarlı ölçümler ve teknik alt örnekler. Alt örnekleri bağımsız biyolojik tekerrür sayma.
- Randomizasyon, bloklama, faktöriyel desen, eşleştirme, zaman/tekrarlı ölçüm, kovaryatlar ve deney birimi düzeyinde bağımsızlık.
- Eksik değerler, aykırı gözlemler, olası veri giriş hataları, ölçüm alt sınırı, dönüşüm gerekçesi ve önceden belirlenen analiz planı. İşlemleri kaydet; eksik veriyi sessizce doldurma veya aykırı değerleri sebepsiz atma.
- Hedef dergi ve alanın istatistik/şekil raporlama beklentileri. p eşiğine göre kör test seçimi yerine varsayım ve tasarım uygunluğunu tartış.

## Yöntem eşlemesi: örnekler, otomatik hüküm değil

| Gerçek desen | Değerlendirilecek yaklaşım | Uyarı |
| --- | --- | --- |
| Tek faktörlü, **bağımsız** gruplar, sürekli çıktı | Tek yönlü ANOVA + gerekirse Tukey; değişken varyans için Welch ANOVA ve uygun çoklu karşılaştırmalar | Varyans, artıklar, n, deney birimi ve dengesiz grup kontrolü zorunlu |
| Tek faktörlü bağımsız gruplar, sıralı/uygunsuz parametrik çıktı | Kruskal–Wallis ve gerekçeli post-hoc | Grup dağılımı farklarını doğrudan ortalama farkı gibi yorumlama |
| İki veya daha fazla faktör | Faktöriyel ANOVA / genel doğrusal model | Etkileşimi incelemeden ayrı tek yönlü testlere bölme |
| Bloklu tarla/saksı denemesi | Bloğu hesaba katan ANOVA veya karma model | Bloğu yok sayma |
| Tekrarlı ölçüm / aynı birimden zaman serisi | Karma etkili model, tekrarlı ölçüm modeli veya uygun alternatif | Aynı birimi bağımsız satırlar gibi test etme |
| Korelasyon / regresyon | Pearson/Spearman, uygun regresyon, tanı grafikleri ve etki belirsizliği | Korelasyondan nedensellik çıkarma |
| Nitel/kategorik çıktı | Oran, güven aralığı, uygun kategorik model/test | Sürekli ANOVA kullanma |

Yukarıdaki liste tek başına analiz doğruluğunu garanti etmez. Önceden tanımlı hipotez, ölçüm süreci ve tasarım belirleyicidir. Çoklu sonlanımlar veya çok sayıda karşılaştırma için hata oranı kontrolünü gerekçelendir.

## Yerleşik, sınırlı yürütülebilir betik

`scripts/analyze_and_plot.py` yalnızca **tek faktörlü bağımsız grup** verisi içindir. CSV/XLSX dosyasında her deney birimi tek satır olmalıdır; `--unit` tekrarları yakalar. Varsayılan yalnızca betimleyicidir. Çıkarımsal yöntem `--analysis` ile tasarım kontrolünden **sonra bilinçli seçilir**.

```bash
python3 -m pip install -r skills/turkish-clear-writing/requirements-statistics.txt
python3 skills/turkish-clear-writing/scripts/analyze_and_plot.py deney.csv \
  --group uygulama --value bitki_boyu_cm --unit saksi_id \
  --analysis anova --output sonuclar
```

Seçenekler: `descriptive`, `anova`, `welch`, `kruskal`. ANOVA için Tukey HSD; Welch için Holm düzeltilmiş ikili Welch t testleri hesaplanır. Kruskal için post-hoc otomatik verilmez. Çıktılar `results.json`, `groups.png` (300 DPI), `groups.pdf` ve `groups.svg` dosyalarıdır. Grafik ham noktalar ve kutu dağılımını gösterir; kutu grafiği ortalama±SD değildir. Sonuç raporundaki istatistikler yöntem, etki büyüklüğü ve tanılarla birlikte incelenmelidir.

**Kapsam dışı desenlerde betiği uygunsuz şekilde kullanma:** iki faktörlü, bloklu, eşleştirilmiş, tekrarlı veya iç içe geçmiş veri için uygun model/ayrı çalışma betiği gerekir. Tek faktörlü aracın çalışması araştırma desenine uygunluk kanıtı değildir.

## Grafik üretimi ve kalite kontrolü

- Ham veri varsa dağılımı göster: kutu + bağımsız birim noktaları, gerektiğinde eşleştirilmiş çizgiler; sadece ortalamalar farkları gizleyebilir. Birim sayısını (`n`) açıkla.
- Doz–yanıt/zaman için gerçek ölçüm zamanlarıyla çizgi/scatter; korelasyonda nokta grafiği ve uygunsa güven aralığı; çok değişkenli desenlerde etkileşim grafiği; korelasyon matrisi için uygun ısı haritası. 3B grafik yalnızca açıklama gücü belirginse.
- Yüzdelik yığılmış çubuk veya radar grafikleri analitik doğruluğu azaltıyorsa gösterişli oldukları için kullanma. Sıfırdan başlamayan çubuk grafik algıyı yanıltabilir; eksen kesmelerini açık göster.
- Y ekseni birimi, ondalık gösterim, grup açıklaması, `n`, hata çubuğunun türü (SD, SE, CI), anlamlılık düzeyi ve çoklu karşılaştırma yöntemini şekil açıklamasında belirt. İstatistiksel harfler ancak uygun ve çalıştırılmış post-hoc çıktısına dayanıyorsa eklenir.
- Renk-körlüğüne uygun, gri baskıda ayrışan palet; tutarlı tipografi ve başlık/gövde hiyerarşisi; veri–metin–tablo–şekil sayısal tutarlılığı. Derginin ölçü/font/DPI kuralları varsa bunlar üstündür.
- PNG (genellikle 300 DPI), ölçeklenebilir SVG ve baskıya uygun PDF üret. Çıktıları açıp etiket taşıması, kesilme, font ve lejantı gözle doğrula.
- Analiz kodu, veri kaynağı, sürümler, temizleme kararları ve dönüşümleri kaydet; sonucu yeniden üretilebilir kıl. Kişisel/mahrem verileri şekil dosyası ya da test fixtures içinde yayımlama.

## Örnek: toprak ve bitki besleme

Yapraktan Zn uygulaması denemesinde fenolojik dönemler aynı saksıda tekrarlandıysa her dönemi ayrı bağımsız saksı saymak yanlıştır. Uygulama × doz faktöriyel ise etkileşim değerlendirilir. Blok varsa modelde temsil edilir. Tek yönlü ANOVA/Tukey yalnızca gerçek deney deseni buna izin verdiğinde kullanılır. SPAD, büyüme, enzim aktivitesi veya doku Zn için farklı alt grup ve tekerrür yapılarını birbirine karıştırma.

## Kaynak ve lisans sınırı

Grafik tasarımında [Chen Liu, Figures for Papers](https://github.com/ChenLiu-1996/figures4papers) içindeki yayın görselleştirmesi ilkelerinden **kavramsal olarak** yararlanılır. Kaynak deponun lisansı [CC BY-NC 4.0](https://github.com/ChenLiu-1996/figures4papers/blob/main/LICENSE) olduğundan kodu, görselleri veya metinleri bu MIT lisanslı projeye kopyalamadık. Buradaki analiz ve çizim betiği ayrı yazılmıştır; upstream projenin onayını veya aynı işlev kapsamını iddia etmez.
