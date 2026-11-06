# Türkçe üslup denetimi ve metin koruma protokolü

## Kullanım amacı

Bu kılavuz, `write` (sıfırdan yaz), `rewrite` (mevcut metni düzenle) ve `audit` (metni değiştirmeden denetle) davranışlarını açıkça ayırır. Üçü de metnin türüne ve hedef okura bağlıdır. `audit` modunda metni yeniden yazma; bulguyu, gerekçeyi, önemini ve bağlama uygun öneriyi ver.

## Üslup profilleri (register)

| Profil | Öncelik | Dikkat edilmesi gerekenler |
| --- | --- | --- |
| `academic` | Kanıt ve terim sadakati, bölüm işlevi, nesnel anlatım | Teknik terimleri ve gerekli edilgeni koru; `-maktadır`, `bununla birlikte`, `söz konusu` gibi ifadeleri sırf görülüyor diye yasaklama. |
| `institutional` | Açık sorumluluk, kısa işlem bildirimi, resmiyet | Gereksiz bürokratik dolgu ve belirsiz özneyi açıklaştır; kurum adı, birim, karar ve tarihleri koru. |
| `technical` | İşlemin yeniden uygulanabilirliği, kesin terim, tutarlılık | Komutları, kodu, kısaltmaları ve yerleşik alan terimlerini koru; hatalı çeviriden kaçın. |
| `general` | Ana düşüncenin açıklığı, doğal ritim, okur dostu örnek | Klişe giriş ve kapanışları incele, ancak yeni duygu, sahne, kişi veya anekdot uydurma. |

Profil, sert kelime yasaklarına gerekçe değildir. Metin türünün gerektirdiği ifade, yalnızca istatistiksel bir sıklık hesabıyla değiştirilemez.

## Denetim akışı

1. Tür, hedef okur, amaç ve bağlamı belirle. Kimin neyi iddia ettiğini ve hangi verilerle desteklediğini çıkar.
2. Kaynak metinde sayıları, istatistikleri, birimleri, karşılaştırma yönünü, atıf bağlarını, belirsizliği ve kapsamı koruma öğesi olarak kaydet.
3. İsteğe bağlı olarak `python3 scripts/audit_turkish.py metin.md --register academic` çalıştır. Betik metni değiştirmez; satır, sütun, kural kodu ve gerekçeli inceleme önerisi döndürür.
4. Yalnızca açık imla sorunlarını doğrudan düzelt; üslup uyarılarını bağlam içinde değerlendir. Tek kelime veya bağlaçtan yapay zekâ yazarlığı çıkarımı yapma.
5. Düzenlemede anlamı, bilimsel kesinliği ve karşılaştırma kapsamını koru. Bir cümleyi kısaltmak bir sonucu, koşulu ya da sınırlılığı silmek anlamına geliyorsa kısaltma.
6. Metin düzenlendiğinde `python3 scripts/audit_turkish.py kaynak.md --compare duzeltilmis.md --json` ile sayı ve DOI farklarını ön kontrolden geçir. Uyuşmazlık varsa kaynakla kontrol et. Eşleşen sayılar da anlamı koruduğunu kanıtlamaz.
7. `audit` çıktısında önem düzeyini ayır: **düzelt** (açık yazım hatası), **incele** (bağlama bağlı ifade), **doğrula** (kanıt, anlam, kaynak veya bilgi eksikliği).

## Ölçümün sınırları

- Betik kural tabanlı bir metin tarayıcısıdır; bir AI dedektörü, TDK'nin eksiksiz dijital kılavuzu veya anlamsal doğruluk kanıtı değildir.
- `-maktadır` oranı, kelime sayısı, kalıp sıklığı ve cümle ritmi yazarın insan mı model mi olduğunu göstermez; sabit bir "insan yazımı eşiği" yoktur.
- Regex eşleşmeleri yanlış pozitif üretebilir. Hedef dergi biçemini, istatistiksel gösterimi, doğrudan alıntıları veya teknik komutları izinsiz değiştirme.
- `--compare` sayısal ve DOI belirteçlerinin varlığını karşılaştırır. "Süre %38 arttı" ile "hız %38 arttı" aynı sayıyı içerir ama aynı bilimsel iddiayı taşımaz.
- Bir ifade yalnızca "AI izini silmek" için yeniden kurulmaz. Editoryal gerekçe açıklık, anlamsal sadakat, hedef okur veya somut yazım kuralı olmalıdır.

## Komutlar

```bash
python3 scripts/audit_turkish.py makale.md --register academic
python3 scripts/audit_turkish.py duyuru.md --register institutional --json
python3 scripts/audit_turkish.py makale.md --compare duzeltilmis.md --json
```

Komutlar skill klasörünün (`skills/turkish-clear-writing`) içinden çalıştırılır. Otomatik regresyon testleri repo kökünden `python3 scripts/check_style_audit.py` ile yürütülür.
