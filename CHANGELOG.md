# Değişiklik günlüğü

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
