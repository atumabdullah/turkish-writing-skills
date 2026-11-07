# Bilimsel grafik motoru — v0.8.0

Bu belgenin kapsamı, **ham CSV/XLSX verisinden betimsel, yeniden üretilebilir, yayın hazırlığına uygun şekiller** oluşturmaktır. Tek bir grafikten istatistiksel anlamlılık veya nedensellik çıkarmayın. İstatistiksel test gerekiyorsa öncelikle gerçek deney birimini, tasarımı, hipotezi ve uygun modeli doğrulayın. Ayrı istatistik modülü yalnızca tek faktörlü bağımsız gruplarda çıkarımsal hesaplama yapar.

## Başlangıç

İsteğe bağlı bağımlılıkları yükleyin:

```bash
python3 -m pip install -r skills/turkish-clear-writing/requirements-statistics.txt
```

Çalıştırılabilir betik: `skills/turkish-clear-writing/scripts/plot_scientific.py`. Grafik şablonları aynı dizindeki `figure_style.py` dosyasında tanımlanan ortak stili kullanır.

Her komutta `--output` ile **ayrı bir çıktı klasörü** belirleyin. Çıktı klasöründe `figure.png` (varsayılan 300 DPI, `--dpi` ile 200–600), `figure.pdf`, `figure.svg` ve `plot_metadata.json` dosyaları oluşturulur. Önceden aynı isimde dosyalar varsa üzerlerine yazılır.

## Veri hazırlığı

- CSV veya XLSX/XLSM dosyası; ilk satır sütun adları, sonraki satırlar gözlemler. **Aynı veya boş sütun başlıkları**, pandas yeniden adlandırmadan önce özgün CSV/Excel başlık satırında kontrol edilerek reddedilir.
- Bir sütundaki gerçek birim ve ölçek değişmemeli. Tekrarlı ölçüm veya alt örnekler aynı birimmiş gibi birleştirilmemeli.
- `--unit saksi_id` kullanılırsa deney birimi ID'leri eksiksiz ve tekil olmalıdır; aynı ID birden fazla satırdaysa betik analizi reddeder. Bunun olmadığı veri otomatik bağımsız kabul edilmez; araştırmacı deseni ayrıca doğrular.
- Sayısal değişkenler gerçek sayılar olmalıdır. Türkçe Excel'den aktarımda ondalık ayırıcıları kontrol edin. Eksik değerler box/bar/line/multi-panel için hata verir; korelasyon ısı haritasında **yalnızca eksik çiftler dışlanır**, ikili örneklem sayıları rapora yazılır.
- Grafikler betimseldir: ANOVA, post-hoc, p değeri, güven aralığı veya anlamlılık harfi üretmez. Hata çubukları seçilen **SD** veya **SEM**'dir; güven aralığı değildir.

## Beş grafik türü

| Tür | Amaç | Zorunlu parametreler |
| --- | --- | --- |
| `box_jitter` | Gruplara göre kutu ve ham gözlem noktaları | `--group`, `--y` |
| `grouped_bar` | İki kategorik boyutta ortalama ve SD/SEM | `--group`, `--subgroup`, `--y` |
| `line_plot` | Sayısal doz/zaman boyunca eğilim ve SD/SEM | `--x`, `--y`; isteğe bağlı `--group` |
| `correlation_heatmap` | Pearson veya Spearman korelasyon matrisi | `--columns` (2–12 sütun); `--method` |
| `multi_panel` | 2–4 yanıt değişkenini aynı şeklin panellerinde göstermek | `--group`, `--columns` (2–4 sütun) |

### Kullanım örnekleri

```bash
# 1. Saksılardaki bağımsız büyüme gözlemleri
python3 skills/turkish-clear-writing/scripts/plot_scientific.py deneme.xlsx \
  --kind box_jitter --group uygulama --y bitki_boyu_cm \
  --unit saksi_id --output figurler/boy

# 2. Uygulama × doz gruplarının ortalama kuru ağırlıkları
python3 skills/turkish-clear-writing/scripts/plot_scientific.py deneme.xlsx \
  --kind grouped_bar --group uygulama --subgroup doz \
  --y kuru_agirlik_g --error sd --unit saksi_id --output figurler/kuru_agirlik

# 3. Sayısal doz boyunca SPAD eğilimleri (tekrarlı x gözlemleri ortalanır)
python3 skills/turkish-clear-writing/scripts/plot_scientific.py deneme.xlsx \
  --kind line_plot --x doz --y spad --group uygulama \
  --unit saksi_id --output figurler/spad

# 4. Değişkenler arası betimsel korelasyon matrisi
python3 skills/turkish-clear-writing/scripts/plot_scientific.py deneme.xlsx \
  --kind correlation_heatmap --columns spad,bitki_boyu_cm,doku_zn \
  --method spearman --unit saksi_id --output figurler/korelasyon

# 5. Üç büyüme ölçüsünü aynı şeklin ayrı panellerinde göster
python3 skills/turkish-clear-writing/scripts/plot_scientific.py deneme.xlsx \
  --kind multi_panel --group uygulama \
  --columns bitki_boyu_cm,kok_boyu_cm,kuru_agirlik_g \
  --unit saksi_id --output figurler/buyume_paneli
```

## Rapor ve görsel doğrulama

`plot_metadata.json` içinde veri dosyasının SHA-256 özeti, kullanılan sütunlar, satır sayısı, grafik tipi, hesaplamalarda kullanılan hata çubuğu türü, yazılım sürümleri ve uyarılar saklanır. Gruplandırılmış grafikte n/ortalama/SD; ısı haritasında r ve **değişken çifti bazında n** kaydedilir. JSON'a ham gözlemler veya deney birimi kimlikleri kopyalanmaz.

Her figürü açıp kırpılma, etiket çakışması, birim ve lejantı gözle inceleyin. Hedef derginin istediği tipografi, boyut ve çözünürlük farklıysa bu kurallar genel stilin önündedir. SEM, gözlemlerin yayılımı yerine ortalamanın belirsizliğine ilişkin bir ölçüdür; küçük n için uygun bağlam olmadan belirsizlik kanıtı gibi kullanmayın.

Doz grafikleri **sayısal** x gerektirir. `line_plot` aynı grup–doz noktasındaki tekrarlardan ortalama üretir ve bunu uyarı olarak kaydeder; tekrarlı ölçüm modelini hesaplamaz. `grouped_bar` üzerinde eksik grup–alt grup kombinasyonları sıfır gösterilmez, boş bırakılır. Kutu grafiği düşük n'de sınırlandırılmış yorum gerektirir.

## Genişleme sınırları

Bu sürümde grafik **betimsel** olarak üretilebilir; etkileşim testi, faktöriyel ANOVA, karma model, regresyon kestirim eğrileri, yayın dergisine birebir tema, otomatik istatistiksel harf ve 3B grafik henüz yoktur. Bu modül, Chen Liu'nun [Figures for Papers](https://github.com/ChenLiu-1996/figures4papers) projesinden bağımsız yazılmıştır; CC BY-NC lisanslı şablon kodlarını kopyalamaz.

Sıradaki sürümler: `v0.9.0` gelişmiş istatistiksel analiz, `v0.9.1` etkileşim görselleştirmesi, `v1.0.0` derinleştirilmiş bilimsel yöntem denetimi. Bu gelecek özellikler burada mevcut olarak iddia edilmez.

## Doğrulama

```bash
python3 scripts/check_publication_figures.py
```

Sentetik CSV/XLSX kayıtları üzerinde beş grafik türü, SVG/PDF/PNG dışa aktarma, açıklayıcı JSON raporu, eksik değerler, tekerrür ID'leri ve geçersiz parametreler test edilir. Gerçek bir araştırmanın tasarım ve biyolojik yorumunun yerini almaz.
