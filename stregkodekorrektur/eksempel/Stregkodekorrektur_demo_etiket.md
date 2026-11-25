# Stregkodekorrektur: demo_etiket.pdf
2026-11-25 · skill version 2.1 (offentlig udgave) · ikke gennemgået af en ekspert

*Eksempel på en rigtig kørsel. Etiketten er opdigtet og lavet med `testfiler/gen_demo.py`. Tal og statusser kommer fra `maaling.json` i samme mappe. Teksten er skrevet af Claude efter skabelonen i `references/levering.md`.*

## Koden
EAN-13 2000000000015 · side 1 · størrelse 100 % (X 0,330 mm) · højde 17,40 mm · bredde 31,35 mm

## Målestok og usikkerhed
Det oplyste format 100 x 60 mm passer med en ramme på siden, så PDF'en er i 1:1. Målingen kan være ca. 0,05 mm forkert. På 14 selvlavede vektor-PDF'er afveg målingerne højst 0,01 mm. Den er ikke afprøvet på billedfiler, drejede koder, farvet baggrund eller trykte filer.

## Skal rettes
### Stregkodens højde (SK-02)
Målt: 17,40 mm · Krav: mindst 22,85 mm · Kilde: GS1 v26 tabel 5-44 (K-02) · Usikkerhed: 0,05 mm

Koden har 76 % af den højde, GS1 kræver ved denne størrelse. Selv med målingens usikkerhed er den for lav. GS1 tillader kun en lavere kode, når det er absolut nødvendigt. Gør koden højere uden at ændre bredden. Der er plads over den.

## Tag stilling til
### Afstand til kanten (SK-11)
Målt: 5,0 mm · Krav: mindst 8 mm, "når muligt" · Kilde: GS1 v26 6.3.3.3 (K-09)

Koden sidder 5,0 mm fra etikettens højre kant. GS1 siger, at den når muligt ikke bør sidde tættere end 8 mm. Det er ikke et ubetinget krav. Kan koden flyttes 3 mm mod venstre, er punktet løst.

### Varenummer (VD-01)
Koden bærer 2000000000015 med gyldigt kontrolciffer. Om det er produktets rigtige nummer, kan kun varedata sige. Oplys det med `--gtin`.

## Kan først tjekkes på prøvetryk
Printkvalitet og lyszoner på tryk med en verifier (SK-25).

## Set på billedet
Vurdering, ikke måling: Koden sidder nederst til højre på etiketten. Cifrene er i en almindelig skrift, ikke fede eller sammenpressede. Der er kun én kode på siden.

## Ingen fund på de tjekkede punkter
Størrelse (SK-01), guard bars (SK-03), lyszoner (SK-04), luft mellem streger og cifre (SK-06), cifrenes størrelse (SK-07), cifrene er de rigtige (SK-08), farve og kontrast (SK-10). Det er ikke en godkendelse.

## Ikke tjekket
- Om koden kan scannes i butikken. Det kræver en verifier på prøvetrykket.
- Om nummeret er produktets rigtige GTIN.
- Om denne del skal have en stregkode, og placering efter emballagetype.
- Punkterne SK-29 til SK-34, som ikke er bygget ind i scriptet endnu.
