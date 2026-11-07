---
name: turkish-clear-writing
description: Türkçe akademik ve kurumsal metinleri kanıta sadık biçimde yazar veya düzenler; akademik veri varsa istatistiksel analiz ve yayın kalitesinde bilimsel şekil üretimine de rehberlik eder. Yazım, bilimsel yöntem, analiz ve grafik isteklerinde kullan; yaratıcı edebiyat için kullanma.
metadata:
  version: "0.7.0"
---

# Türkçe Açık Yazım

Metni yalnızca kısaltma. Okurun bilgiyi doğru, akıcı ve gereksiz çıkarım yükü olmadan işlemesini sağla.

## Önce bağlamı belirle

Eksikse metinden makul biçimde çıkar; sonucu kökten değiştirecek bir belirsizlik varsa sor.

- Amaç: bilgilendirme, açıklama, savunma, öğretme veya özetleme
- Okur: alan uzmanı, lisans öğrencisi, genel okur ya da belirli bir kurum
- Tür ve ton: makale, tez, rapor, duyuru, web metni veya günlük anlatım
- Korunacaklar: teknik terimler, iddia sınırları, sayılar, birimler, özel adlar, atıflar ve biçim

Akademik makalede ayrıca hedef derginin yazar rehberini, makale türünü ve varsa çalışma türüne özgü raporlama kılavuzunu belirle. Derginin açık biçim kuralları; genel örneklerden, varsayılan kaynakça biçiminden ve yerelleştirme tercihlerinden önce gelir. Etik kurul/onam, kayıt, yazarlık, finansman, çıkar çatışması, veri erişimi veya önceki yayın ilişkisi söz konusuysa bunları yalnızca üslup unsuru gibi düzenleme; doğrulanması gereken beyanlar olarak koru.

## Çalışma modunu belirle

- **`write` (üretim):** Kaynak veya konuya dayalı sıfırdan metin yaz. Sağlanmayan olguları, araştırma sonuçlarını, örneklem sayılarını veya anekdotları gerçek gibi ekleme.
- **`rewrite` (düzenleme, varsayılan):** Mevcut metni anlamı, veriyi ve iddia gücünü koruyarak iyileştir. Yalnızca sözcük değiştirerek değil, bilgi akışı ve Türkçe söz dizimiyle çalış.
- **`audit` (denetim):** Metni **değiştirme**; açık yazım hatalarını, bağlama bağlı üslup önerilerini ve doğrulanması gereken anlam/kaynak sorunlarını ayrı raporla. Metne yapay zekâ ürünü olduğuna ilişkin kesin etiket koyma.

Metnin profilini (akademik, kurumsal, teknik veya genel) belirle. Alıntı, yöntem anlatımı ve hedef derginin terminolojisi gibi meşru biçem tercihlerini sırf tekrar ediyor diye silme. Ayrıntılar ve isteğe bağlı terminal denetimi için [references/style-audit.md](references/style-audit.md) dosyasını kullan.

## Düzenleme akışı

1. **Koruma dökümü çıkar.** Ana iddiaları; olasılık, sınırlılık ve karşıtlık belirteçlerini; sayıları, birimleri ve atıfları listele.
2. **Karşılaştırma kapsamını denetle.** Karşılaştırmalı bir metinde amaç veya yöntemde tanıtılan her grup, kaynak, yöntem, doz ya da koşulun temel bulgularda temsil edilip edilmediğini kontrol et. Bir kol eksikse onu sessizce düşürme; “etkisizdi” veya “anlamlı fark yoktu” diye varsayma. Sonuç uydurmadan hangi temel bulgunun doğrulanması gerektiğini işaretle.
3. **Bilgi akışını kur.** Her paragrafta bilinen bilgiden yeni bilgiye ilerle; ana düşünceyi geciktirme; bir paragrafın işlevini tek cümleyle adlandırabil.
4. **Türkçeleştir.** İngilizce söz dizimini taklit eden yapıları çöz; yüklemi doğal konuma getir; gereksiz edilgenliği, aşırı adlaştırmayı ve uzun isim zincirlerini azalt.
5. **Bağları görünür kıl.** Özne veya gönderim belirsizse adı yinele; neden, karşıtlık, koşul ve sonuç ilişkilerini uygun bağlaçlarla açıkla. Bağlaçları mekanik biçimde çoğaltma.
6. **Yoğunluğu ayarla.** Kısaltmayı amaç edinme. Bir cümle çok sayıda yeni kavram veya önermeyi taşıyorsa böl, tanım ya da kısa örnek ekle. Bölme sırasında mantıksal ilişkiyi kaybetme.
7. **Kesinliği koru.** “Gösterir”, “ilişkilidir”, “olabilir”, “öne sürer” ve “kanıtlamaz” aynı güçte değildir. Kaynağın iddia düzeyini yükseltme veya düşürme.
8. **Son doğrulamayı yap.** Düzenlenen metni koruma dökümüyle karşılaştır; sayı, yüzde, tarih, birim, denklem, dipnot, atıf ve etik/şeffaflık beyanlarını tek tek denetle.

## İstatistik ve bilimsel grafik karar adımı

Akademik çalışma, tez, makale veya araştırma raporunda istatistiksel karşılaştırma, yeni şekil ya da sonuçların yeniden hesaplanması **gerekiyorsa** önce [references/statistics-and-figures.md](references/statistics-and-figures.md) dosyasını oku. Hangi deney biriminin bağımsız olduğunu, faktörleri, örneklem yapısını, eksik verileri, hipotezleri ve hedef dergi kuralını değerlendir. Yalnızca doğru veri ve uygun çalışma deseni varsa analiz/şekli **gerçekten üret**; çalıştırılabilir ortamda tek faktörlü bağımsız gruplar için isteğe bağlı `scripts/analyze_and_plot.py` aracını kullanabilirsin. Veri veya uygun tasarım bilgisi yoksa test sonucu, p değeri, anlamlılık harfi ya da grafik uydurma.

Sıradan bir metin düzenlemesinde analiz veya çizim yapma. `audit` modunda mevcut metne müdahale etmeden istatistik/şekil tutarsızlıklarını işaretle. Faktöriyel, bloklu, iç içe, tekrarlı ölçümlü, eşleştirilmiş veya zaman serisi desenlerinde bu tek faktörlü betiği kullanma; gerçek desene uygun model belirle. Raporlanan grafikler için veriye uygun grafik türünü seç, gerekirse yüksek çözünürlüklü PNG ve vektör PDF/SVG olarak çıktı ver. Analiz kararlarını, kullanılan betiği, veri birimini ve belirsizlikleri açıkla.

## Türkçeye özgü kararlar

- **Doğal söz dizimi:** Cümleyi İngilizce sırasına zorlamadan odağı ve yüklemi doğal Türkçe akışında konumlandır. Vurgu gerektirmiyorsa devrikliği sırf çeşitlilik için kullanma.
- **Eklemeli morfoloji:** Uzun sözcüğü tek başına hata sayma. Ancak art arda gelen yapım ve çekim ekleri görevleri belirsizleştiriyorsa sözcüğü bir yan cümle veya ayrı ifadeyle aç.
- **İsim zincirleri:** Üç ya da daha fazla ad/isimleşmiş öğe üst üste geldiğinde tamlayan–tamlanan ilişkisini denetle. Gerekirse fiilleştir, “-e ilişkin/-de kullanılan” gibi açık bir ilişki kur veya iki cümleye böl.
- **Özne ve gönderim:** Türkçede özne düşebilir; fakat iki olası gönderge varsa özneyi yaz. “Bu/bu durum/bunlar/söz konusu” ifadelerinin neye gönderdiğini açıklaştır.
- **Bağdaşıklık:** Ana terimi sırf tekrar olmasın diye her cümlede başka eş anlamlıyla değiştirme. Anahtar kavramı tutarlı biçimde yinele; ilişkileri doğru bağlaçla kur.
- **Bilgi yoğunluğu:** Cümle uzunluğuna tek başına hüküm verme. Yeni kavram, önerme, koşul ve iç içe yan cümle sayısını birlikte değerlendir.
- **Tanımlama ve örnekleme:** Okurun bilmeyebileceği terimi ilk kullanımda kısa biçimde tanımla. Soyut bir ilişkiyi açıklamak gerekiyorsa bir temsilî örnek ver ve örneği bulgu gibi sunma.

Üslup denetimi veya metni değiştirmeden inceleme istendiğinde [references/style-audit.md](references/style-audit.md) dosyasını oku; komut satırı erişimi varsa `scripts/audit_turkish.py` ile açıklanabilir bir ön tarama yap. Bu betik insan/yapay zekâ yazarlığını belirlemez ve akademik kanıt doğrulamasının yerini almaz. Normal metin düzenleme isteklerinde betiğin çalıştırılması zorunlu değildir.

Ayrıntılı tanı–eylem–kontrol yönergeleri için [references/turkish-guidelines.md](references/turkish-guidelines.md) dosyasını oku. Yazım, noktalama, sayı, özel ad veya alıntı biçimi denetiminde [references/tdk-writing-and-punctuation.md](references/tdk-writing-and-punctuation.md) dosyasını kullan. Akademik makale planlama ya da bölüm düzenleme işinde [references/academic-article-workflow.md](references/academic-article-workflow.md) dosyasını oku. Etik, yazarlık, izin/onam, şeffaflık, TR Dizin veya çalışma türüne özgü raporlama denetiminde [references/research-ethics-and-reporting.md](references/research-ethics-and-reporting.md) dosyasını kullan. DOI, kaynakça, geri çekme veya düzeltme kontrolü istenirse [references/doi-verification.md](references/doi-verification.md) dosyasını oku ve `scripts/verify_dois.py` aracını kullan; sıradan metin düzenlemede çevrimiçi sorgu çalıştırma ve kaynakçayı otomatik değiştirme. Akademik veya yüksek riskli düzenlemede [references/evidence-and-limitations.md](references/evidence-and-limitations.md) dosyasındaki kanıt sınırlarını da uygula. Örnek istenirse [references/examples.md](references/examples.md) dosyasını kullan. Değerlendirme veya kalite puanı istenirse [references/evaluation.md](references/evaluation.md) dosyasını oku.

## Değiştirilmemesi gerekenler

- Yeni olgu, kaynak, yöntem, sonuç veya atıf uydurma.
- Korelasyonu nedenselliğe; olasılığı kesinliğe; yazar yorumunu veri sonucuna dönüştürme.
- Sayıları yuvarlama, birimleri dönüştürme veya atıf yerini değiştirme; kullanıcı açıkça istemedikçe kaynak biçemini yeniden düzenleme.
- Dergi şablonundaki ondalık ayırıcı, kaynakça, tablo, denklem veya birim biçimini yalnızca genel Türkçe yazım tercihine uydurmak için değiştirme.
- Eksik etik kurul/onam, kayıt, yazarlık katkısı, finansman veya çıkar çatışması bilgisini tahmin ederek doldurma; eksikliği görünür biçimde işaretle.
- Bir raporlama kontrol listesini iyi araştırma tasarımının, etik onayın veya alan uzmanı değerlendirmesinin yerine koyma.
- Teknik terimi sırf daha gündelik görünsün diye anlamca daraltma ya da genişletme. Gerekirse terimi koruyup kısa tanım ekle.
- Türkçeye özgü yönergeleri beş İngilizce çalışmanın doğrudan bulgusu gibi sunma.

## Değişiklik sonrası anlam kontrolü

- Kaynak ve son metnin sayıları, birimleri, istatistikleri, DOI'leri, atıfları, kapsamı, yönü ve kesinlik düzeyini karşılaştır. Araştırma sonuçlarını veya nedenselliği sessizce değiştirme.
- İstenirse `scripts/audit_turkish.py kaynak.md --compare duzeltilmis.md --json` ile **yalnızca** sayı ve DOI belirteçlerini otomatik ön kontrolden geçir. Sayıların eşit olması eşdeğer anlam kanıtı değildir.
- Her kalıplaşmış bağlacı “AI ifşası” sayma; akademik anlatımda bağlaçlar, edilgen çatı ve `-maktadır` işlevsel olabilir. Kelime sayısı, cümle ritmi veya sabit “insan eşiği” ile yazarlık kararı verme.

## Sonucu sun

`audit` modunda özgün metni yeniden yazma; bulguları konum, gerekçe ve önceliğiyle raporla. `write` ve `rewrite` modlarında kullanıcının istediği metni önce ver. Önemli anlam değişiklikleri, çözülemeyen belirsizlikler veya olası kaynak hataları varsa ardından kısa not düş. İzleme istenirse yalnızca anlamı etkileyen değişiklikleri açıkla; her küçük üslup düzeltmesini listeleme.
