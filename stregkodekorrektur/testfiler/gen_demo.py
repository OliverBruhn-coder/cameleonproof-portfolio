"""Opdigtet etiket til demoen: en EAN-13, der er for lav, og som sidder tæt på kanten.

Etiketten er 100 x 60 mm (stanselinjen er en tynd grå ramme) på en side på 120 x 80 mm.
Nummeret 2000000000015 er fiktivt (præfiks 20 er begrænset cirkulation). Produktnavnet er opdigtet.

Facit:
- X = 0,330 mm (100 %): ingen fund.
- Højde 17,40 mm. Kravet ved X 0,330 er 69,24 x 0,330 = 22,85 mm: RET.
- Stregerne sidder 5,0 mm fra etikettens højre kant. GS1 siger "når muligt" mindst 8 mm: VURDER.

Kør fra denne mappe: python gen_demo.py
"""
import fitz
import numpy as np
import zxingcpp

MM = 72 / 25.4
GTIN = "2000000000015"
X, HOEJDE = 0.330, 17.40
ETIKET = (10.0, 10.0, 110.0, 70.0)          # x0, y0, x1, y1 i mm på siden
OX = ETIKET[2] - 5.0 - 95 * X               # stregerne slutter 5 mm fra højre kant
OY = 40.0
GUARDS = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))


def main(sti="demo_etiket.pdf"):
    doc = fitz.open()
    pg = doc.new_page(width=120 * MM, height=80 * MM)
    x0, y0, x1, y1 = (v * MM for v in ETIKET)
    pg.draw_rect(fitz.Rect(x0, y0, x1, y1), color=(0.6, 0.6, 0.6), width=0.5)
    pg.insert_text(fitz.Point(16 * MM, 22 * MM), "Opdigtet produkt", fontsize=16, fontname="helv")
    pg.insert_text(fitz.Point(16 * MM, 29 * MM), "Eksempel til demo · 250 g", fontsize=9, fontname="helv")
    pg.insert_text(fitz.Point(16 * MM, 62 * MM), "Kun til test. Ikke en rigtig vare.", fontsize=7, fontname="helv")

    moduler = np.array(zxingcpp.write_barcode(zxingcpp.BarcodeFormat.EAN13, GTIN, width=95, height=1,
                                              quiet_zone=0))[0] < 128
    i = 0
    while i < 95:
        if moduler[i]:
            j = i
            while j < 95 and moduler[j]:
                j += 1
            ekstra = 5 * X if any(k in GUARDS for k in range(i, j)) else 0
            pg.draw_rect(fitz.Rect((OX + i * X) * MM, OY * MM, (OX + j * X) * MM, (OY + HOEJDE + ekstra) * MM),
                         color=None, fill=(0, 0, 0))
            i = j
        else:
            i += 1
    y = (OY + HOEJDE + 5 * X + 0.5 * X + 2.2) * MM
    fs = 2.8 * MM
    pg.insert_text(fitz.Point((OX - 3.5) * MM, y), GTIN[0], fontsize=fs, fontname="helv")
    pg.insert_text(fitz.Point((OX + 3 * X) * MM, y), GTIN[1:7], fontsize=fs, fontname="helv")
    pg.insert_text(fitz.Point((OX + 50 * X) * MM, y), GTIN[7:], fontsize=fs, fontname="helv")
    doc.save(sti)
    print(sti)


if __name__ == "__main__":
    main()
