# DOI doğrulama katmanı

Bu katmanı kullanıcı DOI, kaynakça, bibliyografik doğrulama, geri çekme veya düzeltme kontrolü istediğinde kullan. Sıradan metin düzenlemede ağ isteği yapma.

## Amaç

DOI'yi yalnızca biçimsel olarak korumakla yetinme. Aşağıdaki ayrı soruları yanıtla:

1. DOI sözdizimsel olarak ayıklanabiliyor mu?
2. `https://doi.org/<DOI>` çözümleme hizmeti yanıt veriyor mu?
3. Crossref kaydındaki başlık, yazar ve yıl kaynakçadaki bilgilerle uyuşuyor mu?
4. Crossref `update-to` veya `updated-by` alanlarında düzeltme, endişe ifadesi, geri çekme ya da başka bir güncelleme var mı?
5. Otomatik kontrolün kapsamadığı veya belirsiz bıraktığı bir alan var mı?

## Çalıştırma

Skill klasöründe şu betik bulunur:

```bash
python3 scripts/verify_dois.py kaynakca.bib --output doi-dogrulama
python3 scripts/verify_dois.py kaynakca.docx --output doi-dogrulama
python3 scripts/verify_dois.py --doi 10.1000/ornek --output doi-dogrulama
```

Desteklenen girdiler: `txt`, `md`, `bib`, `ris`, `json`, `csv`, `tsv` ve `docx`. PDF kaynakça için önce metni güvenilir biçimde çıkar; taranmış PDF'de OCR hatalarını DOI hatası sanma.

Betik kaynak dosyayı değiştirmez. Şu çıktıları üretir:

- `doi-dogrulama-raporu.xlsx`
- `doi-dogrulama-raporu.md`
- `doi-dogrulama-sonuclari.json`

## Durumların anlamı

- `DOGRULANDI`: DOI çözümlendi ve girdide bulunan başlık/yazar/yıl alanları Crossref kaydıyla eşleşti.
- `GECERLI_DOI_METADATA_INCELENMELI`: DOI çözümlendi ancak karşılaştırma için yeterli yerel bibliyografik alan yoktu.
- `GECERLI_DOI_CROSSREF_DISI_INCELENMELI`: DOI çözümlendi ancak Crossref kaydı bulunamadı. Başka bir kayıt ajansı ve yayıncı metadata sayfası elle incelenmelidir.
- `UYUSMAZLIK`: Sağlanan alanlardan en az biri Crossref kaydıyla uyuşmadı. Asıl kaynağı incelemeden düzeltme yapma.
- `GUNCELLEME_UYARISI`: Düzeltme, endişe ifadesi veya başka bir güncelleme kaydı bulundu.
- `GERI_CEKME_UYARISI`: Geri çekme/yayından kaldırma bildirimi bulundu. Bildirimin kendisini ve yayıncı sayfasını incele.
- `COZUMLENEMEDI`: DOI çözümleyici kaydı bulamadı. Yazım hatasını ve asıl kaynak sayfasını incele.
- `KONTROL_EDILEMEDI`: Ağ/servis hatası ya da işlenemeyen yanıt. Bunu DOI geçersizliği gibi sunma.

## Karar kuralları

- DOI'yi, başlığı, yazarı veya yılı kullanıcı onayı olmadan kaynakçada değiştirme.
- Başlık benzerliği otomatik bir ön kontroldür; çeviri başlık, özel karakter ve metadata hatası olasılığında asıl kaynağı aç.
- Yalnızca DOI'nin yönlendirme yapması, kaynakçadaki kaydın doğru olduğunu kanıtlamaz.
- `p`, cilt, sayı ve sayfa bilgilerini Crossref'te yoksa uydurma.
- Aynı DOI yineleniyorsa tek metadata sorgusu yap; kaynakçadaki yinelenen konumları ayrıca raporla.
- Geri çekme/düzeltme uyarısı varsa kullanıcının metnini sessizce silme veya yeniden yazma; kayıt ve etkilenebilecek iddiayı görünür kıl.
- “Uyarı bulunmadı” ifadesini “yayında sorun yoktur” biçiminde kesinleştirme. Crossref, yayıncı ve Retraction Watch kapsamı eksik olabilir.

## Kaynaklar ve kapsam

- DOI Foundation, DOI Handbook: HTTPS çözümleme ve içerik uzlaşması. https://www.doi.org/doi-handbook/html/
- Crossref REST API: DOI metadata, yayın sonrası güncellemeler ve kayıt alanları. https://www.crossref.org/documentation/retrieve-metadata/rest-api
- Crossref Retraction Watch: geri çekmeler `update-to` alanında, kaynak `publisher` veya `retraction-watch` olarak görülebilir. https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/

Crossref, Retraction Watch geri çekmelerini üretim API'sine dâhil eder. Düzeltme ve endişe ifadesi kayıtları geri çekmeler kadar kapsamlı değildir. Son kaynak kontrol tarihi: 1 Kasım 2026.
