"""
Chunk'ları gözle kontrol etme betiği.

Kullanım:
    python test_chunk.py                        # özet tablo
    python test_chunk.py 22                     # MADDE 22'yi tam göster
"""

import sys
from pathlib import Path

from chunk import chunk_yonetmelik, embed_text

sys.stdout.reconfigure(encoding="utf-8")

PROC = Path("data/processed")


def yukle():
    tum = []
    for txt in sorted(PROC.glob("*.txt")):
        metin = txt.read_text(encoding="utf-8")
        tum += chunk_yonetmelik(metin, kaynak=txt.stem, url=f"local://{txt.name}")
    return tum


def main():
    if not PROC.exists():
        print("Önce `python extract.py` çalıştır.")
        return

    chunks = yukle()
    if not chunks:
        print("Hiç chunk üretilmedi. data/processed/ boş olabilir.")
        return

    # Belirli bir maddeyi tam göster
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        no = int(sys.argv[1])
        for c in chunks:
            if c["madde_no"] == no:
                print("=" * 70)
                print(embed_text(c))
                print()
        return

    # Özet tablo
    print(f"\nToplam {len(chunks)} chunk\n")
    print(f"{'MADDE':>6}  {'PARÇA':>6}  {'UZUNLUK':>8}  BAŞLIK")
    print("-" * 70)
    for c in chunks:
        parca = f"{c['parca']}/{c['parca_toplam']}"
        print(f"{c['madde_no']:>6}  {parca:>6}  {len(c['text']):>8}  {c['baslik']}")

    # Sağlık kontrolleri
    print("\n--- Sağlık kontrolü ---")
    bassiz = [c for c in chunks if not c["baslik"]]
    bolumsuz = [c for c in chunks if not c["bolum"]]
    kisa = [c for c in chunks if len(c["text"]) < 80]
    uzun = [c for c in chunks if len(c["text"]) > 3000]

    print(f"başlığı bulunamayan : {len(bassiz)}")
    print(f"bölümü bulunamayan  : {len(bolumsuz)}")
    print(f"şüpheli kısa (<80)  : {len(kisa)} {[c['madde_no'] for c in kisa][:10]}")
    print(f"şüpheli uzun (>3000): {len(uzun)} {[c['madde_no'] for c in uzun][:10]}")

    if bassiz or kisa or uzun:
        print("\nBu maddeleri tek tek incele:  python test_chunk.py <madde_no>")
    else:
        print("\nHer şey temiz görünüyor.")


if __name__ == "__main__":
    main()
