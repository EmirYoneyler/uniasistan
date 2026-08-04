"""
PDF çıkarılabilirlik kontrolü.

Kullanım:
    python kontrol.py                 # ./data/raw klasörünü tarar
    python kontrol.py C:\\yol\\klasor  # başka klasör

Her PDF için üç ihtimalden birini söyler:
  OK        -> metin düzgün çıkıyor, doğrudan kullanabilirsin
  KODLAMA   -> metin çıkıyor ama Türkçe karakterler bozuk
  OCR       -> metin çıkmıyor, taranmış görüntü
"""

import sys
import re
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

# Bozuk kodlamanın tipik izleri: Türkçe karakterler yerine gelen yanlış harfler
BOZUK_IZ = re.compile(r"[ÝÞðþÐ\ufffd]")
# Sağlıklı bir Türkçe metinde bunlardan en az birkaçı bulunmalı
TR_HARF = re.compile(r"[çğıöşüÇĞİÖŞÜ]")


def kontrol_et(pdf_yolu: Path, ornek_sayfa: int = 3) -> dict:
    sonuc = {
        "dosya": pdf_yolu.name,
        "sayfa": 0,
        "karakter": 0,
        "tr_harf": 0,
        "durum": "?",
        "ornek": "",
    }

    try:
        with pdfplumber.open(pdf_yolu) as pdf:
            sonuc["sayfa"] = len(pdf.pages)
            parcalar = []
            for sayfa in pdf.pages[:ornek_sayfa]:
                metin = sayfa.extract_text() or ""
                parcalar.append(metin)
            metin = "\n".join(parcalar)
    except Exception as e:
        sonuc["durum"] = "HATA"
        sonuc["ornek"] = f"{type(e).__name__}: {e}"
        return sonuc

    sonuc["karakter"] = len(metin.strip())
    sonuc["tr_harf"] = len(TR_HARF.findall(metin))
    sonuc["ornek"] = " ".join(metin.split())[:90]

    # Karar mantığı
    if sonuc["karakter"] < 100:
        # Sayfa başına neredeyse hiç metin yok -> taranmış görüntü
        sonuc["durum"] = "OCR"
    elif BOZUK_IZ.search(metin) or sonuc["tr_harf"] < 5:
        # Metin var ama Türkçe karakterler kayıp/bozuk
        sonuc["durum"] = "KODLAMA"
    else:
        sonuc["durum"] = "OK"

    return sonuc


def main():
    klasor = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")

    if not klasor.is_dir():
        print(f"Klasör bulunamadı: {klasor.resolve()}")
        print("PDF'leri data/raw/ içine koy ya da klasör yolunu argüman olarak ver.")
        sys.exit(1)

    pdfler = sorted(klasor.rglob("*.pdf"))
    if not pdfler:
        print(f"{klasor.resolve()} içinde PDF yok.")
        sys.exit(1)

    print(f"\n{len(pdfler)} PDF taranıyor: {klasor.resolve()}\n")

    sonuclar = [kontrol_et(p) for p in pdfler]

    ad_gen = max(len(s["dosya"]) for s in sonuclar)
    ad_gen = min(max(ad_gen, 8), 45)

    print(f"{'DURUM':<8} {'DOSYA':<{ad_gen}} {'SAYFA':>6} {'KARAKTER':>9}  ÖRNEK")
    print("-" * (8 + ad_gen + 6 + 9 + 40))
    for s in sonuclar:
        ad = s["dosya"] if len(s["dosya"]) <= ad_gen else s["dosya"][: ad_gen - 3] + "..."
        print(
            f"{s['durum']:<8} {ad:<{ad_gen}} {s['sayfa']:>6} "
            f"{s['karakter']:>9}  {s['ornek'][:60]}"
        )

    # Özet
    print()
    for durum in ("OK", "KODLAMA", "OCR", "HATA"):
        adet = sum(1 for s in sonuclar if s["durum"] == durum)
        if adet:
            print(f"  {durum:<8} {adet} dosya")

    ocr_var = any(s["durum"] == "OCR" for s in sonuclar)
    kod_var = any(s["durum"] == "KODLAMA" for s in sonuclar)

    print("\nNe anlama geliyor:")
    if not ocr_var and not kod_var:
        print("  Hepsi temiz. Ingestion'a doğrudan geçebilirsin, plan aynı kalıyor.")
    if kod_var:
        print("  KODLAMA -> `pip install ftfy` ile büyük ölçüde düzelir. ~1 gün ek iş.")
    if ocr_var:
        print("  OCR     -> tesseract + tur dil paketi gerek. Faz 1'e 1 hafta ekle.")
        print("             Önce mevzuat.gov.tr'de HTML karşılığı var mı bak, varsa OCR'a hiç girme.")


if __name__ == "__main__":
    main()
