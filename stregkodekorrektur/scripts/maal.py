#!/usr/bin/env python3
"""Mål stregkoderne i et emballagedesign og tjek dem mod GS1.

Dekoderen (zxing) finder koderne og læser numrene. Alt i mm måles direkte på
stregerne i en gengivelse ved 1200 dpi: modulbredde (X), højde, guard bars,
lyszoner, afstand til cifrene, kontrast i rødt lys, afstand til etikettens kant
og linjer der krydser koden. Målestokken antages at være 1:1 (sådan eksporterer
InDesign og Illustrator). Oplyses etikettens format med --format, efterprøves
målestokken mod en ramme med de mål på siden.

Offentlig udgave: kun GS1-laget. Kundepraksis og et bureaus egne skabeloner er
taget ud. Vises som arbejdsprøve. Alle rettigheder forbeholdes.

Brug:
    python maal.py design.pdf --ud mappe [--gtin 2000000000015] [--diameter 73] [--format 100x60]
    python maal.py skaermbillede.png --ud mappe --dpi 300

Skriver i mappen:
    maaling.json        alle mål og tjek
    oversigt_s<N>.png   siden med koder, etiketkant og krydsende linjer markeret
    kode_<N>.png        koden drejet med stregerne lodret, mål tegnet ind
    kode_<N>_raa.png    koden med omgivelser, uden markeringer
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

# --------------------------------------------------------------------------
# Krav. Kilder og forklaring: references/kilder.md (kilde-ID), references/tjekpunkter.md (tjekpunkt-ID)
# og references/gs1-krav.md.
# --------------------------------------------------------------------------
MM_PR_PT = 25.4 / 72
DPI_FIND, DPI_MAAL, DPI_RAA = 300, 1200, 400
X_MIN, X_MAAL, X_MAX = 0.264, 0.330, 0.660            # GS1 v26 tabel 5-44 (K-01)
SPEC = {   # elementer = streger + mellemrum, startende og sluttende med en streg
    "EAN-13": dict(elementer=59, moduler=95, lyszone=(11, 7), faktor=69.24, guards=(0, 2, 28, 30, 56, 58)),
    "UPC-A": dict(elementer=59, moduler=95, lyszone=(9, 9), faktor=69.24, guards=(0, 2, 4, 6, 28, 30, 52, 54, 56, 58)),
    "EAN-8": dict(elementer=43, moduler=67, lyszone=(7, 7), faktor=55.24, guards=(0, 2, 20, 22, 40, 42)),
    "UPC-E": dict(elementer=33, moduler=51, lyszone=(9, 7), faktor=69.24, guards=(0, 2, 28, 30, 32)),
}
GTIN_LAENGDE = {"EAN-13": 13, "UPC-A": 12, "EAN-8": 8, "UPC-E": 8}
GUARD_X = 5.0             # guard bars forlænges 5X nedad
CIFRE_AFSTAND_X = 0.5     # luft mellem streger og cifre
CIFRE_MIN_SKRIFT_MM = 2.0
KANT_MIN_MM = 8.0         # GS1 v26 6.3.3.3 (K-09): når muligt
X2D_MIN, X2D_MAAL, X2D_MAX = 0.396, 0.495, 0.990
AFSTAND_2D_MM = 50.0
GS1_128_MAX_TEGN, GS1_128_MAX_MM = 48, 165.10
GS1_128_LYSZONE_BUFFER_MM = 13.2    # 2 x 10X ved størst mulig X (0,660 mm): så meget kan lyszonerne lægge til
# Tabel 5-44, anden halvdel (s. 410): mindste afstand mellem hovedkode og tillæg, højst 12X.
# EAN-8 med tillæg står ikke i tabellen (None = ikke angivet)
TILLAEG_MIN_X = {"EAN-13": 7, "UPC-A": 9, "UPC-E": 7, "EAN-8": None}
TILLAEG_MAX_X = 12
X_ONDEMAND_MIN = 0.249        # fodnote (*) tabel 5-44: kun on-demand-print (termisk, laser)
KONTRAST_OK, KONTRAST_MIN = 0.55, 0.40   # 40 %: GS1 v26 5.12.5.11.1 (K-08). 55 %: ikke fundet i GS1, ikke verificeret
TOL_MM = 0.05             # margin: ca. 2 pixel ved 1200 dpi (0,021 mm pr. pixel). Afprøvet 2026-11-22 på selvlavede
                          # vektor-PDF'er: afvigelse højst 0,01 mm (X højst 0,0002 mm). Se references/kilder.md
SKILL_VERSION = "2.1-offentlig"
TEKNISK_MAGENTA = False   # sættes med --teknisk-magenta
MIN_DIAMETER = {          # GS1 v26 tabel 6-2 (K-14), picket fence på cylinder
    0.264: {"EAN-13": 48, "UPC-A": 48, "EAN-8": 34, "UPC-E": 26},
    0.300: {"EAN-13": 55, "UPC-A": 55, "EAN-8": 38, "UPC-E": 29},
    0.350: {"EAN-13": 64, "UPC-A": 64, "EAN-8": 45, "UPC-E": 34},
    0.400: {"EAN-13": 73, "UPC-A": 73, "EAN-8": 51, "UPC-E": 39},
    0.450: {"EAN-13": 82, "UPC-A": 82, "EAN-8": 58, "UPC-E": 44},
    0.500: {"EAN-13": 91, "UPC-A": 91, "EAN-8": 64, "UPC-E": 49},
    0.550: {"EAN-13": 100, "UPC-A": 100, "EAN-8": 70, "UPC-E": 54},
    0.600: {"EAN-13": 109, "UPC-A": 109, "EAN-8": 77, "UPC-E": 59},
    0.660: {"EAN-13": 120, "UPC-A": 120, "EAN-8": 85, "UPC-E": 64},
}

INGEN_FUND, RET, VURDER, SE_SELV, EFTER_TRYK, IKKE_MAALT = "INGEN_FUND", "RET", "VURDER", "SE_SELV", "EFTER_TRYK", "IKKE_MAALT"


def ensure_deps() -> None:
    deps = [("fitz", "pymupdf==1.27.1", "pymupdf"), ("zxingcpp", "zxing-cpp==3.0.0", "zxing-cpp"),
            ("numpy", "numpy", "numpy"), ("PIL", "pillow", "pillow")]
    for module, pinned, loose in deps:
        if importlib.util.find_spec(module):
            continue
        ok = False
        for spec in (pinned, loose):
            for extra in ([], ["--break-system-packages"]):
                cmd = [sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", spec, *extra]
                if subprocess.run(cmd, capture_output=True).returncode == 0:
                    ok = True
                    break
            if ok:
                break
        if not ok:
            sys.exit(f"FEJL: Python-pakken {loose} kunne ikke installeres. Stregkoden kan ikke måles uden.")
    importlib.invalidate_caches()


def gtin14(v):
    """Samme nummer uanset form: UPC-A (12), EAN-13 med 0 foran og GTIN-14 sammenlignes ens."""
    d = re.sub(r"\D", "", v or "")
    return d.zfill(14) if d else ""


# Tjek-id i scriptet -> (tjekpunkt-ID, kilde-ID, sted i kilden, lag). Se references/tjekpunkter.md og kilder.md.
# Lag "GS1" er krav fra GS1 General Specifications v26. Lag "varedata" sammenligner med det GTIN, brugeren oplyser.
TJEKPUNKT = {
    "stoerrelse": ("SK-01", "K-01", "GS1 v26 tabel 5-44 (5.12.3.1)", "GS1"),
    "hoejde": ("SK-02", "K-02, K-03", "GS1 v26 tabel 5-44 med fodnote (**), 6.3.3.4", "GS1"),
    "guard": ("SK-03", "K-04", "GS1 v26 5.2.3.2", "GS1"),
    "lyszone_v": ("SK-04", "K-05", "GS1 v26 tabel 5-44, 5.2.3.4", "GS1"),
    "lyszone_h": ("SK-04", "K-05", "GS1 v26 tabel 5-44, 5.2.3.4", "GS1"),
    "cifre": ("SK-05", "K-06", "GS1 v26 5.2.5", "GS1"),
    "cifre_afstand": ("SK-06", "K-06", "GS1 v26 5.2.5", "GS1"),
    "cifre_stoerrelse": ("SK-07", "K-07", "GS1 v26 4.14 regel 2.a.iii (bør)", "GS1"),
    "cifre_tekst": ("SK-08", "K-06", "GS1 v26 5.2.5", "GS1"),
    "cifre_stanse": ("SK-09", "K-06", "GS1 v26 5.2.5 (afledt)", "GS1"),
    "kontrast": ("SK-10", "K-08", "GS1 v26 5.12.5.11.1 og tabel 5-44 (afledt)", "GS1"),
    "kant": ("SK-11", "K-09, K-10", "GS1 v26 6.3.3.3 (når muligt), 6.2.3.3", "GS1"),
    "linjer": ("SK-12", "K-10", "GS1 v26 6.2.3.3", "GS1"),
    "kode_findes": ("SK-13", "K-11", "GS1 v26 6.3.1", "GS1"),
    "kontrolciffer": ("SK-14", "K-21", "GS1 v26 5.2.2.1-5.2.2.3 (SHALL), 7.9.1", "GS1"),
    "itf": ("SK-15", "K-12", "GS1 v26 5.1.1 (beskrivende)", "GS1"),
    "flere_koder": ("SK-16", "K-11, K-17", "GS1 v26 6.3.1, 4.15.1 pkt. 2", "GS1"),
    "forskellige_numre": ("SK-16", "K-11", "GS1 v26 6.3.1", "GS1"),
    "tillaeg": ("SK-17", "K-13", "GS1 v26 5.2.3.6, tabel 5-44 (s. 410)", "GS1"),
    "krumning": ("SK-18", "K-14", "GS1 v26 6.2.3.2, tabel 6-1 og 6-2", "GS1"),
    "2d_stoerrelse": ("SK-19", "K-15", "GS1 v26 tabel 5-46", "GS1"),
    "2d_digital_link": ("SK-20", "K-16", "GS1 v26 tabel 5-46 fodnote (**)", "GS1"),
    "2d_gtin": ("SK-21", "K-17", "GS1 v26 4.15.1 pkt. 2 og 8", "GS1"),
    "2d_alene": ("SK-22", "K-18", "GS1 v26 tabel 5-45 (tekst efter), 4.15.4 pkt. 1", "GS1"),
    "2d_afstand": ("SK-23", "K-19", "GS1 v26 6.3.3.1 (bør)", "GS1"),
    "gs1_128": ("SK-24", "K-20", "GS1 v26 5.4.1, 5.4.4.3, 5.4.6.3", "GS1"),
    "tryk": ("SK-25", "K-08, K-05", "GS1 v26 tabel 5-44", "GS1"),
    "varenummer": ("VD-01", "K-35", "Oplyst af brugeren (varedata), ikke et GS1-krav", "varedata"),
}
# Måleusikkerhed pr. tjek (mm), som siges i rapporten. Se "Målingens usikkerhed" i SKILL.md.
USIKKERHED = {
    "stoerrelse": "X måles med under 0,1 % afvigelse på vektor-PDF'er",
    "hoejde": f"margin {TOL_MM:g} mm (afprøvet: højst 0,01 mm afvigelse)",
    "guard": f"margin {TOL_MM:g} mm (afprøvet: højst 0,01 mm afvigelse)",
    "lyszone_v": f"margin {TOL_MM:g} mm (afprøvet: højst 0,01 mm afvigelse)",
    "lyszone_h": f"margin {TOL_MM:g} mm (afprøvet: højst 0,01 mm afvigelse)",
    "cifre_afstand": "margin 0,02 mm. Ikke afprøvet",
    "kontrast": "tilnærmelse i rødt lys, ikke en verifier-måling. Ikke afprøvet",
    "kant": "ikke afprøvet",
    "tillaeg": f"margin {TOL_MM:g} mm. Ikke afprøvet separat",
}


def tjek(id_, navn, status, tekst, maalt=None, krav=None, kilde=None):
    tp = TJEKPUNKT.get(id_)
    t = {"id": id_, "tjekpunkt": tp[0] if tp else None, "kilde_id": tp[1] if tp else None, "lag": tp[3] if tp else None,
         "navn": navn, "status": status, "tekst": tekst, "maalt": maalt, "krav": krav,
         "kilde": tp[2] if tp else kilde}
    if id_ in USIKKERHED and status in (RET, VURDER, INGEN_FUND) and maalt:
        t["usikkerhed"] = USIKKERHED[id_]
    return t


def r2(v, n=2):
    return None if v is None else round(float(v), n)


# --------------------------------------------------------------------------
# Indlæsning
# --------------------------------------------------------------------------

def open_document(path: Path, dpi: float | None):
    import fitz
    if path.suffix.lower() == ".pdf":
        return fitz.open(path), "pdf"
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
        res = dpi or (im.info.get("dpi") or (None,))[0]
    if not res:
        sys.exit("FEJL: billedet har ingen opløsning. Angiv den med --dpi (fx --dpi 300).")
    doc = fitz.open()
    page = doc.new_page(width=w * 72 / res, height=h * 72 / res)
    page.insert_image(page.rect, filename=str(path))
    return doc, f"billede ({w}x{h} px ved {res:g} dpi)"


def render(page, dpi, clip=None, gray=False):
    import fitz
    import numpy as np
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False,
                          colorspace=fitz.csGRAY if gray else fitz.csRGB)
    a = np.frombuffer(pix.samples, dtype=np.uint8)
    return a.reshape(pix.height, pix.width) if gray else a.reshape(pix.height, pix.width, 3)


def fmt_name(r) -> str:
    return str(r.format).replace("BarcodeFormat.", "")


def split_tillaeg(text: str, fmt: str):
    raw = (text or "").strip()
    m = re.match(r"^(\d{8,14})[ +](\d{2}|\d{5})$", raw)
    if m:
        return m.group(1), m.group(2)
    n = GTIN_LAENGDE.get(fmt)
    if n and raw.isdigit() and len(raw) - n in (2, 5):
        return raw[:n], raw[n:]
    return raw, None


def find_symbols(doc, rod_lys=False):
    """Alle koder på alle sider. Returnerer (koder, afviste)."""
    import numpy as np
    import zxingcpp
    opts = {}
    if hasattr(zxingcpp, "EanAddOnSymbol"):
        opts["ean_add_on_symbol"] = zxingcpp.EanAddOnSymbol.Read
    koder, afviste = [], []
    for pno, page in enumerate(doc, start=1):
        # Gråtoner direkte fra PyMuPDF: en tredjedel af hukommelsen og ingen float-kopi
        # af en side der kan være 7000 x 5000 px.
        gray = np.ascontiguousarray(render(page, DPI_FIND, gray=True))
        found = list(zxingcpp.read_barcodes(gray, return_errors=True, **opts))
        if not any(r.valid for r in found) and (found or rod_lys):
            # Som scanneren ser det: rødt lys. Magenta markeringer og rød/orange/brun bund
            # bliver lyse, så en kode de forstyrrer i gråtoner kan læses her. Kun når gråtonerne gav
            # en ugyldig læsning, eller når hele filen er gennemsøgt uden fund (koster en farvegengivelse).
            rod = np.ascontiguousarray(render(page, DPI_FIND)[..., 0])
            i_rod = list(zxingcpp.read_barcodes(rod, return_errors=True, **opts))
            if any(r.valid for r in i_rod):
                found = i_rod
            del rod
        omvendt = False
        if not any(r.valid for r in found):
            inv = list(zxingcpp.read_barcodes(np.ascontiguousarray(255 - gray), **opts))
            if inv:
                found, omvendt = inv, True
        for r in found:
            fmt = fmt_name(r)
            pts = [(p.x, p.y) for p in (r.position.top_left, r.position.top_right,
                                        r.position.bottom_right, r.position.bottom_left)]
            s = 72.0 / DPI_FIND
            bbox = [min(x for x, _ in pts) * s, min(y for _, y in pts) * s,
                    max(x for x, _ in pts) * s, max(y for _, y in pts) * s]
            if not r.valid:
                if fmt in SPEC and re.fullmatch(r"\d{7,14}", r.text or ""):
                    afviste.append({"type": fmt, "nummer": r.text, "side": pno, "bbox_pt": bbox,
                                    "fejl": str(r.error)})
                continue
            main, add = split_tillaeg(r.text, fmt)
            koder.append({"type": fmt, "nummer": main, "tillaeg": add, "side": pno, "bbox_pt": bbox,
                          "retning": int(r.orientation or 0), "omvendt": omvendt,
                          "symbologi_id": r.symbology_identifier, "ekstra": dict(r.extra or {}),
                          "raa_tekst": r.text})
    # zxing leverer en kode med tillæg to gange: hovedkoden alene og koden med
    # tillæg. Tillægget lægges på hovedkoden, så målingen sker på hovedkoden.
    for k in [k for k in koder if k["ekstra"].get("EanAddOn") or k["tillaeg"]]:
        k["tillaeg"] = k["ekstra"].get("EanAddOn") or k["tillaeg"]
        soskende = [o for o in koder if o is not k and o["nummer"] == k["nummer"] and o["side"] == k["side"]
                    and not o["tillaeg"] and naer(o["bbox_pt"], k["bbox_pt"], 60 / MM_PR_PT)]
        if soskende:
            o = soskende[0]
            o["tillaeg"] = k["tillaeg"]
            o["bbox_pt"] = [o["bbox_pt"][0], min(o["bbox_pt"][1], k["bbox_pt"][1]),
                            o["bbox_pt"][2], max(o["bbox_pt"][3], k["bbox_pt"][3])] if o["retning"] % 180 == 0 else \
                           [min(o["bbox_pt"][0], k["bbox_pt"][0]), o["bbox_pt"][1],
                            max(o["bbox_pt"][2], k["bbox_pt"][2]), o["bbox_pt"][3]]
            koder.remove(k)
    # Samme kode læst to gange samme sted tælles én gang.
    unikke = []
    for k in sorted(koder, key=lambda k: k["tillaeg"] is None):
        if not any(u["nummer"] == k["nummer"] and u["side"] == k["side"] and overlap(u["bbox_pt"], k["bbox_pt"])
                   for u in unikke):
            unikke.append(k)
    unikke.sort(key=lambda k: (k["side"], k["bbox_pt"][1], k["bbox_pt"][0]))
    for i, k in enumerate(unikke, start=1):
        k["nr"] = i
    return unikke, afviste


def naer(a, b, d):
    return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])


def overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


# --------------------------------------------------------------------------
# Siden: format, etiketkant, målestok, linjer
# --------------------------------------------------------------------------

def format_fra_args(tekst) -> dict:
    """Etikettens format i mm fra --format, fx '100x60' eller '100 x 60 mm'."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)", tekst or "")
    if not m:
        return {}
    return {"format_mm": [float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))]}


def rammer(page, format_mm, tegninger):
    """Rektangler på siden med præcis det oplyste formats mål (uanset farve)."""
    import fitz
    if not format_mm:
        return []
    W, H = format_mm
    fundne, med_beskaering = [], []
    for d in tegninger:
        rects = [d["rect"]] + [it[1] for it in d["items"] if it[0] == "re"]
        for r in rects:
            w, h = r.width * MM_PR_PT, r.height * MM_PR_PT
            for tw, th in ((W, H), (H, W)):
                if abs(w - tw) <= 1.5 and abs(h - th) <= 1.5:
                    if not any(abs(r.x0 - f.x0) < 1 and abs(r.y0 - f.y0) < 1 for f in fundne):
                        fr = fitz.Rect(r)
                        fr.farve = d.get("color")   # skabelonens tekniske farve, hvis rammen er streget
                        fundne.append(fr)
                # Baggrundsflade med beskæring (bleed): samme overskud på alle sider.
                bx, by = (w - tw) / 2, (h - th) / 2
                if 1.0 <= bx <= 6.0 and abs(bx - by) <= 0.5:
                    b = (bx + by) / 2 / MM_PR_PT
                    fr = fitz.Rect(r.x0 + b, r.y0 + b, r.x1 - b, r.y1 - b)
                    fr.farve = None
                    med_beskaering.append(fr)
    if not fundne:
        fundne = med_beskaering[:1]
    tb = page.trimbox
    if tb != page.mediabox:
        w, h = tb.width * MM_PR_PT, tb.height * MM_PR_PT
        if (abs(w - W) <= 1.0 and abs(h - H) <= 1.0) or (abs(w - H) <= 1.0 and abs(h - W) <= 1.0):
            fundne.append(fitz.Rect(tb))
    return fundne


def maalestok(page, kol, fundne):
    side_mm = (page.rect.width * MM_PR_PT, page.rect.height * MM_PR_PT)
    fmt = kol.get("format_mm")
    if fmt and fundne:
        return {"status": "bekraeftet", "tekst": f"Det oplyste format {fmt[0]:g} x {fmt[1]:g} mm passer med "
                f"en ramme på siden, så PDF'en er i 1:1."}
    if fmt and (max(side_mm) + 1 < max(fmt) or min(side_mm) + 1 < min(fmt)):
        return {"status": "tvivl", "tekst": f"Siden ({side_mm[0]:.0f} x {side_mm[1]:.0f} mm) er mindre end "
                f"det oplyste format ({fmt[0]:g} x {fmt[1]:g} mm). PDF'en er sandsynligvis skaleret, "
                "og mål i mm passer ikke."}
    if fmt:
        return {"status": "antaget", "tekst": f"Det oplyste format {fmt[0]:g} x {fmt[1]:g} mm, men ingen ramme "
                "med de mål blev fundet. Målene forudsætter at PDF'en er i 1:1."}
    return {"status": "antaget", "tekst": "Intet format oplyst (--format). Målene forudsætter at filen er i 1:1."}


def er_teknisk(c, fundne):
    """Ikke-trykt teknisk farve: magenta (kun med --teknisk-magenta) eller farven på den streg-ramme,
    der matcher det oplyste format."""
    if not c:
        return False
    if TEKNISK_MAGENTA and c[0] > 0.6 and c[1] < 0.35 and c[2] > 0.3:
        return True
    return any(getattr(f, "farve", None) and max(abs(a - b) for a, b in zip(c[:3], f.farve[:3])) < 0.06
               for f in fundne)


def delstier(items, trin=16):
    """En tegnings delstier som lister af punkter (pt). Kurver samples."""
    import fitz
    stier, cur = [], []
    for it in items:
        if it[0] == "re":
            r = fitz.Rect(it[1])
            stier.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
            continue
        if it[0] == "qu":
            q = it[1]
            stier.append([tuple(q.ul), tuple(q.ur), tuple(q.lr), tuple(q.ll), tuple(q.ul)])
            continue
        if it[0] == "l":
            seg = [(it[1].x, it[1].y), (it[2].x, it[2].y)]
        elif it[0] == "c":
            p0, p1, p2, p3 = it[1:5]
            seg = [(p0.x, p0.y)]
            for i in range(1, trin + 1):
                t = i / trin
                u = 1 - t
                seg.append((u ** 3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t ** 3 * p3.x,
                            u ** 3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t ** 3 * p3.y))
        else:
            continue
        if cur and math.dist(cur[-1], seg[0]) < 0.5:
            cur.extend(seg[1:])
        else:
            if cur:
                stier.append(cur)
            cur = list(seg)
    if cur:
        stier.append(cur)
    return stier


def areal(pts):
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2


def i_polygon(x, y, poly):
    inde, j = False, len(poly) - 1
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[j]
        if (yi > y) != (yj > y) and x < xi + (y - yi) * (xj - xi) / ((yj - yi) or 1e-12):
            inde = not inde
        j = i
    return inde


def afstand_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / n))
    return math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))


def form_af(st):
    xs, ys = [p[0] for p in st], [p[1] for p in st]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if areal(st) >= 0.995 * w * h:
        return "rektangulær"
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    r = [math.dist((mx, my), q) for q in st]
    return "rund" if max(r) - min(r) < 0.02 * max(r) else "formet"


def stanselinje(tegninger, fundne, kode_rect, format_mm=None):
    """Lukkede tekniske konturer der omslutter koden.

    ydre: konturen med det oplyste format (etikettens yderkant, rund eller formet), ellers
          den største. indre: den mindste, hvis den er en anden (panel, fold eller
          sikkerhedsramme inde på arket).
    """
    cx, cy = (kode_rect.x0 + kode_rect.x1) / 2, (kode_rect.y0 + kode_rect.y1) / 2
    min_areal = 1.5 * kode_rect.width * kode_rect.height
    kandidater = [[(f.x0, f.y0), (f.x1, f.y0), (f.x1, f.y1), (f.x0, f.y1), (f.x0, f.y0)] for f in fundne]
    for d in tegninger:
        if d.get("color") is None or not er_teknisk(d["color"], fundne):
            continue
        kandidater += [st for st in delstier(d["items"]) if len(st) >= 4 and math.dist(st[0], st[-1]) < 1.5]
    omslutter = [(areal(st), st) for st in kandidater if areal(st) >= min_areal and i_polygon(cx, cy, st)]
    if not omslutter:
        return None, None
    omslutter.sort(key=lambda t: t[0])

    def passer_format(st):
        if not format_mm:
            return False
        xs, ys = [p[0] for p in st], [p[1] for p in st]
        w, h = (max(xs) - min(xs)) * MM_PR_PT, (max(ys) - min(ys)) * MM_PR_PT
        return any(abs(w - a) <= 1.5 and abs(h - b) <= 1.5 for a, b in (format_mm, format_mm[::-1]))
    med_format = [t for t in omslutter if passer_format(t[1])]
    # Er der flere med Format-mål (fx rektangel og den runde kontur indeni), er den mindste stanselinjen.
    ydre = med_format[0][1] if med_format else omslutter[-1][1]
    indre = omslutter[0][1] if omslutter[0][1] is not ydre and omslutter[0][0] < 0.9 * areal(ydre) else None
    return (ydre, form_af(ydre)), ((indre, form_af(indre)) if indre else None)



def kant_afstand_mm(poly, rect):
    """Mindste afstand fra kodens kant til konturen. Negativ = så meget går koden udenfor."""
    pts = []
    n = 24
    for i in range(n + 1):
        x = rect.x0 + rect.width * i / n
        y = rect.y0 + rect.height * i / n
        pts += [(x, rect.y0), (x, rect.y1), (rect.x0, y), (rect.x1, y)]
    segs = list(zip(poly, poly[1:] + poly[:1]))
    inde, ude = math.inf, 0.0
    for px, py in pts:
        d = min(afstand_seg(px, py, a, b) for a, b in segs)
        if i_polygon(px, py, poly):
            inde = min(inde, d)
        else:
            ude = max(ude, d)
    return (-ude if ude > 0 else inde) * MM_PR_PT


def keglestub(poly):
    """Er konturen en ringsektor (udfoldet bøtte- eller bægeretiket)?

    To lange rette sider peger mod et fælles centrum, og de øvrige punkter ligger på
    to radier om det. Går etiketten hele vejen rundt, er buelængden lig omkredsen,
    så diameteren er r * vinkel / pi. Returnerer diametre i mm eller None.
    """
    segs = [(poly[i], poly[i + 1]) for i in range(len(poly) - 1)]
    lange = sorted(segs, key=lambda s: -math.dist(*s))[:2]
    if len(lange) < 2 or math.dist(*lange[1]) < 10 / MM_PR_PT:
        return None
    (a1, a2), (b1, b2) = lange
    d = (a2[0] - a1[0]) * (b2[1] - b1[1]) - (a2[1] - a1[1]) * (b2[0] - b1[0])
    if abs(d) < 1e-6:
        return None
    t = ((b1[0] - a1[0]) * (b2[1] - b1[1]) - (b1[1] - a1[1]) * (b2[0] - b1[0])) / d
    c = (a1[0] + t * (a2[0] - a1[0]), a1[1] + t * (a2[1] - a1[1]))
    radier = [math.dist(c, q) for q in poly]
    ri, ry = min(radier), max(radier)
    if ri < 5 / MM_PR_PT or ry - ri < 5 / MM_PR_PT:
        return None
    paa_bue = sum(1 for r in radier if min(abs(r - ri), abs(r - ry)) < 0.01 * ry)
    if paa_bue < 0.8 * len(radier):
        return None
    v = [math.atan2(q[1] - c[1], q[0] - c[0]) for q in poly]
    ref = v[0]
    rel = [((x - ref + math.pi) % (2 * math.pi)) - math.pi for x in v]
    vinkel = max(rel) - min(rel)
    return {"d_lille_mm": ri * MM_PR_PT * vinkel / math.pi, "d_stor_mm": ry * MM_PR_PT * vinkel / math.pi,
            "vinkel_grader": math.degrees(vinkel), "_centrum": c, "_vinkel": vinkel}


def krydsende_linjer(tegninger, zone, fundne):
    """Stregede linjer (ikke fyld) der går gennem kodens zone."""
    import fitz
    out = []
    for d in tegninger:
        if d.get("color") is None or d.get("type") == "f":
            continue
        if not (d["rect"] + (-0.5, -0.5, 0.5, 0.5)).intersects(zone):
            continue
        c = d.get("color") or (0, 0, 0)
        stiplet = bool(re.search(r"\[\s*\d", str(d.get("dashes") or "")))
        teknisk = er_teknisk(c, fundne)
        if max(c[:3]) < 0.3 and not stiplet:
            continue   # sorte, ubrudte streger er design (fx omridsede cifre)
        hit = False
        for it in d["items"]:
            if it[0] == "l":
                hit = seg_rect(it[1], it[2], zone)
            elif it[0] == "re":
                r = fitz.Rect(it[1])
                hit = r.intersects(zone) and not r.contains(zone) and not zone.contains(r)
            elif it[0] in ("c", "qu") and (stiplet or teknisk):
                # Kurver tæller kun som teknik (fx en afrundet stanselinje); ellers er det design.
                if it[0] == "c":
                    hit = fitz.Rect(it[1], it[4]).include_point(it[2]).include_point(it[3]).intersects(zone)
                else:
                    hit = it[1].rect.intersects(zone) and not it[1].rect.contains(zone)
            if hit:
                break
        if not hit or any(d["rect"].contains(zone) and abs(d["rect"].x0 - f.x0) < 1 for f in fundne):
            continue
        out.append({"farve": "#%02x%02x%02x" % tuple(int(255 * v) for v in c[:3]), "teknisk": teknisk,
                    "_items": d["items"], "_bredde_pt": d.get("width") or 0.5,
                    "stiplet": stiplet,
                    "bredde_mm": r2((d.get("width") or 0) * MM_PR_PT),
                    "rect_pt": [r2(v) for v in d["rect"]]})
    return out


def seg_rect(p, q, r):
    """Skærer linjestykket p-q rektanglet r?"""
    if r.contains(p) or r.contains(q):
        return True
    import fitz
    edges = [(r.tl, r.tr), (r.tr, r.br), (r.br, r.bl), (r.bl, r.tl)]
    return any(segs_cross(p, q, a, b) for a, b in edges)


def segs_cross(p1, p2, p3, p4):
    def o(a, b, c):
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
    d1, d2, d3, d4 = o(p3, p4, p1), o(p3, p4, p2), o(p1, p2, p3), o(p1, p2, p4)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


# --------------------------------------------------------------------------
# Måling af en 1D-retailkode
# --------------------------------------------------------------------------

def magenta_maske(rgb):
    """Pixels i teknisk magenta inkl. kantudjævning mod hvidt, udvidet 2 px. Tom uden --teknisk-magenta."""
    import numpy as np
    if not TEKNISK_MAGENTA:
        return np.zeros(rgb.shape[:2], bool)
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    m = (r > 150) & (r - g > 90) & (b - g > 40)
    for ax in (0, 1):   # udvid 2 px, så kantudjævnede rester også dækkes
        m = m | np.roll(m, 1, ax) | np.roll(m, -1, ax) | np.roll(m, 2, ax) | np.roll(m, -2, ax)
    return m


def otsu(v):
    import numpy as np
    h = np.bincount(v.ravel(), minlength=256).astype(float)
    p = h / h.sum()
    w = np.cumsum(p)
    mu = np.cumsum(p * np.arange(256))
    with np.errstate(divide="ignore", invalid="ignore"):
        s = (mu[-1] * w - mu) ** 2 / (w * (1 - w))
    if not np.isfinite(s).any():      # kun én gråtone: ingen tærskel at finde
        return int(v.mean()) if v.size else 128
    return int(np.nanargmax(np.where(np.isfinite(s), s, -1)))


def runs(mask):
    out, start = [], 0
    for i in range(1, len(mask) + 1):
        if i == len(mask) or mask[i] != mask[start]:
            out.append((start, i - start, bool(mask[start])))
            start = i
    return out


def lin(v):
    v = v / 255.0
    return ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92


def maal_1d(page, kode, spec, tegninger=(), fundne=(), format_mm=None):
    """Mål koden på stregerne selv. Returnerer mål (mm) og geometri til tegning."""
    import fitz
    import numpy as np
    x0, y0, x1, y1 = kode["bbox_pt"]
    k = int(round(kode["retning"] / 90.0)) % 4
    tvaers = k in (1, 3)                 # koden står lodret på siden
    laengde_pt = (y1 - y0) if tvaers else (x1 - x0)
    x_gaet_mm = laengde_pt * MM_PR_PT / spec["moduler"]
    # zxing's ramme kan være en enkelt scanlinje; udsnittet skal rumme hele højden
    m_laeng, m_tvaers = 16 / MM_PR_PT, (9 + 80 * x_gaet_mm) / MM_PR_PT
    mx, my = (m_tvaers, m_laeng) if tvaers else (m_laeng, m_tvaers)
    clip = fitz.Rect(x0 - mx, y0 - my, x1 + mx, y1 + my) & page.rect
    rgb = render(page, DPI_MAAL, clip)
    rgb = np.ascontiguousarray(np.rot90(rgb, k))
    lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(np.uint8)
    px_mm = DPI_MAAL / 25.4
    H, W = lum.shape
    # Tekniske markeringer i magenta (stanselinjer, mål), som ikke trykkes, må hverken tælle
    # som streg, mellemrum, lyszone eller ciffer. Kun med --teknisk-magenta.
    tek_px = magenta_maske(rgb)
    # Kodens midte i det drejede udsnit
    cx_pg, cy_pg = (x0 + x1) / 2, (y0 + y1) / 2
    mask = np.zeros(render_shape(clip), bool)
    py = int((cy_pg - clip.y0) * DPI_MAAL / 72)
    px = int((cx_pg - clip.x0) * DPI_MAAL / 72)
    mask[min(py, mask.shape[0] - 1), min(px, mask.shape[1] - 1)] = True
    mask = np.rot90(mask, k)
    cy, cx = [int(v[0]) for v in np.nonzero(mask)]
    halv_laengde = ((y1 - y0) if tvaers else (x1 - x0)) * DPI_MAAL / 72 / 2

    c_sl = (slice(max(0, cy - int(3 * px_mm)), cy + int(3 * px_mm)),
            slice(max(0, int(cx - halv_laengde)), int(cx + halv_laengde)))
    centrum = lum[c_sl][~tek_px[c_sl]] if (~tek_px[c_sl]).any() else lum[c_sl]
    thr = otsu(centrum)
    band = max(1, int(0.25 * px_mm))
    if tek_px[max(0, cy - band): cy + band + 1, c_sl[1]].any():
        band = max(1, int(1.5 * px_mm))   # en teknisk markering hen over koden: brug et bredere bånd
    blok = lum[max(0, cy - band): cy + band + 1].astype(float)
    blok[tek_px[max(0, cy - band): cy + band + 1]] = np.nan
    with np.errstate(all="ignore"):
        gns = np.nanmean(blok, axis=0)
    gns = np.where(np.isnan(gns), 255, gns)
    profil = gns < thr
    rr = runs(profil)
    n, moduler = spec["elementer"], spec["moduler"]
    venstre_forventet = cx - halv_laengde
    x_gaet = 2 * halv_laengde / moduler
    bedst = None
    for i, (s, l, dark) in enumerate(rr):
        if not dark or abs(s - venstre_forventet) > 12 * x_gaet or i + n > len(rr):
            continue
        el = rr[i:i + n]
        if not el[-1][2]:
            continue
        bredde = el[-1][0] + el[-1][1] - el[0][0]
        X = bredde / moduler
        guard_fejl = max(abs(e[1] / X - 1) for e in el[:3])
        score = guard_fejl + abs(bredde - 2 * halv_laengde) / (2 * halv_laengde)
        if bedst is None or score < bedst[0]:
            bedst = (score, i, el, X)
    if bedst is None or bedst[0] > 1.5:
        return None, "Stregerne kunne ikke tælles op i højopløsning (koden er måske skæv, beskadiget eller trykt på mønster)."
    _, i0, el, Xpx = bedst
    venstre, hoejre = el[0][0], el[-1][0] + el[-1][1]

    def kolonner(idx):
        return [el[j][0] + el[j][1] // 2 for j in idx]
    streger = [j for j in range(0, n, 2)]
    mork0 = lum < thr

    def streg_bund(j):
        c = el[j][0] + el[j][1] // 2
        r = cy
        while r + 1 < H and mork0[r + 1, c]:
            r += 1
        return r
    bunde = {j: streg_bund(j) for j in streger}
    normal = np.median([bunde[j] for j in streger if j not in spec["guards"]])
    # Guard bars + evt. UPC-A's forlængede første/sidste ciffer (EAN-13 med 0 foran = UPC-A)
    guard_idx = [j for j in streger if j in spec["guards"] or bunde[j] > normal + 2 * Xpx_foreloebig(el, moduler)]
    data_idx = [j for j in streger if j not in guard_idx]
    rum_idx = [j for j in range(1, n, 2)]
    dc, gc, rc = kolonner(data_idx), kolonner(guard_idx), kolonner(rum_idx)

    mork = lum < thr
    lys = ~mork
    dc_a, rc_a = np.array(dc), np.array(rc)

    def kode_raekke(r):
        # Kolonner dækket af en teknisk markering tæller ikke med.
        fd, fr = ~tek_px[r, dc_a], ~tek_px[r, rc_a]
        if fd.mean() < 0.3 or fr.mean() < 0.3:
            return True
        return mork[r, dc_a[fd]].mean() >= 0.85 and lys[r, rc_a[fr]].mean() >= 0.85

    spring = int(0.35 * px_mm)   # tynde linjer (op til 0,35 mm) hen over koden springes over

    def udstraek(r, trin):
        while True:
            n = r + trin
            if 0 <= n < H and kode_raekke(n):
                r = n
                continue
            for d in range(2, spring + 2):
                n2 = r + trin * d
                if 0 <= n2 < H and kode_raekke(n2) and all(
                        0 <= r + trin * dd < H and kode_raekke(r + trin * dd) for dd in range(d, min(d + 3, spring + 2))):
                    r = n2
                    break
            else:
                return r

    top = udstraek(cy, -1)
    bund = udstraek(cy, 1)
    hoejde_px = bund - top + 1

    # Guard bars: hvor langt under de andre streger de fortsætter.
    guard_rum = [j for j in rum_idx if j - 1 in guard_idx and j + 1 in guard_idx]
    grc = kolonner(guard_rum)
    g = bund
    while g < H - 1 and mork[g + 1, gc].mean() >= 0.85 and (not grc or lys[g + 1, grc].mean() >= 0.85):
        g += 1
    guard_px = g - bund

    # Kodens zone (streger + krævede lyszoner) i sidekoordinater, og linjer der krydser den.
    def til_side(r0, r1, c0, c1):
        bm = np.zeros((H, W), bool)
        bm[max(0, int(r0)):min(H, int(r1)), max(0, int(c0)):min(W, int(c1))] = True
        ys_, xs_ = np.nonzero(np.rot90(bm, -k))
        s_ = 72.0 / DPI_MAAL
        return fitz.Rect(clip.x0 + xs_.min() * s_, clip.y0 + ys_.min() * s_,
                         clip.x0 + (xs_.max() + 1) * s_, clip.y0 + (ys_.max() + 1) * s_)
    lzv_krav, lzh_krav = spec["lyszone"][0] * Xpx, spec["lyszone"][1] * Xpx
    zone = til_side(top, bund + 1, venstre - lzv_krav, hoejre + lzh_krav)
    linjer = krydsende_linjer(tegninger, zone, fundne) if tegninger else []
    omraade = til_side(max(0, top - 4 * px_mm), min(H, bund + 9 * px_mm), max(0, venstre - lzv_krav - 4 * px_mm),
                       min(W, hoejre + lzh_krav + 4 * px_mm))
    naer = krydsende_linjer(tegninger, omraade, fundne) if tegninger else []

    # Tekniske linjer (magenta eller rammens farve) trykkes ikke og tæller hverken i lyszonen
    # eller som cifre.
    teknisk_maske = np.zeros((H, W), bool)
    tekniske = [l for l in naer if l["teknisk"]]
    if tekniske:
        from PIL import Image, ImageDraw
        u = Image.new("1", (render_shape(clip)[1], render_shape(clip)[0]), 0)
        dr = ImageDraw.Draw(u)
        sc = DPI_MAAL / 72
        P = lambda pt: ((pt.x - clip.x0) * sc, (pt.y - clip.y0) * sc)  # noqa: E731
        for l in tekniske:
            bw = max(3, int(l["_bredde_pt"] * sc) + 4)
            for it in l["_items"]:
                if it[0] == "l":
                    dr.line([P(it[1]), P(it[2])], fill=1, width=bw)
                elif it[0] == "re":
                    r_ = fitz.Rect(it[1])
                    dr.rectangle([P(r_.tl), P(r_.br)], outline=1, width=bw)
                elif it[0] == "c":
                    dr.line([P(it[1]), P(it[2]), P(it[3]), P(it[4])], fill=1, width=bw)
        teknisk_maske = np.rot90(np.array(u, dtype=bool), k)
        if teknisk_maske.shape != (H, W):
            teknisk_maske = np.zeros((H, W), bool)
    # Lyszonen vurderes i rødt lys som scanneren (ISO 15416 måler ved ca. 660 nm): rød,
    # orange, pink og brun er lyse for scanneren, sort, blå og grøn er mørke.
    rod_k = rgb[..., 0]
    c_rod = rod_k[c_sl][~tek_px[c_sl]] if (~tek_px[c_sl]).any() else rod_k[c_sl]
    thr_r = otsu(c_rod)
    mork_lz = (rod_k < thr_r) & ~teknisk_maske & ~tek_px
    mork_cif = mork & ~teknisk_maske & ~tek_px

    # Lyszoner: fra yderste streg og udad, i ISO 15416's inspektionsbånd (10-90 % af højden).
    def lyszone(side):
        dist = None
        b0, b1 = top + (bund - top) // 10, bund - (bund - top) // 10
        rk = range(b0, b1 + 1, max(1, (b1 - b0) // 60))
        for r in rk:
            if side < 0:
                seg = mork_lz[r, :venstre][::-1]
            else:
                seg = mork_lz[r, hoejre:]
            hit = np.flatnonzero(seg[:-1] & seg[1:]) if len(seg) > 1 else np.array([])
            d = hit[0] if len(hit) else len(seg)
            dist = d if dist is None else min(dist, d)
        kant = (venstre if side < 0 else W - hoejre)
        return dist, dist >= kant - 1

    lz_v, lz_v_rand = lyszone(-1)
    lz_h, lz_h_rand = lyszone(1)

    # Cifrene under koden: første mørke række mellem guard bars.
    data_x0 = el[3][0] - 1
    data_x1 = el[n - 4][0] + el[n - 4][1] + 1
    under = mork_cif[bund + 1: min(H, bund + 1 + int(8 * px_mm)), data_x0:data_x1].copy()
    for j in guard_idx:   # midterens guard bars går ned mellem cifrene
        a0, a1 = el[j][0] - data_x0 - 2, el[j][0] + el[j][1] - data_x0 + 2
        if a1 > 0 and a0 < under.shape[1]:
            under[:, max(0, a0):min(under.shape[1], a1)] = False
    raekke_mork = under.sum(axis=1) >= 2
    cifre = None
    a = None
    for start, laengde, er_mork in runs(raekke_mork):
        # Under 0,25 mm er det kantudjævning af stregerne, ikke cifre.
        if er_mork and laengde >= 0.25 * px_mm:
            a, b = start, start + laengde - 1
            break
    if a is not None and a <= max(3 * px_mm, 10 * Xpx):   # cifrene skal stå lige under stregerne
        cifre = {"afstand_px": int(a), "hoejde_px": int(b - a + 1), "top": int(bund + 1 + a),
                 "bund": int(bund + 1 + b)}

    # Cifrene læses: først som tekst i PDF'en, ellers med OCR på båndet under koden.
    cifre_laest, cifre_kilde, ocr_forsog = None, None, []
    if cifre:
        b0, b1 = bund + 1, min(H, cifre["bund"] + int(0.4 * px_mm))
        c0, c1 = max(0, int(venstre - 12 * Xpx)), min(W, int(hoejre + 10 * Xpx))
        # Tekstlaget: et lidt større felt, fordi tegnenes bokse er højere end cifrene.
        hri_rect = til_side(max(0, bund - int(0.5 * px_mm)), min(H, cifre["bund"] + int(1.5 * px_mm)),
                            max(0, int(venstre - 15 * Xpx)), min(W, int(hoejre + 12 * Xpx))) if b1 > b0 else None
        if hri_rect is not None:
            t_ = laes_cifre_tekst(page, hri_rect, k)
            # Kun en hel læsning tæller; en halv (fx uden første ciffer) går videre til OCR.
            if t_ and len(t_) in (len(kode["nummer"]), len(kode["nummer"].lstrip("0")), 12, 13) and \
                    abs(len(t_) - len(kode["nummer"])) <= 1:
                cifre_laest, cifre_kilde = t_, "tekst i PDF'en"
        if not cifre_laest and b1 > b0:
            r0, r1 = max(0, cifre["top"] - 4), min(H, cifre["bund"] + 5)
            band = lum[r0:r1, c0:c1].copy()
            band[tek_px[r0:r1, c0:c1]] = 255     # teknisk tekst og mål er ikke cifre
            for j in guard_idx:          # guard bars går ned mellem cifrene
                band[:, max(0, el[j][0] - c0 - 3):max(0, el[j][0] + el[j][1] - c0 + 3)] = 255
            ocr_forsog = laes_cifre_ocr(band)
            if gtin14(kode["nummer"]) not in {gtin14(t) for t in ocr_forsog} and n == 59:
                # Læs første ciffer, venstre og højre gruppe hver for sig (mellem guard bars).
                grupper = [(c0, el[0][0] - 2), (el[2][0] + el[2][1] + 2, el[28][0] - 2),
                           (el[30][0] + el[30][1] + 2, el[56][0] - 2)]
                dele = []
                for g0, g1 in grupper:
                    if g1 - g0 < 5:
                        dele = []
                        break
                    laes = laes_cifre_ocr(lum[r0:r1, g0:g1], psm_liste=(7, 8, 10))
                    dele.append(laes)
                if len(dele) == 3 and all(dele):
                    for a_ in dele[0]:
                        for b_ in dele[1]:
                            for c_ in dele[2]:
                                ocr_forsog.append(a_ + b_ + c_)
            if ocr_forsog:
                rigtig = [t for t in ocr_forsog if gtin14(t) == gtin14(kode["nummer"])]
                cifre_laest = rigtig[0] if rigtig else max(set(ocr_forsog), key=ocr_forsog.count)
                cifre_kilde = "OCR"

    # Kontrast i rødt lys (scannerens 660 nm ~ den røde kanal).
    rod = rgb[..., 0].astype(float)
    midt = slice(top + (bund - top) // 4, bund - (bund - top) // 4)
    bar_r = np.median(np.concatenate([rod[midt, c] for c in dc]))
    rum_r = np.median(np.concatenate([rod[midt, c] for c in rc]))
    sc = lin(rum_r) - lin(bar_r)
    omvendt = bool(kode.get("omvendt")) or bar_r > rum_r

    # Tillæg (EAN-2/5): luften efter hovedsymbolet.
    tillaeg_luft = None
    if kode.get("tillaeg"):
        efter = [r for r in rr[i0 + n:] if r[2]]
        if efter:
            tillaeg_luft = efter[0][0] - hoejre

    # Stregernes yderramme tilbage til sidekoordinater (til kantafstand og tegning).
    bmask = np.zeros((H, W), bool)
    bmask[top:bund + 1 + guard_px, venstre:hoejre] = True
    ub = np.rot90(bmask, -k)
    ys, xs = np.nonzero(ub)
    s = 72.0 / DPI_MAAL
    streg_pt = [clip.x0 + xs.min() * s, clip.y0 + ys.min() * s, clip.x0 + (xs.max() + 1) * s, clip.y0 + (ys.max() + 1) * s]

    kontur, form, kegle = None, None, None
    if tegninger:
        ydre, _ = stanselinje(tegninger, fundne, fitz.Rect(streg_pt), format_mm)
        if ydre:
            kontur, form = ydre
            if form == "formet":
                kegle = keglestub(kontur)
                if kegle:   # diameteren der hvor koden sidder (kodens midte)
                    mid = ((streg_pt[0] + streg_pt[2]) / 2, (streg_pt[1] + streg_pt[3]) / 2)
                    kegle["d_ved_koden_mm"] = math.dist(kegle.pop("_centrum"), mid) * MM_PR_PT * kegle.pop("_vinkel") / math.pi

    h0, w0 = render_shape(clip)

    def til_pt(r, c):
        """Et punkt i det drejede udsnit tilbage til sidekoordinater."""
        rr_, cc_ = {0: (r, c), 1: (c, w0 - 1 - r), 2: (h0 - 1 - r, w0 - 1 - c), 3: (h0 - 1 - c, r)}[k]
        return clip.x0 + (cc_ + 0.5) * 72 / DPI_MAAL, clip.y0 + (rr_ + 0.5) * 72 / DPI_MAAL

    hoejde_inde_px, cifre_ude = None, None
    if kontur is not None and len(kontur) >= 3:
        cmid = (venstre + hoejre) // 2
        prover = [top + (bund - top) * i / 40 for i in range(41)]
        inde = sum(i_polygon(*til_pt(r_, cmid), kontur) for r_ in prover)
        if inde < len(prover):
            hoejde_inde_px = hoejde_px * inde / len(prover)
        if cifre:
            c_v = venstre - 10 * Xpx if spec["moduler"] == 95 else venstre   # EAN-13: første ciffer til venstre
            hjorner = [(cifre["top"], c_v), (cifre["top"], hoejre), (cifre["bund"], c_v), (cifre["bund"], hoejre),
                       (cifre["bund"], (venstre + hoejre) / 2)]
            cifre_ude = not all(i_polygon(*til_pt(r_, c_), kontur) for r_, c_ in hjorner)

    mm = lambda v: None if v is None else v / px_mm  # noqa: E731
    X = Xpx / px_mm
    return {
        "hoejde_inden_for_stanse_mm": mm(hoejde_inde_px), "cifre_uden_for_stanse": cifre_ude,
        "X_mm": X, "bredde_mm": (hoejre - venstre) / px_mm, "hoejde_mm": mm(hoejde_px),
        "guard_forlaengelse_mm": mm(guard_px),
        "lyszone_v_mm": mm(lz_v), "lyszone_v_til_kant_af_udsnit": lz_v_rand,
        "lyszone_h_mm": mm(lz_h), "lyszone_h_til_kant_af_udsnit": lz_h_rand,
        "cifre_afstand_mm": mm(cifre["afstand_px"]) if cifre else None,
        "cifre_hoejde_mm": mm(cifre["hoejde_px"]) if cifre else None,
        "kontrast": sc, "streg_roed": float(bar_r), "baggrund_roed": float(rum_r), "omvendt": omvendt,
        "tillaeg_luft_mm": mm(tillaeg_luft),
        "cifre_laest": cifre_laest, "cifre_kilde": cifre_kilde,
        # EAN-13 med 0 foran og forlængede streger ved første og sidste ciffer er en UPC-A
        "upca_stil": kode["type"] == "EAN-13" and kode["nummer"].startswith("0") and 4 in guard_idx and 52 in guard_idx,
        "streg_bbox_pt": streg_pt, "linjer": linjer, "tekniske_ignoreret": bool(tekniske),
        "kontur": kontur, "kontur_form": form, "kegle": kegle,
        "naer_linje": None,
        "_tegn": {"rgb": rgb, "px_mm": px_mm, "venstre": venstre, "hoejre": hoejre, "top": top,
                  "bund": bund, "guard_px": guard_px, "lz_v": lz_v, "lz_h": lz_h, "cifre": cifre, "Xpx": Xpx},
    }, None


def Xpx_foreloebig(el, moduler):
    return (el[-1][0] + el[-1][1] - el[0][0]) / moduler


def laes_cifre_tekst(page, rect, k):
    """Cifrene som tekst i PDF'en (når de ikke er omdannet til kurver)."""
    ord_ = page.get_text("words", clip=rect)
    nogle = [w for w in ord_ if re.search(r"\d", w[4])]
    if not nogle:
        return None
    noegle = {0: lambda w: w[0], 2: lambda w: -w[0], 1: lambda w: w[1], 3: lambda w: -w[1]}[k % 4]
    return "".join(re.sub(r"\D", "", w[4]) for w in sorted(nogle, key=noegle)) or None


def laes_cifre_ocr(gray_band, psm_liste=(7, 6)):
    """Cifrene med Tesseract, hvis den findes. Returnerer en liste af læsninger."""
    import shutil as _sh
    if not _sh.which("tesseract"):
        return []
    try:
        import pytesseract
    except ImportError:
        if subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pytesseract", "--break-system-packages"],
                          capture_output=True).returncode and subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "pytesseract"], capture_output=True).returncode:
            return []
        importlib.invalidate_caches()
        import pytesseract
    from PIL import Image
    import numpy as np
    out = []
    h = gray_band.shape[0]
    for maal_h in (56, 80):
        f = maal_h / max(1, h)
        img = Image.fromarray(gray_band).resize((max(1, int(gray_band.shape[1] * f)), max(1, int(h * f))))
        a = np.array(img)
        a = np.where(a < 140, 0, 255).astype("uint8")
        a = np.pad(a, 30, constant_values=255)
        for psm in psm_liste:
            try:
                t = pytesseract.image_to_string(Image.fromarray(a),
                                                config=f"--psm {psm} -c tessedit_char_whitelist=0123456789")
            except Exception:
                continue
            t = re.sub(r"\D", "", t)
            if t:
                out.append(t)
    return out


def render_shape(clip):
    return (int(round(clip.height * DPI_MAAL / 72)), int(round(clip.width * DPI_MAAL / 72)))


# --------------------------------------------------------------------------
# Tjek
# --------------------------------------------------------------------------

def tjek_1d(kode, m, spec, maalestok_status, ramme, linjer, args):
    T = []
    if m.get("omvendt"):
        return [tjek("kontrast", "Farve og kontrast", VURDER,
                     "Koden har lyse streger på mørk bund. Scannere er bygget til mørke streger på lys bund, så "
                     "koden kan sandsynligvis ikke scannes. GS1 v26 har ikke en sætning, der forbyder det for EAN/UPC "
                     "(ikke fundet), så det er en vurdering. De øvrige mål giver ikke mening før det er afklaret.",
                     "omvendt", "mørke streger på lys bund", "GS1 Danmark 2021 s. 2 (sekundær)")]
    fmt = kode["type"]
    mm_ok = maalestok_status != "tvivl"
    ret = RET if mm_ok else VURDER     # ved tvivl om målestokken dømmes mm-krav ikke hårdt
    X = m["X_mm"]
    pct = 100 * X / X_MAAL

    if X_ONDEMAND_MIN - 0.002 <= X < X_MIN - 0.002:
        T.append(tjek("stoerrelse", "Stregkodens størrelse", VURDER,
                      f"X er {X:.3f} mm ({pct:.0f} %). Under 0,264 mm er kun lovligt ved on-demand-print "
                      "(termisk, laser), 0,249 til 0,264 mm (GS1 tabel 5-44 fodnote (*)). For andre trykmetoder er "
                      "0,264 mm minimum. Hvordan der trykkes, ved scriptet ikke.",
                      f"{X:.3f} mm ({pct:.0f} %)", "0,264-0,660 mm (0,249 ved on-demand-print)", "GS1 v26 tabel 5-44 (*)"))
    elif X < X_MIN - 0.002 or X > X_MAX + 0.002:
        T.append(tjek("stoerrelse", "Stregkodens størrelse", ret,
                      f"X er {X:.3f} mm ({pct:.0f} %). GS1 tillader 0,264-0,660 mm (80-200 %).",
                      f"{X:.3f} mm ({pct:.0f} %)", "0,264-0,660 mm", "GS1 v26 tabel 5-44"))
    elif X < X_MAAL * 0.85:
        # 80 % er GS1's minimum. Lovligt, så ingen handling; nævnes kun.
        T.append(tjek("stoerrelse", "Stregkodens størrelse", INGEN_FUND,
                      f"X er {X:.3f} mm ({pct:.0f} %), GS1's minimum er 80 %. Lovligt; koden har lidt mindre "
                      "margin i trykket end en 100 %-kode.",
                      f"{X:.3f} mm ({pct:.0f} %)", "0,264-0,660 mm, normal 0,330", "GS1 v26 tabel 5-44"))
    else:
        T.append(tjek("stoerrelse", "Stregkodens størrelse", INGEN_FUND, f"X er {X:.3f} mm ({pct:.0f} %).",
                      f"{X:.3f} mm ({pct:.0f} %)", "0,264-0,660 mm", "GS1 v26 tabel 5-44"))

    krav_h = spec["faktor"] * X
    h = m["hoejde_mm"]
    h_inde = m.get("hoejde_inden_for_stanse_mm")
    note, maalt_h = "", None
    if h_inde is not None and h_inde < h - 0.3:
        # Stregerne fortsætter ud over stanselinjen; det der skæres af, kommer ikke med på emballagen.
        note = f" Stregerne er {h:.2f} mm i filen, men stanselinjen skærer dem, så kun {h_inde:.2f} mm kommer med."
        maalt_h = f"{h_inde:.2f} mm inden for stanselinjen"
        h = h_inde
    # Kravet regnes af den målte X; dens usikkerhed er ca. 0,2 %.
    if h + TOL_MM < krav_h * 0.998:
        st = ret
        tekst = (f"Stregerne er {h:.2f} mm høje. Ved denne størrelse kræver GS1 mindst {krav_h:.2f} mm "
                 f"({100 * h / krav_h:.0f} % af kravet). GS1 tillader kun lavere kode når det er absolut "
                 "nødvendigt, og så skal den højest mulige højde bruges. Om det er nødvendigt her, kan scriptet "
                 "ikke afgøre." + note)
    elif h < krav_h * 0.998:
        st = VURDER
        tekst = (f"Stregerne er {h:.2f} mm høje, krav {krav_h:.2f} mm. Målt lige under kravet, men inden for målingens "
                 "usikkerhed. Tæt på grænsen." + note)
    else:
        st, tekst = INGEN_FUND, f"Stregerne er {h:.2f} mm høje (krav {krav_h:.2f} mm)." + note
    T.append(tjek("hoejde", "Stregkodens højde", st, tekst, maalt_h or f"{h:.2f} mm", f"mindst {krav_h:.2f} mm",
                  "GS1 v26 tabel 5-44 og 6.3.3.4"))

    g, krav_g = m["guard_forlaengelse_mm"], GUARD_X * X
    if g + TOL_MM < krav_g * 0.6:
        T.append(tjek("guard", "Guard bars forlænget", ret,
                      f"Guard bars (de lange streger i kanterne og midten) går {g:.2f} mm under de andre. "
                      f"De skal gå ca. 5X = {krav_g:.2f} mm ned.", f"{g:.2f} mm", f"ca. {krav_g:.2f} mm",
                      "GS1 v26 5.2.3.2"))
    else:
        T.append(tjek("guard", "Guard bars forlænget", INGEN_FUND, f"Guard bars går {g:.2f} mm ned (ca. 5X).",
                      f"{g:.2f} mm", f"ca. {krav_g:.2f} mm", "GS1 v26 5.2.3.2"))

    for side, navn, idx in (("v", "venstre", 0), ("h", "højre", 1)):
        if side == "h" and kode.get("tillaeg"):
            continue      # afstanden til tillægget tjekkes som SK-17 (samme mellemrum, ellers to fund for én fejl)
        lz, rand = m[f"lyszone_{side}_mm"], m[f"lyszone_{side}_til_kant_af_udsnit"]
        krav = spec["lyszone"][idx] * X
        maalt = f"{'mindst ' if rand else ''}{lz:.2f} mm ({lz / X:.1f}X)"
        if lz + TOL_MM < krav and not rand:
            T.append(tjek(f"lyszone_{side}", f"Lyszone {navn}", ret,
                          f"Der er kun {lz:.2f} mm fri plads {navn} for stregerne, før noget mørkt begynder. "
                          f"GS1 kræver {spec['lyszone'][idx]}X = {krav:.2f} mm.", maalt, f"{krav:.2f} mm",
                          "GS1 v26 tabel 5-44"))
        elif lz < krav and not rand:
            T.append(tjek(f"lyszone_{side}", f"Lyszone {navn}", VURDER,
                          f"Fri plads {navn}: {maalt}, krav {krav:.2f} mm. Målt lige under kravet, men inden for målingens "
                          "usikkerhed. Tæt på grænsen.", maalt, f"{krav:.2f} mm", "GS1 v26 tabel 5-44"))
        else:
            T.append(tjek(f"lyszone_{side}", f"Lyszone {navn}", INGEN_FUND, f"Fri plads {navn}: {maalt}.", maalt,
                          f"{krav:.2f} mm", "GS1 v26 tabel 5-44"))

    if m["cifre_afstand_mm"] is None:
        T.append(tjek("cifre", "Cifre under koden", RET,
                      "Der er ingen cifre lige under stregerne. GS1 kræver at nummeret står i klar tekst "
                      "under koden.", None, "cifre under koden", "GS1 v26 5.2.5"))
    else:
        a, krav_a = m["cifre_afstand_mm"], CIFRE_AFSTAND_X * X
        if a + 0.02 < krav_a:
            T.append(tjek("cifre_afstand", "Luft mellem streger og cifre", ret,
                          f"Cifrene starter {a:.2f} mm under stregerne. GS1 kræver mindst 0,5X = {krav_a:.2f} mm.",
                          f"{a:.2f} mm", f"mindst {krav_a:.2f} mm", "GS1 v26 5.2.5"))
        else:
            T.append(tjek("cifre_afstand", "Luft mellem streger og cifre", INGEN_FUND, f"{a:.2f} mm luft.",
                          f"{a:.2f} mm", f"mindst {krav_a:.2f} mm", "GS1 v26 5.2.5"))
        ch = m["cifre_hoejde_mm"]
        skrift = ch / 0.71
        if skrift + 0.05 < CIFRE_MIN_SKRIFT_MM:
            T.append(tjek("cifre_stoerrelse", "Cifrenes størrelse", VURDER,
                          f"Cifrene er {ch:.2f} mm høje, svarende til ca. {skrift:.1f} mm skrift. GS1 anbefaler "
                          f"mindst {CIFRE_MIN_SKRIFT_MM:g} mm.", f"ca. {skrift:.1f} mm", "mindst 2 mm (anbefaling)",
                          "GS1 v26 4.14 regel 2.a.iii"))
        else:
            T.append(tjek("cifre_stoerrelse", "Cifrenes størrelse", INGEN_FUND,
                          f"Cifrene er {ch:.2f} mm høje (ca. {skrift:.1f} mm skrift).", f"ca. {skrift:.1f} mm",
                          "mindst 2 mm (anbefaling)", "GS1 v26 4.14 regel 2.a.iii"))
    laest, kilde, nr = m.get("cifre_laest"), m.get("cifre_kilde"), kode["nummer"]
    if m["cifre_afstand_mm"] is None:
        pass
    elif laest and gtin14(laest) == gtin14(nr):
        T.append(tjek("cifre_tekst", "Cifrene er de rigtige", INGEN_FUND,
                      f"Cifrene under koden er læst ({kilde}): {laest}. Det er nummeret i koden.", laest, nr, "GS1 v26 5.2.5"))
    elif laest and kilde == "tekst i PDF'en":
        T.append(tjek("cifre_tekst", "Cifrene er de rigtige", RET,
                      f"Cifrene under koden siger {laest}, men koden bærer {nr}. Én af dem er forkert.",
                      laest, nr, "GS1 v26 5.2.5"))
    elif laest and len(laest) == len(nr):
        forskel = sum(1 for a, b in zip(laest, nr) if a != b)
        T.append(tjek("cifre_tekst", "Cifrene er de rigtige", VURDER,
                      f"OCR læser cifrene som {laest}, men koden bærer {nr} ({forskel} ciffer afviger). "
                      "Se efter på billedet: er det OCR der tager fejl, eller står der et forkert ciffer?",
                      laest, nr, "GS1 v26 5.2.5"))
    else:
        T.append(tjek("cifre_tekst", "Cifrene er de rigtige", SE_SELV,
                      f"Cifrene kunne ikke læses maskinelt{(' (OCR læste ' + laest + ')') if laest else ''}. "
                      f"Læs dem på billedet og sammenlign med {nr}.", laest, nr, "GS1 v26 5.2.5"))

    sc = m["kontrast"]
    if m.get("omvendt"):
        T.append(tjek("kontrast", "Farve og kontrast", VURDER,
                      "Koden har lyse streger på mørk bund. Scannere er bygget til mørke streger på lys bund.",
                      "omvendt", "mørke streger på lys bund", "GS1 Danmark 2021 s. 2 (sekundær)"))
    elif sc < KONTRAST_MIN:
        T.append(tjek("kontrast", "Farve og kontrast", VURDER,
                      f"Kontrasten i rødt lys er ca. {sc:.0%}. GS1 kræver samlet kvalitet 1.5 (1.5/06/660), og GS1 "
                      "skriver, at symbolkontrast under 40 % kun får karakter 1. Så kan koden ikke nå 1.5. Scriptet "
                      "måler kun en tilnærmelse og ikke som en verifier, så det er ikke en sikker fejl. Scanneren lyser "
                      "med rødt, så røde, orange og lyse streger forsvinder. Brug sort eller mørkeblå på hvid bund.",
                      f"ca. {sc:.0%}", f"mindst {KONTRAST_MIN:.0%}", "GS1 v26 5.12.5.11.1"))
    elif sc < KONTRAST_OK:
        T.append(tjek("kontrast", "Farve og kontrast", VURDER,
                      f"Kontrasten i rødt lys er ca. {sc:.0%}. Det er over 40 %, men tæt på. Test koden med en scanner.",
                      f"ca. {sc:.0%}", f"helst {KONTRAST_OK:.0%}+ (55 % er ikke fundet i GS1)", "ISO/IEC 15416 (ikke læst)"))
    else:
        T.append(tjek("kontrast", "Farve og kontrast", INGEN_FUND, f"Kontrast i rødt lys ca. {sc:.0%}.",
                      f"ca. {sc:.0%}", f"mindst {KONTRAST_MIN:.0%}", "GS1 v26 5.12.5.11.1"))

    if m.get("cifre_uden_for_stanse"):
        T.append(tjek("cifre_stanse", "Cifre inden for stanselinjen", ret,
                      "Cifrene under koden går ud over stanselinjen og bliver helt eller delvist skåret af.",
                      "uden for stanselinjen", "inden for stanselinjen", "GS1 v26 5.2.5"))
    if m.get("kontur") is not None or ramme is not None:
        import fitz
        b = fitz.Rect(m["streg_bbox_pt"])
        if m.get("kontur") is not None:
            d = kant_afstand_mm(m["kontur"], b)
            hvad = {"rund": "den runde stanselinje", "formet": "stanselinjen (formet etiket)",
                    "rektangulær": "etikettens kant"}[m["kontur_form"]]
        else:
            afst = [(b.x0 - ramme.x0), (ramme.x1 - b.x1), (b.y0 - ramme.y0), (ramme.y1 - b.y1)]
            d, hvad = min(afst) * MM_PR_PT, "etikettens kant"
        if d < -0.5:
            T.append(tjek("kant", "Afstand til kanten", ret,
                          f"Koden går {-d:.1f} mm ud over {hvad} og bliver skåret af.", f"{d:.1f} mm",
                          f"mindst {KANT_MIN_MM:g} mm", "GS1 v26 6.2.3.3"))
        elif d < KANT_MIN_MM:
            T.append(tjek("kant", "Afstand til kanten", VURDER,
                          f"Koden sidder {d:.1f} mm fra {hvad}. GS1 siger, at koden når muligt ikke bør sidde tættere end 8 mm "
                          "på pakkens kant (GS1 v26 6.3.3.3). Det er ikke et ubetinget krav.", f"{d:.1f} mm",
                          f"mindst {KANT_MIN_MM:g} mm", "GS1 v26 6.3.3.3"))
        else:
            T.append(tjek("kant", "Afstand til kanten", INGEN_FUND, f"{d:.1f} mm til {hvad}.", f"{d:.1f} mm",
                          f"mindst {KANT_MIN_MM:g} mm", "GS1 v26 6.3.3.3"))
    else:
        T.append(tjek("kant", "Afstand til kanten", SE_SELV,
                      "Etikettens kant blev ikke fundet i filen. Vurdér afstanden på oversigtsbilledet.",
                      None, f"mindst {KANT_MIN_MM:g} mm", "GS1 v26 6.3.3.3"))

    if linjer:
        beskriv = ", ".join(f"{'stiplet ' if l['stiplet'] else ''}{'teknisk ' if l.get('teknisk') else ''}{l['farve']}"
                            for l in linjer[:5])
        T.append(tjek("linjer", "Linjer gennem koden", VURDER,
                      f"{len(linjer)} streg(er) i filen går gennem koden eller dens lyszoner ({beskriv}). Er det "
                      "en fold-, skære- eller svejselinje, skal koden flyttes. Se dem markeret på billedet.",
                      f"{len(linjer)} linje(r)", "ingen fold, skæring eller svejsning over koden", "GS1 v26 6.2.3.3"))

    if kode.get("tillaeg"):
        luft = m["tillaeg_luft_mm"]
        if luft is not None:
            min_x = TILLAEG_MIN_X.get(fmt)
            lo = (min_x if min_x is not None else 7) * X
            hi = TILLAEG_MAX_X * X
            ok = lo - TOL_MM <= luft <= hi + TOL_MM
            if min_x is None:
                # EAN-8 med tillæg er ikke i tabel 5-44: højst 12X er kendt, mindsteafstanden er ikke
                st = INGEN_FUND if ok else VURDER
                krav = f"højst 12X = {hi:.2f} mm (mindsteafstand ikke angivet for EAN-8)"
                lo_txt = "ikke angivet"
            else:
                st = INGEN_FUND if ok else ret
                if ok and luft < lo:
                    st = VURDER      # lige under kravet, men inden for målingens usikkerhed
                krav = f"{min_x}-12X = {lo:.2f}-{hi:.2f} mm"
                lo_txt = f"{lo:.2f}"
                # Et EAN-13-nummer, der starter med 0, er det samme som et UPC-A (12 cifre). zxing melder det som
                # EAN-13. Er luften mindst 7X men under 9X, afhænger kravet af, om koden er trykt som UPC-A.
                if fmt == "EAN-13" and kode["nummer"].startswith("0") and 7 * X - TOL_MM <= luft < 9 * X - TOL_MM:
                    st = VURDER
                    krav += " (9X hvis koden er et UPC-A, nummeret starter med 0)"
            T.append(tjek("tillaeg", "Tillægskode", st,
                          f"Tillæg {kode['tillaeg']}: {luft:.2f} mm luft til hovedkoden (krav {krav}).",
                          f"{luft:.2f} mm", f"{lo_txt}-{hi:.2f} mm", "GS1 v26 5.2.3.6, tabel 5-44"))

    kegle = m.get("kegle")
    if kegle and not args.diameter:
        T.append(tjek("krumning", "Buet etiket (bøtte eller bæger)", VURDER,
                      f"Stanselinjen er en udfoldet kegle ({kegle['vinkel_grader']:.0f} grader). Går etiketten hele "
                      f"vejen rundt, er emballagen ca. Ø {kegle['d_ved_koden_mm']:.0f} mm der hvor koden sidder "
                      f"(Ø {kegle['d_lille_mm']:.0f} mm i den smalle ende, Ø {kegle['d_stor_mm']:.0f} mm i den brede). "
                      "Bekræft at etiketten går hele vejen rundt (eller oplys diameteren) og kør igen med "
                      "--diameter, så krumningen kan tjekkes.",
                      f"Ø ca. {kegle['d_ved_koden_mm']:.0f} mm ved koden (hvis hele vejen rundt)",
                      "bekræftet diameter", "GS1 v26 6.2.3.2, tabel 6-2"))
    if args.diameter:
        rækker = sorted(MIN_DIAMETER)
        op = next((r for r in rækker if X <= r + 1e-9), rækker[-1])        # første række med X lig eller over
        ned = max([r for r in rækker if r <= X + 1e-9] or [rækker[0]])     # sidste række med X lig eller under
        dmin = MIN_DIAMETER[op].get(fmt)
        dlav = MIN_DIAMETER[ned].get(fmt)
        vinkel = math.degrees(math.asin(min(1.0, m["bredde_mm"] / args.diameter)))
        if dmin:
            mellem = abs(op - ned) > 1e-9   # X ligger mellem to rækker i tabel 6-2 (fx 0,330)
            if args.diameter >= dmin:
                st = INGEN_FUND
            elif mellem and args.diameter >= dlav:
                st = VURDER
            else:
                st = RET
            raekke_tekst = (f"Tabel 6-2 har ingen række for X {X:.3f} mm. Rækkerne ved {ned:.3f} og {op:.3f} mm giver "
                            f"{dlav} og {dmin} mm, så kravet ligger et sted derimellem. " if mellem else "")
            T.append(tjek("krumning", "Rund emballage", st,
                          f"Ved diameter {args.diameter:g} mm og X {X:.3f} mm kræver GS1 mindst {dmin if not mellem else dlav}"
                          f"{(' til ' + str(dmin)) if mellem else ''} mm, når "
                          f"stregerne står parallelt med aksen (picket fence). {raekke_tekst}Vinklen ud til kodens kant "
                          f"er ca. {vinkel:.0f} grader (under 30). Står koden på tværs (ladder), gælder kravet ikke.",
                          f"Ø {args.diameter:g} mm", f"Ø mindst {dmin if not mellem else str(dlav) + ' til ' + str(dmin)} mm",
                          "GS1 v26 6.2.3.2, tabel 6-2"))

    T.append(tjek("tryk", "Printkvalitet og lyszoner på tryk", EFTER_TRYK,
                  "Måles med en stregkode-verifier på prøvetrykket (mindst 1.5/06/660).", None, "1.5/06/660",
                  "GS1 v26 tabel 5-44"))
    return T





def spor_af_kode(doc):
    """Tekst i filen der tyder på en stregkode: ordet EAN/stregkode/barcode eller et gyldigt GTIN."""
    for pno, page in enumerate(doc, start=1):
        try:
            t = page.get_text()
        except Exception:
            continue
        m = re.search(r"\b(EAN|stregkode|barcode|GTIN)\b", t, re.I)
        if m:
            return pno, t[max(0, m.start() - 15): m.end() + 25].replace("\n", " ").strip()
        for g in re.finditer(r"(?<!\d)(\d[ ]?\d{6}[ ]?\d{6})(?!\d)", t):
            d = re.sub(r"\D", "", g.group(1))
            v = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(d[:-1])))
            if (10 - v % 10) % 10 == int(d[-1]) and set(d) != {"0"}:
                return pno, g.group(1)
    return None



def tjek_identitet(koder, afviste, args, doc=None):
    """Tjek der gælder filen som helhed: findes en kode, er nummeret rigtigt."""
    T = []
    retail = [k for k in koder if k["type"] in SPEC]
    if retail and all(k["omvendt"] for k in retail):
        T.append(tjek("kode_findes", "Stregkode findes", VURDER,
                      "Koden kan kun læses med byttede farver (lyse streger på mørk bund). Scannere er bygget til "
                      "mørke streger på lys bund og kan sandsynligvis ikke læse den. Det er en vurdering, ikke et "
                      "fundet forbud i GS1 v26.", "omvendt", "mørke streger på lys bund", "GS1 Danmark 2021 s. 2 (sekundær)"))
    if not retail:
        if afviste:
            a = afviste[0]
            T.append(tjek("kontrolciffer", "Kontrolciffer", RET,
                          f"Der er en {a['type']}-kode ({a['nummer']}), men kontrolcifret er forkert, så scannere "
                          "afviser den. Generér koden forfra fra det rigtige nummer.", a["nummer"],
                          "gyldigt kontrolciffer", "GS1 v26 7.9.1"))
        elif any(k["omvendt"] for k in koder):
            T.append(tjek("kode_findes", "Stregkode findes", VURDER,
                          "Koden kan kun læses med byttede farver (lyse streger på mørk bund). Scannere er bygget til "
                          "mørke streger på lys bund og kan sandsynligvis ikke læse den.", "omvendt",
                          "mørke streger på lys bund", "GS1 Danmark 2021 s. 2 (sekundær)"))
        else:
            andre = ", ".join(sorted({k["type"] for k in koder})) or "ingen"
            spor = spor_af_kode(doc) if doc is not None else None
            if koder:
                T.append(tjek("kode_findes", "Stregkode findes", VURDER,
                              f"Der er ingen EAN- eller UPC-kode, kun {andre}. En vare, der er beregnet til kassen, skal have "
                              "mindst én stregkode (GS1 v26 6.3.1). Om denne del skal scannes i kassen, ved kun du.",
                              andre, "EAN/UPC hvis delen skal scannes", "GS1 v26 6.3.1"))
            elif spor:
                T.append(tjek("kode_findes", "Stregkode findes", VURDER,
                              f"Der står \"{spor[1]}\" på side {spor[0]}, men der er ingen stregkode der kan "
                              f"scannes (andre koder: {andre}). Mangler koden, eller er den en pladsholder uden "
                              "streger? Om delen skal have en kode, ved kun du.", andre, "EAN/UPC der kan scannes",
                              "GS1 v26 6.3.1"))
            else:
                # Mange dele har med vilje ingen kode: forside-etiket hvor koden tiltrykkes,
                # vægtvarer med butiksetiket, kolli, låg, inderpose.
                T.append(tjek("kode_findes", "Stregkode findes", VURDER,
                              f"Der er ingen EAN- eller UPC-kode i filen (andre koder: {andre}). Det er ikke en fejl, "
                              "hvis denne del ikke skal have en (fx en etiket hvor koden tiltrykkes, en vægtvare, "
                              "kolli eller låg). Skal den have en, mangler den.", andre, "EAN/UPC hvis delen "
                              "skal scannes", "GS1 v26 6.3.1"))
    for k in koder:
        if k["type"] in ("ITF", "ITF-14", "ITF14"):
            T.append(tjek("itf", "ITF-14 på forbrugerpakning", VURDER,
                          f"Der er en ITF-14 ({k['nummer']}). GS1 beskriver ITF-14 som en kode til varer, der ikke "
                          "forventes at passere kassen (GS1 v26 5.1.1). Et udtrykkeligt forbud er ikke fundet, så "
                          "tag stilling: skal denne pakke scannes i kassen, skal den have en EAN/UPC.", k["nummer"],
                          "EAN/UPC hvis pakken scannes i kassen", "GS1 v26 5.1.1"))
    for k in retail:
        n = k["nummer"]
        if args.gtin:
            g1, g2 = n.zfill(14), re.sub(r"\D", "", args.gtin).zfill(14)
            T.append(tjek("varenummer", "Varenummer", INGEN_FUND if g1 == g2 else RET,
                          "Nummeret passer med det oplyste." if g1 == g2 else
                          f"Koden bærer {n}, men produktets nummer er oplyst som {args.gtin}. Koden er måske genbrugt fra "
                          "en anden variant. Det er RET, fordi nummeret er oplyst af dig i denne samtale.",
                          n, args.gtin, "Oplyst af brugeren"))
        else:
            T.append(tjek("varenummer", "Varenummer", VURDER,
                          f"Koden bærer {n} med gyldigt kontrolciffer. Om det er det rigtige produkts nummer, kan "
                          "kun kundens varedata sige. Oplys det med --gtin.", n, "produktets GTIN", "Oplyst af brugeren"))
    pr_side = {}
    for k in retail:
        pr_side.setdefault((k["side"], k["nummer"]), []).append(k)
    for (side, n), ks in pr_side.items():
        if len(ks) > 1:
            T.append(tjek("flere_koder", "Samme nummer flere steder", VURDER,
                          f"Nummeret {n} står i {len(ks)} stregkoder på side {side}. Ligger de på samme pakke "
                          "og kan ses samtidig, skal én fjernes eller dækkes.", f"{len(ks)} koder", "én synlig kode",
                          "GS1 v26 6.3.1"))
    numre = {k["nummer"] for k in retail}
    if len(numre) > 1:
        T.append(tjek("forskellige_numre", "Forskellige numre", VURDER,
                      f"Filen har koder med forskellige numre: {', '.join(sorted(numre))}. Hører de til forskellige "
                      "varianter eller sider, er det ikke en fejl. Samme vare må ikke have flere forskellige numre "
                      "(GS1 v26 6.3.1).", ", ".join(sorted(numre)), "ét nummer pr. vare", "GS1 v26 6.3.1"))
    return T


def tjek_2d(k, retail, maalestok_status):
    T = []
    txt = k["raa_tekst"] or ""
    ekstra = k["ekstra"]
    w_mm = (k["bbox_pt"][2] - k["bbox_pt"][0]) * MM_PR_PT
    moduler = None
    if "QR" in k["type"] and str(ekstra.get("Version", "")).isdigit():
        moduler = 17 + 4 * int(ekstra["Version"])
    elif "Matrix" in k["type"] and re.match(r"\d+x\d+", str(ekstra.get("Version", ""))):
        moduler = int(str(ekstra["Version"]).split("x")[1])
    ai01 = (re.search(r"\(01\)(\d{14})|(?:^|\x1d|<GS>)01(\d{14})", txt)
            if not txt.lower().startswith("http") else None)
    url = txt.lower().startswith("http")
    gs1_domaene = url and "gs1" in txt.lower().split("/")[2] if url and txt.count("/") >= 2 else False
    gs1 = (k["symbologi_id"] in ("]Q3", "]d2") or "/01/" in txt or bool(ai01) or gs1_domaene
           or bool(re.match(r"\(\d{2,4}\)", txt)))
    navn = f"{k['type']} {k['nr']}"
    if not gs1:
        T.append(tjek("2d_type", navn, INGEN_FUND, f"Almindelig {k['type']} ({txt[:40]}), ikke en GS1-kode. Ingen GS1-krav.",
                      txt[:40], None, None))
        return T
    if moduler:
        X = w_mm / moduler
        st = INGEN_FUND if X2D_MIN - 0.005 <= X <= X2D_MAX + 0.005 else (RET if maalestok_status != "tvivl" else VURDER)
        T.append(tjek("2d_stoerrelse", f"{navn}: modulstørrelse", st,
                      f"Modulet er ca. {X:.3f} mm. GS1 kræver 0,396-0,990 mm for 2D-koder der scannes i kassen "
                      "(tabel 5-46).", f"{X:.3f} mm", "0,396-0,990 mm", "GS1 v26 tabel 5-46"))
    if txt.lower().startswith("http"):
        m = re.search(r"/01/(\d{14})", txt)
        T.append(tjek("2d_digital_link", f"{navn}: GS1 Digital Link", INGEN_FUND if m else VURDER,
                      "Ukomprimeret Digital Link med varenummer." if m else
                      f"Linket ({txt[:60]}) ser ikke ud som ukomprimeret form med /01/ og 14 cifre. GS1 kræver den "
                      "ukomprimerede form. Formen /01/ er vores læsning af det, så tjek linket.", txt[:60],
                      "https://.../01/<GTIN-14>", "GS1 v26 tabel 5-46"))
        gtin = m.group(1) if m else None
    else:
        gtin = (ai01.group(1) or ai01.group(2)) if ai01 else None
        if not gtin:
            T.append(tjek("2d_gtin", f"{navn}: varenummer", VURDER,
                          "GS1-koden bærer ikke et varenummer (AI 01). Til kassen skal den det.", txt[:40],
                          "AI (01)", "GS1 v26 tabel 5-46"))
    if gtin and retail and all(r["nummer"].zfill(14) != gtin for r in retail):
        T.append(tjek("2d_gtin", f"{navn}: varenummer", RET,
                      f"2D-koden bærer {gtin}, men stregkoden bærer {retail[0]['nummer']}.", gtin,
                      retail[0]["nummer"].zfill(14), "GS1 v26 4.15.1"))
    if not retail:
        T.append(tjek("2d_alene", f"{navn}: uden stregkode", VURDER,
                      "En 2D-kode til kassen skal ifølge GS1 bruges ud over en almindelig EAN/UPC-stregkode i en "
                      "overgangsperiode. GS1 henviser til profiler i afsnit 8 for fremtidig brug uden stregkode, og "
                      "dem er ikke læst, så tag stilling.", "kun 2D", "1D og 2D", "GS1 v26 4.15.4"))
    else:
        r = min(retail, key=lambda r: abs(r["bbox_pt"][0] - k["bbox_pt"][0]))
        c1 = ((r["bbox_pt"][0] + r["bbox_pt"][2]) / 2, (r["bbox_pt"][1] + r["bbox_pt"][3]) / 2)
        c2 = ((k["bbox_pt"][0] + k["bbox_pt"][2]) / 2, (k["bbox_pt"][1] + k["bbox_pt"][3]) / 2)
        b2 = k["bbox_pt"]
        hjoerner = [(b2[0], b2[1]), (b2[2], b2[1]), (b2[0], b2[3]), (b2[2], b2[3])]
        d = max(math.dist(c1, h_) for h_ in hjoerner) * MM_PR_PT      # fjerneste hjørne af 2D-koden
        T.append(tjek("2d_afstand", f"{navn}: afstand til stregkoden", INGEN_FUND if d <= AFSTAND_2D_MM else VURDER,
                      f"Hele 2D-koden ligger inden for {d:.0f} mm fra stregkodens midte (GS1 bør: radius 50 mm "
                      "fra stregkodens midte, inklusive 2D-kodens lyszone). Lyszonen er ikke regnet med i målet, "
                      "så er tallet tæt på 50, er det tæt på grænsen.",
                      f"{d:.0f} mm", "højst 50 mm radius", "GS1 v26 6.3.3.1"))
    return T


def tjek_gs1_128(k):
    w = (max(k["bbox_pt"][2] - k["bbox_pt"][0], k["bbox_pt"][3] - k["bbox_pt"][1])) * MM_PR_PT
    n = len(re.sub(r"[()]", "", k["raa_tekst"] or ""))   # dataets tegn, uden zxing's parenteser
    # Grænsen er 165,10 mm INKLUSIVE lyszoner (mindst 10X hver, 5.4.6.3). Scriptet måler uden lyszoner.
    # Over grænsen uden lyszoner er et sikkert fund. Tæt på grænsen kan lyszonerne vippe det: VURDER.
    if n > GS1_128_MAX_TEGN or w > GS1_128_MAX_MM:
        st = RET
    elif w > GS1_128_MAX_MM - GS1_128_LYSZONE_BUFFER_MM:
        st = VURDER
    else:
        st = INGEN_FUND
    return [tjek("gs1_128", f"GS1-128 {k['nr']}", st,
                 f"{n} tegn og {w:.0f} mm bred uden lyszoner (højst {GS1_128_MAX_TEGN} tegn og 165,10 mm inklusive "
                 "lyszoner; lyszonerne er mindst 10X hver og er ikke regnet med her).",
                 f"{n} tegn, {w:.0f} mm", "48 tegn, 165,10 mm inkl. lyszoner", "GS1 v26 5.4.1")]


# --------------------------------------------------------------------------
# Billeder
# --------------------------------------------------------------------------

def font(size):
    from PIL import ImageFont
    for name in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


ROED, GROEN, BLAA, ORANGE, LILLA = (220, 30, 30), (0, 150, 70), (0, 110, 220), (230, 120, 0), (200, 0, 200)


def tegn_kode(m, tjekliste, kode, sti):
    from PIL import Image, ImageDraw
    t = m["_tegn"]
    img = Image.fromarray(t["rgb"])
    d = ImageDraw.Draw(img)
    pm, X = t["px_mm"], t["Xpx"]
    v, h, top, bund = t["venstre"], t["hoejre"], t["top"], t["bund"]
    st = {x["id"]: x["status"] for x in tjekliste}
    w = max(6, int(pm * 0.16))   # synlig efter nedskalering
    spec = SPEC[kode["type"]]
    for side, idx, x0 in (("v", 0, v), ("h", 1, h)):
        krav = spec["lyszone"][idx] * X
        farve = GROEN if st.get(f"lyszone_{side}") == INGEN_FUND else ROED
        if side == "v":
            d.rectangle([x0 - krav, top, x0, bund], outline=farve, width=w)
        else:
            d.rectangle([x0, top, x0 + krav, bund], outline=farve, width=w)
    d.rectangle([v, top, h, bund], outline=ROED, width=w)
    krav_h = spec["faktor"] * m["X_mm"] * pm
    if st.get("hoejde") != INGEN_FUND:
        y = bund - krav_h
        for x in range(int(v), int(h), int(4 * w)):
            d.line([x, y, min(x + 2 * w, h), y], fill=ORANGE, width=w)
        d.line([v, y, v, top], fill=ORANGE, width=w)
        d.line([h, y, h, top], fill=ORANGE, width=w)
    if t["cifre"] and st.get("cifre_afstand") not in (INGEN_FUND, None):
        d.rectangle([v, bund, h, t["cifre"]["top"]], outline=LILLA, width=w)
    scale = min(1.0, 1100 / img.width)
    img = img.resize((int(img.width * scale), int(img.height * scale)))
    f = font(24)
    linjer = [("Rød: stregerne som de er målt", ROED),
              ("Grøn/rød: den fri plads GS1 kræver på hver side (rød = ikke fri)", GROEN)]
    if st.get("hoejde") != INGEN_FUND:
        linjer.append((f"Orange: så høje skal stregerne være (krav {spec['faktor'] * m['X_mm']:.2f} mm)", ORANGE))
    if t["cifre"] and st.get("cifre_afstand") not in (INGEN_FUND, None):
        linjer.append(("Lilla: for lidt luft mellem streger og cifre", LILLA))
    tal = [f"{kode['type']} {kode['nummer']}" + (f" + {kode['tillaeg']}" if kode.get("tillaeg") else ""),
           f"Størrelse {100 * m['X_mm'] / X_MAAL:.0f} % (X {m['X_mm']:.3f} mm) · højde {m['hoejde_mm']:.2f} mm · "
           f"bredde {m['bredde_mm']:.2f} mm",
           "Vist med stregerne lodret." if kode["retning"] else ""]
    rows = len(linjer) + len([x for x in tal if x])
    out = Image.new("RGB", (max(img.width, 1000), img.height + 34 * rows + 20), "white")
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    y = img.height + 10
    for tekst, farve in linjer:
        d.rectangle([10, y + 5, 32, y + 25], fill=farve)
        d.text((42, y), tekst, fill="black", font=f)
        y += 34
    for tekst in tal:
        if tekst:
            d.text((10, y), tekst, fill="black", font=f)
            y += 34
    out.save(sti)


def tegn_oversigt(page, side, koder, ramme, linjer, sti, konturer=(), indre=()):
    from PIL import Image, ImageDraw
    # Oversigten vises højst 1600 px bred, så den renderes direkte i den størrelse.
    dpi = max(20, int(min(DPI_FIND, 1600 * 72 / max(page.rect.width, page.rect.height))))
    img = Image.fromarray(render(page, dpi))
    s = dpi / 72
    f_ = dpi / DPI_FIND

    def w(x):
        return max(2, round(x * f_))
    d = ImageDraw.Draw(img)
    if konturer:
        for k_ in konturer:
            d.line([(x * s, y * s) for x, y in k_], fill=BLAA, width=w(8))
    elif ramme is not None:
        d.rectangle([ramme.x0 * s, ramme.y0 * s, ramme.x1 * s, ramme.y1 * s], outline=BLAA, width=w(8))
    for k_ in indre:
        (x0_, y0_), (x1_, y1_) = k_
        n_ = max(2, int(math.dist(k_[0], k_[1]) / 6))
        for i in range(0, n_ - 1, 2):
            d.line([((x0_ + (x1_ - x0_) * i / n_) * s, (y0_ + (y1_ - y0_) * i / n_) * s),
                    ((x0_ + (x1_ - x0_) * (i + 1) / n_) * s, (y0_ + (y1_ - y0_) * (i + 1) / n_) * s)],
                   fill=BLAA, width=w(10))
    for l in linjer:
        r = l["rect_pt"]
        d.rectangle([r[0] * s, r[1] * s, r[2] * s, r[3] * s], outline=LILLA, width=w(6))
    f = font(max(14, round(60 * f_)))
    for k in koder:
        b = k["bbox_pt"]
        m = w(12)
        d.rectangle([b[0] * s - m, b[1] * s - m, b[2] * s + m, b[3] * s + m], outline=ROED, width=w(10))
        d.text((b[0] * s, b[1] * s - w(80)), str(k["nr"]), fill=ROED, font=f, stroke_width=w(4), stroke_fill="white")
    head = Image.new("RGB", (img.width, 40), "white")
    ImageDraw.Draw(head).text((10, 8), f"Side {side}. Rød: koder (nummereret). Blå: etikettens kant. "
                              "Lilla: linjer gennem en kode.", fill="black", font=font(20))
    out = Image.new("RGB", (img.width, img.height + 40), "white")
    out.paste(head, (0, 0))
    out.paste(img, (0, 40))
    out.save(sti)


def tegn_raa(page, kode, sti):
    import fitz
    from PIL import Image
    b = kode["bbox_pt"]
    m = 25 / MM_PR_PT
    clip = fitz.Rect(b[0] - m, b[1] - m, b[2] + m, b[3] + m) & page.rect
    Image.fromarray(render(page, DPI_RAA, clip)).save(sti)


# --------------------------------------------------------------------------

IKKE_TJEKKET = [
    "Om koden kan scannes i butikken, og printkvaliteten (1.5/06/660). Kræver en verifier på prøvetrykket (SK-25).",
    "At nummeret er produktets rigtige GTIN, hvis det ikke er oplyst med --gtin.",
    "Om denne del skal have en stregkode (SK-13) og om det er den rigtige kode til varen.",
    "Billedets egne punkter: cifrenes skrift (SK-26), placering efter emballagetype (SK-27), fold om hjørner og flapper (SK-28).",
    "Ikke implementeret endnu: kantafstand højst 100 mm (SK-29), tillæggets højde og lyszone (SK-30), UPC første og sidste ciffer (SK-31), "
    "2D-kodens lyszone og kvalitet (SK-32), tekst ved 2D og DataBar (SK-33), bundmærkning (SK-34).",
    "UPC-A: scanneren melder et UPC-A som EAN-13 med 0 først, så lyszonerne (9X og 9X) og tillægsafstanden (9X) for UPC-A bruges ikke fuldt ud.",
    "ISO/IEC 15416 og GS1 Application Standard Profiles (afsnit 8) er ikke læst. Intet er gennemgået af en fagperson.",
    "Offentlig udgave: kun GS1-laget. Kundepraksis og et bureaus egne skabeloner er taget ud.",
]
USIKKERHED_TEKST = (
    "Størrelser i mm måles på stregerne i en gengivelse ved 1200 dpi (0,021 mm pr. pixel). Scriptet bruger en margin på "
    f"{TOL_MM:g} mm (ca. 2 pixel) på højde, guard bars og lyszoner. På 14 selvlavede vektor-PDF'er afveg målingerne højst "
    "0,01 mm (X højst 0,0002 mm). Ikke afprøvet på billedfiler, drejede koder, farvet baggrund eller trykte filer. "
    "Kontrast er en tilnærmelse og ikke en verifier-måling."
)


def _json(o):
    """numpy-tal og -sandhedsværdier til JSON."""
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(type(o))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fil")
    ap.add_argument("--ud", required=True)
    ap.add_argument("--gtin", help="Produktets GTIN ifølge kunden")
    ap.add_argument("--diameter", type=float, help="Diameter i mm, hvis koden sidder på en rund flade")
    ap.add_argument("--dpi", type=float, help="Opløsning for billedfiler")
    ap.add_argument("--format", help="Etikettens format i mm, fx 100x60. Bruges til at bekræfte målestokken og finde kanten")
    ap.add_argument("--teknisk-magenta", action="store_true",
                    help="Magenta streger og flader er tekniske markeringer, der ikke trykkes")
    args = ap.parse_args()
    global TEKNISK_MAGENTA
    TEKNISK_MAGENTA = args.teknisk_magenta
    t0 = time.time()
    ensure_deps()
    import fitz

    fil = Path(args.fil)
    ud = Path(args.ud)
    ud.mkdir(parents=True, exist_ok=True)
    doc, kildetype = open_document(fil, args.dpi)
    koder, afviste = find_symbols(doc)
    if not any(k["type"] in SPEC for k in koder):
        koder, afviste = find_symbols(doc, rod_lys=True)    # anden runde i rødt lys
    retail = [k for k in koder if k["type"] in SPEC]

    resultat = {"fil": fil.name, "skill_version": SKILL_VERSION, "kildetype": kildetype, "sider": len(doc),
                "koder": [], "fil_tjek": [], "sider_info": {}, "forbehold": [], "billeder": []}
    if "billede" in kildetype:
        resultat["forbehold"].append("Filen er et billede. Mål i mm hviler på den oplyste opløsning, og "
                                     "præcisionen er begrænset af billedets pixels. Etikettens kant og linjer "
                                     "kan ikke findes.")

    side_cache = {}
    for pno in sorted({k["side"] for k in koder} | (set(range(1, min(len(doc), 4) + 1)) if not koder else set())):
        page = doc[pno - 1]
        tegninger = page.get_drawings() if kildetype == "pdf" else []
        kol = format_fra_args(args.format) if kildetype == "pdf" else {}
        fundne = rammer(page, kol.get("format_mm"), tegninger)
        ml = maalestok(page, kol, fundne) if kildetype == "pdf" else {"status": "antaget", "tekst": kildetype}
        side_cache[pno] = (page, tegninger, kol, fundne, ml)
        resultat["sider_info"][pno] = {"format_mm": kol.get("format_mm"), "maalestok": ml,
                                       "rammer_fundet": len(fundne)}

    resultat["fil_tjek"] = tjek_identitet(koder, afviste, args, doc if kildetype == "pdf" else None)

    for k in koder:
        page, tegninger, kol, fundne, ml = side_cache[k["side"]]
        entry = {"nr": k["nr"], "type": k["type"], "nummer": k["nummer"], "tillaeg": k["tillaeg"], "side": k["side"],
                 "retning_grader": k["retning"], "maal": None, "tjek": []}
        if k["type"] in SPEC:
            m, fejl = maal_1d(page, k, SPEC[k["type"]], tegninger, fundne, kol.get("format_mm"))
            if m is not None and m.get("upca_stil"):
                k["type"] = entry["type"] = "UPC-A"
            if m is not None and ml["status"] != "bekraeftet" and not (0.2 <= m["X_mm"] <= 1.0):
                ml = {"status": "tvivl", "tekst": f"X er målt til {m['X_mm']:.3f} mm, og målestokken kunne ikke "
                      "bekræftes. PDF'en er sandsynligvis ikke i 1:1, så mål i mm kan ikke bruges."}
                resultat["sider_info"][k["side"]]["maalestok"] = ml
            if m is None:
                entry["tjek"].append(tjek("maaling", "Måling", IKKE_MAALT, fejl))
            else:
                ramme = next((f for f in fundne if f.contains(fitz.Rect(m["streg_bbox_pt"]).tl)), None)
                if ramme is None and fundne:
                    ramme = min(fundne, key=lambda f: f.width * f.height)
                X = m["X_mm"]
                linjer = [{kk: vv for kk, vv in l.items() if not kk.startswith("_")} for l in m["linjer"]]
                entry["tjek"] = tjek_1d(k, m, SPEC[k["type"]], ml["status"], ramme, linjer, args)
                entry["maal"] = {kk: (r2(v, 4) if kk == "X_mm" else r2(v)) if isinstance(v, float) else v
                                 for kk, v in m.items() if not kk.startswith("_")
                                 and kk not in ("streg_bbox_pt", "linjer", "kontur", "kegle", "naer_linje")}
                entry["_kontur"] = m.get("kontur")
                entry["_indre"] = (m.get("naer_linje") or (None, None, None))[2]
                if m.get("kegle"):
                    entry["maal"]["kegle"] = {kk: r2(v, 1) for kk, v in m["kegle"].items()}
                entry["maal"]["stoerrelse_pct"] = r2(100 * X / X_MAAL, 1)
                entry["maal"]["krav_hoejde_mm"] = r2(SPEC[k["type"]]["faktor"] * X)
                entry["linjer"] = linjer
                tegn_kode(m, entry["tjek"], k, ud / f"kode_{k['nr']}.png")
                resultat["billeder"].append(f"kode_{k['nr']}.png")
            tegn_raa(page, k, ud / f"kode_{k['nr']}_raa.png")
            resultat["billeder"].append(f"kode_{k['nr']}_raa.png")
        elif k["type"] in ("QR Code", "Data Matrix", "QRCode", "DataMatrix", "Micro QR Code"):
            entry["tjek"] = tjek_2d(k, retail, side_cache[k["side"]][4]["status"])
            tegn_raa(page, k, ud / f"kode_{k['nr']}_raa.png")
            resultat["billeder"].append(f"kode_{k['nr']}_raa.png")
        elif k["type"] in ("Code 128", "Code128") and (k["symbologi_id"] == "]C1"
                                                      or re.match(r"\(\d{2,4}\)", k["raa_tekst"] or "")):
            entry["tjek"] = tjek_gs1_128(k)
        resultat["koder"].append(entry)

    for pno, (page, tegninger, kol, fundne, ml) in side_cache.items():
        sk = [k for k in koder if k["side"] == pno]
        alle_linjer = [l for e in resultat["koder"] if e["side"] == pno for l in e.get("linjer", [])]
        ramme = fundne[0] if len(fundne) == 1 else (min(fundne, key=lambda f: f.width * f.height) if fundne else None)
        konturer = [e["_kontur"] for e in resultat["koder"] if e["side"] == pno and e.get("_kontur")]
        indre = [e["_indre"] for e in resultat["koder"] if e["side"] == pno and e.get("_indre")]
        tegn_oversigt(page, pno, sk, ramme, alle_linjer, ud / f"oversigt_s{pno}.png", konturer, indre)
        resultat["billeder"].append(f"oversigt_s{pno}.png")
        if ml["status"] != "bekraeftet":
            resultat["forbehold"].append(f"Side {pno}: {ml['tekst']}")

    alle = resultat["fil_tjek"] + [t for e in resultat["koder"] for t in e["tjek"]]
    resultat["opsummering"] = {s: sum(1 for t in alle if t["status"] == s)
                               for s in (RET, VURDER, SE_SELV, EFTER_TRYK, IKKE_MAALT, INGEN_FUND)}
    # Tjekpunkter uden fund og tjekpunkter, der aldrig er tjekket. INGEN_FUND er ikke en godkendelse.
    resultat["ingen_fund_paa"] = sorted({f"{t['tjekpunkt']} {t['navn']}" for t in alle
                                         if t["status"] == INGEN_FUND and t.get("tjekpunkt")})
    resultat["ikke_tjekket"] = IKKE_TJEKKET + [f"{t['tjekpunkt'] or t['id']} {t['navn']}: {t['tekst']}"
                                               for t in alle if t["status"] == IKKE_MAALT]
    resultat["usikkerhed"] = USIKKERHED_TEKST
    resultat["tid_s"] = round(time.time() - t0, 1)
    for e in resultat["koder"]:
        e.pop("_kontur", None)
        e.pop("_indre", None)
    (ud / "maaling.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=1, default=_json), encoding="utf-8")

    print(f"{fil.name}: {len(koder)} kode(r) på {len(doc)} side(r), {resultat['tid_s']} s (skill version {SKILL_VERSION})")
    for t in resultat["fil_tjek"]:
        if t["status"] != INGEN_FUND:
            print(f"  [{t['status']}] {t.get('tjekpunkt') or ''} {t['navn']}: {t['tekst']}")
    for e in resultat["koder"]:
        mm = e["maal"] or {}
        print(f"  Kode {e['nr']}: {e['type']} {e['nummer']} side {e['side']}"
              + (f" · X {mm.get('X_mm')} mm ({mm.get('stoerrelse_pct')} %) · højde {mm.get('hoejde_mm')} mm" if mm else ""))
        for t in e["tjek"]:
            if t["status"] not in (INGEN_FUND, EFTER_TRYK):
                print(f"    [{t['status']}] {t.get('tjekpunkt') or ''} {t['navn']}: {t['maalt'] or ''} "
                      f"{('(krav ' + t['krav'] + ')') if t['krav'] else ''}")
    print("  Ingen fund på de tjekkede punkter: " + (", ".join(resultat["ingen_fund_paa"]) or "ingen") +
          ". Det er ikke en godkendelse. Se 'ikke_tjekket' i maaling.json.")
    for f in resultat["forbehold"]:
        print(f"  Forbehold: {f}")
    print(f"Filer i {ud}: maaling.json, " + ", ".join(resultat["billeder"]))


if __name__ == "__main__":
    main()
