# Değerlendirme ve küçük test protokolü

## 10 puanlık denetim

Her maddeye 0 (başarısız), 1 (kısmen), 2 (başarılı) ver.

1. **Anlam ve kanıt:** Ana iddialar, koşullar ve sınırlılıklar korunmuş mu?
2. **Sayı ve kaynak:** Sayılar, birimler, tarihler ve atıflar doğru yerde ve eksiksiz mi?
3. **Doğal Türkçe:** Söz dizimi, ek kullanımı ve tamlamalar Türkçede doğal mı?
4. **Bağdaşıklık:** Özneler, gönderimler ve mantıksal ilişkiler açık mı?
5. **Okur uyumu:** Terimler gerektiği kadar tanımlanmış; bilgi yoğunluğu hedef okura uygun mu?

Herhangi bir sayı/atıf kaybı veya iddia gücü değişikliği varsa toplam puandan bağımsız olarak metni başarısız say ve düzelt.

## Davranış testi

Bir düzenleme örneğini şu sırayla dene:

1. Kaynak metinden korunacak öğeleri ayrı listele.
2. Metni skill ile düzenle.
3. Okunabilirlik puanına bakmadan önce listedeki öğeleri karşılaştır.
4. Bir okura metni ver ve “Ana sonuç nedir?”, “Bu sonuç kesin mi?”, “Hangi sayı sonucu sınırlar?” gibi sorular sor.
5. Yanıtlar kaynak metinle uyuşmuyorsa daha kısa yazmak yerine kayıp ilişkiyi geri ekle.

## Otomatik örnek testi

Paket kökünde `python3 scripts/check_examples.py` çalıştır. Test, örnek düzenlemelerde korunması gereken sayı, atıf ve kesinlik işaretlerinin kaybolmadığını denetler. Bu test doğal Türkçe kalitesini veya gerçek okur anlamasını kanıtlamaz; yalnızca temel koruma hatalarını yakalar.
