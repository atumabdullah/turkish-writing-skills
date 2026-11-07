# Değişiklik günlüğü

## 0.9.1 — 2026-11-08

- Özgün `plot_interactions.py` eklendi: faktöriyel `factorial_interaction` ve karma model `mixed_interaction` görselleştirmeleri, bilimsel şekil stili ve ham noktalar.
- Faktöriyel `uygulama × doz` çizimlerinde sayısal doz aralıkları, hücre ortalamaları ve seçilebilir SD/SEM/ayrı hücre Student t %95 güven aralıkları sağlandı.
- Karma modelin `prediction_grid` alanında sabit etkilere ait popülasyon kestirimleri ve asimptotik %95 güven bantları hesaplanıyor; grafik modelleri yeniden çalıştırmadan bunları kullanıyor.
- Ham veri SHA-256, deney birimi, örneklem ve faktöriyel hücre/tahmin ızgarası tutarlılığı kontrol ediliyor; uyumsuz veri/rapor çiftleri reddediliyor. Yeni anlamlılık p değeri, güven aralığı fark testi veya harf uydurulmuyor.
- PNG/PDF/SVG yayın şekilleri, `interaction_table.csv`, `interaction_metadata.json` ve `interaction_caption.md` alt yazı dosyası ile örnek ve bilimsel sınır belgeleri eklendi.
- `check_interaction_graphs.py` ile modeli gerçekten çalıştıran uçtan uca sentetik testler; veri/rapor çakışması ve bozulmuş model girdileri için regresyon testleri GitHub Actions'a eklendi.
- Önceki akademik yazım, DOI, genel grafik ve gelişmiş istatistik modülleri korundu.


## 0.9.0 — 2026-11-08

- Açık analiz seçimi ve deney birimi denetimleriyle dört gelişmiş istatistik yöntemi için `advanced_statistics.py` eklendi: iki faktörlü Type III ANOVA (sum-kodlama), Pearson/Spearman korelasyonu, HC3 çoklu doğrusal regresyon ve rastgele kesişimli doğrusal karma model.
- Komut satırı analiz kipleri: `factorial`, `correlation`, `regression`, `mixed`; yöntemler tasarıma göre araştırmacı tarafından seçilir.
- ANOVA'da etkileşim, F/p, kısmi eta-kare, hücre örneklem sayıları ve artık/varyans tanıları; korelasyonda çiftler bazında n ve Holm/FDR düzeltmesi.
- Regresyonda sağlam SE, güven aralığı, R², VIF ve heteroskedastisite tanısı; karma modelde doğrusal zaman × grup etkileşimi, ML yakınsama ve varyans bileşenleri.
- Deney birimi tekrarı, uygunsuz eksik faktör hücresi, teknik alt örnek, birim-zaman tekrarı, kollinearite, grup değişimi, yetersiz veri ve yakınsamama için korumalar.
- Codex incelemesinde bulunan `C`/`Q` Patsy formül yardımcı adı çakışmaları ve `const` adlı sayısal yordayıcının intercept ile çakışması izole edilmiş model sütunlarıyla düzeltildi; bağımsız regresyon testleri eklendi.
- Tekrar üretilebilir JSON/CSV/Markdown çıktı; kaynak SHA-256 ve paket sürümü; kapsam sınırları ve `check_advanced_statistics.py` sentetik regresyon testleri eklendi.
- Önceki Türkçe yazım, DOI, tek faktörlü analiz ve beş bilimsel grafik türü aynen korundu.


## 0.8.0 — 2026-11-08

- Yayın kalitesinde betimsel grafikler için ortak Matplotlib stili ve beş grafik türü (`box_jitter`, `grouped_bar`, `line_plot`, `correlation_heatmap`, `multi_panel`) eklendi.
- CSV/XLSX okuma, sayısal/kategorik sütun denetimi, eksik değer politikası, deney birimi ID denetimi ve sayısal doz sıralaması eklendi.
- Codex incelemesinde yakalanan, pandas'ın tekrar eden CSV/Excel sütunlarını sessizce yeniden adlandırması önlendi; özgün başlık satırında mükerrer/boş ad denetimi ve regresyon testleri eklendi.
- 200–600 DPI PNG ve vektörel PDF/SVG, kaynak dosya SHA-256 özeti ve makine okunabilir `plot_metadata.json` ile yeniden üretilebilir çıktı desteği eklendi.
- Korelasyon haritalarında çift bazında n, undefined korelasyon için NA ve eksik veriye ilişkin açıklama eklendi; grafikler istatistiksel anlamlılık iddiasında bulunmaz.
- Sınırlamalar, dergi öncesi kalite kontrolü, kullanma örnekleri ve sentetik örnek dosyası belgelendi.
- Beş grafik türü, çıktı dosyaları, CSV/XLSX, istatistiksel belirsizlik uyarıları ve hatalı veri durumları için sentetik GitHub Actions regresyon testleri eklendi.
- Önceki Türkçe yazım, etik, DOI ve tek faktörlü çıkarımsal istatistik modülleri korundu.


## 0.7.1 — 2026-11-07

- Codex incelemesindeki Levene tanısının NaN üretmesi durumunda raporun durması düzeltildi; tanı değeri `null` ve gerekçeli uyarı olarak kaydediliyor, geçerli analiz çıktıları korunuyor.
- Kruskal–Wallis için grup içi sabit veriler, gruplar farklıysa yanlışlıkla reddedilmiyor; bütün gözlemler aynı olduğunda uygun hata korunuyor.
- Her iki sınır durumu, ayrışan sabit gruplar ve bütünüyle aynı gözlemler için sentetik regresyon testleri eklendi.
- Eski yazım/DOI testleri ve Claude kurulum paketi değişmeden korunarak sürüm 0.7.1'e yükseltildi.


## 0.7.0 — 2026-11-07

- Akademik veri analizi ve yayın kalitesinde bilimsel grafik ihtiyacı için isteğe bağlı yönlendirme eklendi; yalnızca metin düzenlemede hesaplama zorunlu değil.
- Deney birimi, yalancı tekerrür, faktöriyel/bloklu/tekrarlı desen, eksik veri, varsayımlar ve çoklu karşılaştırma kontrolleri belgelendi.
- Tek faktörlü bağımsız gruplar için CSV/XLSX tabanlı betimsel analiz, tek yönlü ANOVA + Tukey, Welch ANOVA + Holm düzeltilmiş ikili Welch testleri ve Kruskal–Wallis içeren Python betiği eklendi.
- Ham noktaları gösteren yayın şekilleri 300 DPI PNG ve vektör PDF/SVG olarak dışa aktarılıyor; JSON raporlar ve sentetik regresyon testleri eklendi.
- Chen Liu'nun Figures for Papers deposuna kaynak verildi; CC BY-NC lisanslı kaynak kodu/görselleri MIT projemize aktarılmadı.


## 0.6.0 — 2026-11-06

- `write`, `rewrite` ve metni değiştirmeyen `audit` modları açıkça ayrıldı; akademik, kurumsal, teknik ve genel metin profilleri belgelendi.
- Türkçe üslup, seçilmiş TDK yazımı ve kalıplaşmış ifadeler için bağımlılıksız, açıklanabilir bir komut satırı denetleyicisi eklendi.
- Üslup bulguları kesin yapay zekâ yazarlık kararı olarak sunulmuyor; akademik ve teknik profillerde genel klişe uyarılarının önceliği düşürülüyor.
- `--compare` ile kaynak ve düzenlenmiş metindeki sayısal belirteçler ve DOI değişiklikleri için sınırlı ön kontrol eklendi; anlamsal eşdeğerlik iddiası özellikle reddedildi.
- Kod bloklarını, satır içi kodu, bağlantıları ve DOI'leri denetim dışında tutma; konum bilgisi, JSON çıktı ve 10 ağsız regresyon testi eklendi.
- Yeni testler GitHub Actions'a ve paket doğrulamasına bağlandı. Önceki DOI ve akademik davranış koruma katmanları korundu.

## 0.5.0 — 2026-11-01

- DOI çözümleme, Crossref metadata sorgusu ve başlık–ilk yazar–yıl eşleştirmesi yapan doğrulama katmanı eklendi.
- Crossref ve Retraction Watch kayıtlarındaki geri çekme, düzeltme, endişe ifadesi ve diğer yayın sonrası güncellemeler görünür uyarılara dönüştürüldü.
- Crossref dışındaki geçerli DOI'ler, çözümlenemeyen DOI'lerden ayrıldı; kaynakça girdilerinin otomatik değiştirilmesi engellendi.
- Sonuçların JSON, Markdown ve XLSX olarak dışa aktarılması sağlandı.
- Ağ gerektirmeyen sentetik DOI, metadata uyumsuzluğu, geri çekme ve servis hatası testleri eklendi.

## 0.4.2 — 2026-11-01

- Karşılaştırmalı özetlerde amaç veya yöntemde tanıtılan bütün grupların temel bulgularda temsil edilip edilmediğini denetleyen kural eklendi.
- Eksik bir karşılaştırma kolu için “etkisizdi” ya da “anlamlı fark yoktu” gibi sonuçlar uydurmak yerine doğrulama notu verme zorunluluğu getirildi.
- Gerçek Claude kullanımında gözlenen eksik karşılaştırma kolu sorunu için on birinci sentetik davranış vakası eklendi.

## 0.4.1 — 2026-10-31

- Gerçek metin gerektirmeyen on vakalık sentetik davranış test seti eklendi.
- Sayı, atıf, DOI, etik bilgi, gönderim belirsizliği, nedensellik, bölüm ayrımı, TDK ve raporlama kılavuzu seçimleri sınandı.
- Örnek çıktılardaki korunacak, zorunlu ve yasaklı öğeleri denetleyen bağımlılıksız test betiği eklendi.
- İlk testin yazar tarafından yürütülen duman testi olduğu ve bağımsız doğrulama yerine geçmediği belgelendi.

## 0.4.0 — 2026-10-31

- YÖK Bilimsel Araştırma ve Yayın Etiği Yönergesi etik risk denetimi olarak eklendi.
- TR Dizin ölçütlerinin makale düzeyi beklentileri, dergi yönetimine ait hükümlerden ayrıldı.
- TÜBİTAK ULAKBİM’in makale bölümlerine ilişkin işlevsel önerileri eklendi; eski/sabit biçim önerileri evrenselleştirilmedi.
- EQUATOR kılavuzları sağlık araştırmalarında gerçek çalışma türüne göre seçilecek biçimde eşlendi.
- Etik kurul/onam, kayıt, ORCID, finansman ve benzeri tanımlayıcıları koruyan örnek test eklendi.

## 0.3.0 — 2026-10-31

- TDK yazım ve noktalama kaynağından akademik yazıya dönük denetim yönergeleri eklendi.
- Akademik makale planlama, başlık–özet, literatür tarama, yöntem, bulgular, tartışma ve kaynakça iş akışı eklendi.
- Kaynak önceliği ve hedef dergi biçiminin genel yazım tercihlerine üstünlüğü açıklandı.
- Google Books sınırlı ön izlemesinin erişim sınırı kaynak notlarına işlendi.

## 0.2.0 — 2026-10-31

- Beş öncelikli çalışma kaynak ve tarih düzeyinde doğrulandı.
- Kanıt, temkinli aktarım ve Türkçeye özgü uyarlama katmanları ayrıldı.
- Türkçe söz dizimi, eklemeli morfoloji, isim zincirleri, gönderim, bağdaşıklık ve bilgi yoğunluğu yönergeleri genişletildi.
- Akademik kesinlik, sayı ve atıf koruma denetimleri eklendi.
- Önce–sonra örnekleri ile küçük otomatik test paketi eklendi.

## 0.1.0

- İlk Agent Skill yapısı, temel Türkçe açık yazım yönergeleri ve proje belgeleri oluşturuldu.
