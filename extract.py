"""
PDF -> temiz metin.

Kullanım:
    python extract.py

data/raw/*.pdf dosyalarını okur, data/processed/*.txt olarak yazar.
"""

import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

RAW = Path("data/raw")
OUT = Path("data/processed")


def pdf_to_text(pdf_yolu: Path) -> str:
    parcalar = []
    with pdfplumber.open(pdf_yolu) as pdf:
        for sayfa in pdf.pages:
            metin = sayfa.extract_text() or ""
            parcalar.append(metin)
    return "\n".join(parcalar)


def temizle(text: str) -> str:
    satirlar = []
    for s in text.split("\n"):
        s = s.replace("\xa0", " ").rstrip()
        # Resmî Gazete PDF'lerindeki sayfa altı/üstü gürültüsü
        if s.strip().startswith("Başbakanlık Mevzuatı Geliştirme"):
            continue
        if s.strip().isdigit() and len(s.strip()) <= 3:  # sayfa numarası
            continue
        satirlar.append(s)
    return "\n".join(satirlar)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pdfler = sorted(RAW.glob("*.pdf"))

    if not pdfler:
        print(f"{RAW.resolve()} içinde PDF yok.")
        return

    for pdf in pdfler:
        metin = temizle(pdf_to_text(pdf))
        hedef = OUT / (pdf.stem + ".txt")
        hedef.write_text(metin, encoding="utf-8")
        print(f"{pdf.name:<50} -> {hedef.name}  ({len(metin):,} karakter)")

    print(f"\n{len(pdfler)} dosya işlendi. Çıktılar: {OUT.resolve()}")
    print("Şimdi data/processed/ içindeki bir .txt dosyasını açıp gözle kontrol et.")


if __name__ == "__main__":
    main()
