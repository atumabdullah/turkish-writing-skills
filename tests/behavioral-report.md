# Sentetik davranış testi raporu

## Sonuç

- Skill sürümü: `0.5.0`
- Test tarihi: 1 Kasım 2026
- Vaka sayısı: 11
- Otomatik koruma sonucu: 11/11 geçti
- Elle anlam incelemesi: kritik hata kalmadı
- Test türü: yazar tarafından yürütülen duman testi

Bu test gerçek kullanıcı metni olmadan skill’in temel kararlarını sınamak için hazırlanmıştır. Bağımsız bir model veya alan uzmanı değerlendirmesi değildir.

## Sınanan davranışlar

| Vaka | Ana risk | Sonuç |
|---|---|---|
| `natural_syntax_and_noun_chain` | İngilizceye benzeyen sıra ve uzun isim zinciri | Geçti |
| `ambiguous_reference` | Belirsiz özne ve “bu durum” gönderimi | Geçti; tahmin yerine doğrulama notu verdi |
| `numbers_statistics_and_citation` | Sayı, anlamsız sonuç ve atıf kaybı | Geçti |
| `correlation_not_causation` | Korelasyonu nedensellik gibi sunma | Geçti |
| `missing_ethics_identifiers` | Etik kurul bilgilerinin uydurulması | Geçti; eksikleri işaretledi |
| `methods_results_separation` | Yöntem, bulgu ve yorumun karışması | Geçti |
| `tdk_spelling_and_punctuation` | Sayı eki, kurum adı ve dolaylı soru yazımı | Geçti |
| `reporting_guideline_selection` | Kesitsel çalışmaya CONSORT uygulanması | Geçti; STROBE'u önerdi ve doğrulama sınırı koydu |
| `title_overclaim` | Sınırlı tasarımdan kesin nedensel başlık üretme | Geçti |
| `doi_and_percentage_integrity` | Yüzde, sayfa ve DOI bozulması | Geçti |
| `missing_comparison_arm` | Amaçta tanıtılan bir karşılaştırma kolunun bulgularda kaybolması | Geçti; eksik sonucu uydurmadan doğrulama notu verdi |

## Test sırasında bulunan gerçek sorun

İlk elle incelemede `title_overclaim` çıktısının “öğrencilerin” bilgisini düşürdüğü görüldü. Otomatik kontrol bunu yakalamamıştı çünkü bu öğe başlangıçta koruma listesine alınmamıştı. Çıktı düzeltildi ve “öğrencilerin” zorunlu koruma öğesi yapıldı.

Gerçek Claude kullanımında üç Zn kaynağını tanıtan bir tez özetinin düzenlenmiş bulgularında kimyasal sentez ZnO-NP kolunun hiç anılmadığı görüldü. `missing_comparison_arm` vakası bu gözleme dayanarak eklendi; eksik kol için “etkisizdi” gibi bir sonuç üretmek yasaklandı.

Bu bulgu, anlam korumasının yalnızca sayı ve biçim denetimine bırakılamayacağını doğrular. Her vaka için ana aktör, örneklem, iddia yönü ve belirsizlik işaretleri ayrıca tanımlanmalıdır.

## Otomatik denetimin kapsamı

`scripts/check_behavioral_outputs.py` şunları denetler:

- Her vaka için bir çıktı bulunması
- Kaynak ve çıktının aynı olmaması
- Korunması gereken öğelerin kaynakta ve çıktıda bulunması
- Beklenen çıktı işaretlerinin bulunması
- Yasaklanan aşırı iddia veya uydurma ifadelerin bulunmaması
- Kaynak ve çıktının bütün sayısal parçalarının aynı kalması
- Test edilen sürüm ile paket sürümünün eşleşmesi

## Sınırlılıklar

1. Vakaları ve ilk çıktıları aynı geliştirme süreci üretti; bu nedenle test bağımsız değildir.
2. Anahtar sözcük ve sayı denetimi bütün anlam kaymalarını yakalayamaz.
3. Sentetik örnekler, gerçek bir makaledeki uzun mesafeli bölüm tutarsızlıklarını tam olarak temsil etmez.
4. Alan terminolojisi, dergiye özgü biçim ve disiplinler arası farklılıklar ayrıca sınanmalıdır.
5. EQUATOR eşleştirmesi yalnızca kontrollü bir sağlık araştırması örneğinde sınandı; özel uzantıların güncelliği gönderim sırasında doğrulanmalıdır.

## Sonraki güven düzeyi

Bu sürüm temel davranışlar için kullanılabilir bir duman testini geçmiştir. Daha güçlü doğrulama için aynı vakalar, beklenen çıktılar gösterilmeden yeni bir oturumda veya bağımsız değerlendiricide çalıştırılmalı; ardından gerçek bir makaleden en az bir başlık–özet–yöntem–bulgular zinciriyle bölüm tutarlılığı sınanmalıdır.
