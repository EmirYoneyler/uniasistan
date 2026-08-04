# UniAsistan

İstanbul Aydın Üniversitesi yönetmelikleri üzerinde çalışan, **kaynak gösteren** Türkçe soru-cevap asistanı. Öğrencilerin "stajım kaç gün", "bütünlemeye kim girebilir", "AA kaç puan" gibi sorularına yönetmeliğin ilgili maddesine atıf vererek cevap verir.

> 🚧 Geliştirme aşamasında. Şu an ingestion katmanı çalışıyor; retrieval ve arayüz geliyor.

---

## Neden

Yönetmelik 16 sayfa, 48 madde ve kimse okumuyor. Öğrenciler aynı soruları WhatsApp gruplarında birbirine soruyor, çoğu zaman yanlış cevap alıyor. Amaç: doğru cevabı, **hangi maddeye dayandığını göstererek** vermek.

## Mimari

```
PDF ──► extract.py ──► chunk.py ──► embedding ──► Postgres (pgvector + tsvector)
                                                          │
                    soru ──► hibrit arama ──► rerank ──► LLM ──► kaynaklı cevap
```

| Katman | Seçim |
|---|---|
| Backend | FastAPI |
| Veritabanı | Supabase (Postgres + pgvector) |
| Embedding | BGE-M3 |
| Rerank | Cohere Rerank v3.5 |
| Arayüz | Next.js |

## Türkçe mevzuata özgü çözümler

Bu projenin asıl işi metni doğru parçalamak. Karşılaştığım problemler:

**Yapıya duyarlı bölümleme.** Sabit boyutlu chunking yönetmelikte bir maddenin ortasından keser ve cevap yarım kalır. Bunun yerine her `MADDE` bir chunk; bölüm başlığı (`DÖRDÜNCÜ BÖLÜM – Sınav, Değerlendirme ve Not Sistemi`) ve madde başlığı (`Mazeret sınavı`) metadata olarak taşınıp embedding metnine ekleniyor. Madde başlığı kritik: öğrenci "mazeret sınavı" diye arıyor ama bu ifade madde gövdesinde hiç geçmiyor olabilir.

**Çok harfli bentler.** Tanımlar maddesi `a)`'dan `z)`'ye gidip `aa)`, `bb)`, `çç)`, `ee)` diye devam ediyor. Tek harf varsayan regex bu satırları önceki paragrafa yapıştırıyordu.

**İki aşamalı bölme.** Çok uzun maddeler önce fıkra (`(1)`, `(2)`) sınırından bölünüyor; hâlâ 2500 karakteri aşan parçalar bent sınırından tekrar bölünüyor. Her parçada madde girişi tekrarlanıyor, yoksa `b) AKTS: ...` tek başına bağlamsız kalıyor.

**Türkçe sondan eklemeli.** "stajın", "staja", "stajını" BM25 için farklı token. Postgres'in `to_tsvector('turkish', ...)` snowball yapılandırması kök buluyor. Hibrit arama, `AA` veya `MADDE 23` gibi tam eşleşme gerektiren sorgularda dense aramanın ıskaladığı yerleri yakalıyor.

**Halüsinasyon riski.** Yönetmelik konusunda uydurma cevap öğrencinin ders kaydını kaçırmasına yol açar. Model, verilen maddeler yetersizse "bilgi bulamadım" demek zorunda; her cevaba kaynak maddesi ve "kesin bilgi için öğrenci işlerine danışın" uyarısı ekleniyor.

## Mevcut durum

```
58 chunk / 1 yönetmelik
başlığı bulunamayan : 0
bölümü bulunamayan  : 0
şüpheli uzun (>3000): 0
```

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Yönetmelikleri `data/raw/` içine indir (kaynak: [mevzuat.gov.tr](https://mevzuat.gov.tr/MevzuatMetin/yonetmelik/8.5.40234.pdf)), sonra:

```bash
python kontrol.py       # PDF'lerden metin çıkıyor mu kontrol et
python extract.py       # PDF -> temiz metin
python test_chunk.py    # chunk'ları gözle kontrol et
```

## Yol haritası

- [x] PDF çıkarma ve temizleme
- [x] MADDE bazlı, yapıya duyarlı chunking
- [ ] Altın küme (50 gerçek öğrenci sorusu) + eval betiği
- [ ] Embedding + pgvector
- [ ] Hibrit arama + rerank
- [ ] FastAPI `/ask` endpoint'i
- [ ] Next.js sohbet arayüzü
- [ ] Deploy

## Uyarı

Bu bir öğrenci projesidir, resmî bir kaynak değildir. Yönetmelikler değişir (bu metin en son 25/10/2025'te değişti). Kesin bilgi için öğrenci işlerine danışın.
