"""Yönetmelik metnini MADDE bazlı chunk'lara böler."""
import re

MADDE_RE = re.compile(r"^[ \t]*MADDE\s+(\d+)\s*[-–—]", re.MULTILINE)
BOLUM_RE = re.compile(
    r"^[ \t]*([A-ZÇĞİÖŞÜ]+)[ \t]+BÖLÜM[ \t]*\n+[ \t]*(.+?)[ \t]*\n", re.MULTILINE)
FIKRA_RE = re.compile(r"^\((\d+)\)", re.MULTILINE)

MAX_CHUNK = 2500  # karakter; bundan uzun maddeler fıkralara bölünür


BOLUM_MARK_RE = re.compile(r"^[A-ZÇĞİÖŞÜ]+\s+BÖLÜM\s*$")
YENI_BLOK_RE = re.compile(r"^\s*(\(\d+\)|[a-zçğıöşü]{1,2}\)|MADDE\s+\d)")


def satirlari_birlestir(text: str) -> str:
    """PDF'in satır ortasından kestiği cümleleri birleştirir.

    Başlık satırlarını (BÖLÜM işareti, bölüm adı, madde başlığı) ayrı tutar;
    aksi hâlde 'Amaç' gibi başlıklar bir önceki paragrafın sonuna yapışır.
    """
    ham = [s.strip() for s in text.split("\n")]
    out = []
    for i, s in enumerate(ham):
        if not s:
            out.append("")
            continue

        onceki_ham = ham[i - 1] if i > 0 else ""
        sonraki_ham = next((x for x in ham[i + 1:] if x), "")

        basli_satir = (
            YENI_BLOK_RE.match(s)                     # (1), a), MADDE 5-
            or BOLUM_MARK_RE.match(s)                 # "İKİNCİ BÖLÜM"
            or BOLUM_MARK_RE.match(onceki_ham)        # bölüm adı satırı
            or MADDE_RE.match(sonraki_ham)            # madde başlığı ("Amaç")
        )

        if out and out[-1] and not basli_satir:
            out[-1] = out[-1].rstrip() + " " + s
        else:
            out.append(s)
    return "\n".join(out)


def _madde_basligi(text: str, madde_start: int):
    onceki = text[:madde_start].rstrip("\n")
    if not onceki:
        return None
    son = onceki.split("\n")[-1].strip()
    if 0 < len(son) <= 80 and not son.endswith((".", ":", ";")):
        return son
    return None


BENT_RE = re.compile(r"^\s*([a-zçğıöşü]{1,2})\)", re.MULTILINE)


def _parcala(govde: str, bolucu, max_len: int):
    """Verilen sınır regex'ine göre gövdeyi max_len'i aşmayan parçalara böler."""
    pozlar = [m.start() for m in bolucu.finditer(govde)]
    if len(pozlar) < 2:
        return None
    bas = govde[: pozlar[0]].strip()
    parcalar, tampon = [], bas
    for i, p in enumerate(pozlar):
        son = pozlar[i + 1] if i + 1 < len(pozlar) else len(govde)
        birim = govde[p:son].strip()
        if tampon and len(tampon) + len(birim) > max_len:
            parcalar.append(tampon.strip())
            tampon = bas + "\n" + birim   # başlık her parçada tekrarlansın
        else:
            tampon = (tampon + "\n" + birim).strip()
    if tampon.strip():
        parcalar.append(tampon.strip())
    return parcalar


def _fikralara_bol(govde: str, max_len: int):
    """Uzun maddeyi fıkra sınırından böler; hâlâ uzun kalan parçaları bent
    sınırından tekrar böler. Fıkra bölünmesi her zaman önceliklidir."""
    if len(govde) <= max_len:
        return [govde]

    parcalar = _parcala(govde, FIKRA_RE, max_len) or [govde]

    sonuc = []
    for p in parcalar:
        if len(p) > max_len:
            alt = _parcala(p, BENT_RE, max_len)
            sonuc.extend(alt if alt else [p])
        else:
            sonuc.append(p)
    return sonuc


def chunk_yonetmelik(text: str, kaynak: str, url: str, max_len: int = MAX_CHUNK):
    text = satirlari_birlestir(text)
    bolumler = [(m.start(), m.end(), f"{m.group(1)} BÖLÜM – {m.group(2)}")
                for m in BOLUM_RE.finditer(text)]
    matches = list(MADDE_RE.finditer(text))
    chunks = []

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        baslik = _madde_basligi(text, start)

        if i + 1 < len(matches):
            sb = _madde_basligi(text, matches[i + 1].start())
            if sb:
                try:
                    end = text.rindex(sb, start, end)
                except ValueError:
                    pass
        for bs, be, _ in bolumler:
            if start < bs < end:
                end = bs
                break

        bolum = None
        for bs, be, ad in bolumler:
            if be <= start:
                bolum = ad

        govde = text[start:end].strip()
        parcalar = _fikralara_bol(govde, max_len)
        for j, p in enumerate(parcalar):
            no = int(m.group(1))
            chunks.append({
                "chunk_id": f"{kaynak}#m{no}p{j + 1}",
                "text": p, "madde_no": no, "parca": j + 1,
                "parca_toplam": len(parcalar), "baslik": baslik,
                "bolum": bolum, "kaynak": kaynak, "url": url,
            })
    return chunks


def embed_text(c: dict) -> str:
    ust = " › ".join(x for x in (c["kaynak"], c["bolum"], c["baslik"]) if x)
    ek = f" (parça {c['parca']}/{c['parca_toplam']})" if c["parca_toplam"] > 1 else ""
    return f"{ust}{ek}\n\n{c['text']}"
