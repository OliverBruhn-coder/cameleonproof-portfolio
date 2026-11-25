---
type: policy
tags: [tjekpunkter, stregkode, gs1]
date: 2026-11-22
language: da
---

# Tjekpunkter: Stregkode

Udkast 2026-11-22. Hvert tjekpunkt peger på et kilde-ID i `kilder.md`. Intet er bekræftet af en ekspert.
Testfil-kolonnen peger på fejlvarianter i et privat testkorpus med rigtige designs. De er ikke med i denne offentlige udgave. De offentlige, opdigtede testfiler ligger i `../testfiler`.

Typer: **måles** (script), **vurderes** (skill med billedet), **menneske** (kræver viden udefra).
Statusser: `RET`, `VURDER`, `SE_SELV`, `EFTER_TRYK`, `IKKE_MAALT` og `INGEN_FUND`.

## Regler for hele området

- Intet tjekpunkt giver "OK", "i orden" eller "godkendt". Et tjek, der ikke finder noget, rapporteres som `INGEN_FUND`, altså "ingen fund på de tjekkede punkter", og de ikke tjekkede punkter listes.
- `RET` bruges kun, når D-01 har et tal eller en ordlyd ("skal"), og målingen er sikker, også med målingens usikkerhed. Hvor kilden kun siger "bør", "når muligt" eller er en vejledning, eller målingen er en tilnærmelse, bruges `VURDER`.
- **VD-01 (varenummer) sammenligner med det GTIN, brugeren oplyser.** Det er ikke et GS1-krav. Et andet nummer end det oplyste er `RET`, fordi nummeret er oplyst af brugeren.
- Står teksten som kurver, kan cifrene ikke læses som tekst. Tjek, der kræver tekst, giver så `SE_SELV` eller `IKKE_MAALT` og aldrig et gæt.
- Hvad der aldrig bliver tjekket af scriptet står i hver rapport under "Ikke tjekket" (se bunden af denne fil).

## A. GS1-krav (D-01), implementeret i scriptet

| ID | Tjekpunkt | Kilde-ID | Type | Fejl hvis | Status ved fund | Testfil |
|---|---|---|---|---|---|---|
| SK-01 | Stregkodens størrelse (X) er mellem 0,264 og 0,660 mm (80 til 200 %). Ved on-demand-print er 0,249 til 0,264 mm lovligt | K-01 | måles | X under 0,249 eller over 0,660 mm | `RET`. X fra 0,249 til 0,264 mm er `VURDER` (lovligt ved on-demand-print, K-01 fodnote (*)). `VURDER`, hvis målestokken er i tvivl. 80 til 85 % er lovligt og giver `INGEN_FUND` med en note | V1, V2. Selvlavede: syn3_00 (X 0,255 giver `VURDER`), syn3_01 (X 0,240 giver `RET`) |
| SK-02 | Stregehøjden er mindst 69,24 x X (EAN-13, UPC-A, UPC-E) eller 55,24 x X (EAN-8). Skærer stanselinjen stregerne, tæller kun delen inden for | K-02, K-03 | måles | Målt højde er under kravet med mere end målingens usikkerhed | `RET`. K-03 tillader afkortning, når den er "absolut nødvendig", og det kan intet script afgøre. Skillen spørger derfor, om den lave højde er aftalt, men dommen ændres ikke af svaret | V13, V14 |
| SK-03 | Guard bars er forlænget ca. 5X nedad | K-04 | måles | Forlængelsen er under 60 % af 5X | `RET` | V15 |
| SK-04 | Lyszoner er mindst 11X og 7X (EAN-13), 7X og 7X (EAN-8), 9X og 9X (UPC-A), 9X og 7X (UPC-E) | K-05 | måles | Fri, lys plads er under kravet | `RET` | V3, V4 |
| SK-05 | Nummeret står i klar tekst under koden | K-06 | måles | Der er ingen cifre lige under stregerne | `RET` | V8. V19 (ladder-kode) giver også `RET`, og det er ikke afklaret, om det er en falsk alarm |
| SK-06 | Mindst 0,5X luft mellem cifrene og stregerne | K-06 | måles | Mindre luft | `RET` | V17 |
| SK-07 | Cifrene er mindst 2 mm i skriftstørrelse | K-07 | måles | Under 2 mm | `VURDER` (kilden siger "bør") | V31 |
| SK-08 | Cifrene er det nummer, koden bærer | K-06 | måles (tekst i PDF'en) eller vurderes (OCR) | Cifrene afviger fra koden | `RET` ved tekst i PDF'en. `VURDER` ved OCR. `SE_SELV`, hvis de ikke kunne læses | V7 |
| SK-09 | Cifrene ligger inden for stanselinjen | K-06 (afledt: skåret af cifre er ikke vist) | måles | Cifrene går ud over stanselinjen | `RET` | ikke lavet |
| SK-10 | Mørke streger på lys bund. Symbolkontrast i rødt lys mindst 40 % (nedre grænse for karakter 2) | K-08 | måles | Kontrast under 40 %, eller lyse streger på mørk bund | `VURDER`. Scriptets kontrast er en tilnærmelse og ikke en verifier-måling. 40 til 55 % er også `VURDER` (55 % er ikke fundet i D-01) | V5, V6 |
| SK-11 | Afstand til emballagens kant er mindst 8 mm (når muligt) | K-09 | måles | Koden sidder tættere end 8 mm på kanten | `VURDER`. `RET` kun hvis koden går ud over stanselinjen eller kanten og bliver skåret af (K-10: aldrig på kanter og stanselinjer) | W1 |
| SK-12 | Ingen fold-, skære- eller svejselinje gennem koden eller dens lyszoner | K-10 | måles (linjer i filen) og vurderes | Linje krydser koden | `VURDER`, fordi scriptet ikke kan se, hvad linjen er | V9, V18 |
| SK-13 | Der er en stregkode, hvis varen skal scannes i kassen | K-11 | måles (findes kode?) og menneske | Ingen kode eller en pladsholder uden streger | `VURDER`. Om delen skal have en kode, ved kun grafikeren | V10 |
| SK-14 | Koden har gyldigt kontrolciffer (SHALL i 5.2.2.1 til 5.2.2.3, beregning i 7.9.1) | K-21 | måles | Kontrolcifret passer ikke | `RET` | V26 |
| SK-15 | Ingen ITF-14 på en forbrugerpakning | K-12 | måles | Koden er en ITF-14 | `VURDER`. Kilden er beskrivende ("ikke forventet at passere kassen"), ikke et forbud | V11 |
| SK-16 | Ikke to forskellige GTIN på samme vare. Ikke to synlige koder med samme nummer | K-11, K-17 | måles og vurderes | Samme nummer flere gange, eller flere forskellige numre | `VURDER`. Scriptet ved ikke, om koderne sidder på samme pakke | V12 |
| SK-17 | Tillæg (EAN-2 og EAN-5): luft til hovedkoden mindst 7X (EAN-13, UPC-E) eller 9X (UPC-A), højst 12X | K-13 | måles | Luften ligger uden for grænserne. EAN-8: mindsteafstand ikke angivet i tabel 5-44 | `RET` (EAN-13, UPC-A, UPC-E). `VURDER` (EAN-8) | V16 (lovligt tillæg, skal give `INGEN_FUND`). Selvlavede: syn3_02 (EAN-13 + 2, 8X, ingen fund), syn3_03 (6X, `RET`), syn3_04 (UPC-A + 2, 8X: `VURDER`, se note), syn3_05 (10X, ingen fund). Note: zxing melder et UPC-A som EAN-13 med 0 først, så UPC-A tjekkes som EAN-13 (9X mellem 7X og 9X giver `VURDER`). Lyszoner for UPC-A (9X og 9X) bruges derfor ikke |
| SK-18 | Rund flade: diameter mindst efter tabel 6-2 | K-14 | måles (kræver oplyst diameter) | Diameter under tabellens mindste ved denne X | `RET` under den lavere rækkes værdi. `VURDER` mellem to rækker (fx X 0,330, hvor tabellen ikke har en række). Står koden på tværs (ladder), gælder kravet ikke | observationssæt i det gamle projekt, ikke kørt her |
| SK-19 | GS1 2D-kode: modul 0,396 til 0,990 mm | K-15 | måles | Modul uden for området | `RET`. `VURDER`, hvis målestokken er i tvivl | V23 |
| SK-20 | GS1 Digital Link er i ukomprimeret form med /01/ og 14 cifre | K-16 | måles | Linket er ikke i den form | `VURDER` (formen er skillens læsning af "ukomprimeret") | V22 |
| SK-21 | 2D-koden bærer samme GTIN som stregkoden | K-17 | måles | Forskelligt GTIN. Intet GTIN (AI 01) i en GS1 2D-kode | `RET` ved forskelligt GTIN. `VURDER` hvis intet GTIN | V24 |
| SK-22 | En 2D-kode til kassen står sammen med en EAN/UPC | K-18 | måles | Kun 2D | `VURDER`. K-18 henviser til profiler i afsnit 8, der ikke er læst | V20 |
| SK-23 | 2D-koden ligger inden for 50 mm radius fra stregkodens centrum | K-19 | måles | Længere væk | `VURDER` (kilden siger "bør") | V21 |
| SK-24 | GS1-128: højst 48 datategn og 165,10 mm inklusive lyszoner | K-20 | måles | Flere end 48 tegn, eller bredden uden lyszoner alene er over 165,10 mm (sikkert fund). Er bredden uden lyszoner mellem 152 og 165,10 mm, kan koden blive for lang med lyszoner (tvivl) | `RET` over grænsen. `VURDER` i tvivlsområdet, fordi scriptet ikke måler lyszonerne | V25 |
| SK-25 | Printkvalitet mindst 1.5/06/660 og lyszoner på det trykte | K-08, K-05 | menneske (verifier) | Kan kun måles på prøvetrykket | `EFTER_TRYK` | ingen |

## B. Det billedet skal afgøre (GS1-krav, ikke målt af scriptet)

| ID | Tjekpunkt | Kilde-ID | Type | Fejl hvis | Status ved fund | Testfil |
|---|---|---|---|---|---|---|
| SK-26 | Cifrenes skrift er tydelig: ikke fed, kursiv, lys eller smal, mellemrum ikke formindsket | K-07 | vurderes | Skriften er fed, kursiv, lys eller smal | `SE_SELV` (kilden siger "bør ikke") | ikke lavet (V28 til V30 har fejlen, men scriptet kan ikke se den; skillen skal afgøre det på billedet) |
| SK-27 | Placering efter emballagetype: nederste højre kvadrant af bagsiden, ikke på hals af flaske eller kande, osv. | K-22 | vurderes | Placeringen afviger fra typens regel | `SE_SELV` | W2 |
| SK-28 | Koden er på en plan flade: ikke rundt om hjørne, ikke under en flap, ikke over ru overflade | K-10 | vurderes | Koden sidder på en af disse | `SE_SELV` | ikke lavet |

## C. Varedata (ikke GS1)

| ID | Tjekpunkt | Kilde-ID | Type | Fejl hvis | Status ved fund | Testfil |
|---|---|---|---|---|---|---|
| VD-01 | Koden bærer det GTIN, brugeren har oplyst for produktet | K-35 | måles | Koden bærer et andet nummer end det oplyste | `RET`, fordi nummeret er oplyst af brugeren. Uden oplyst nummer: `VURDER` med spørgsmålet | `tests/test_maal.py` |

## D. Fundet i D-01, men ikke implementeret i scriptet

Kilden er læst. Intet script måler dem endnu. De står i rapporten under "Ikke tjekket", eller grafikeren ser selv efter.

| ID | Tjekpunkt | Kilde-ID | Type | Fejl hvis | Status ved fund | Testfil |
|---|---|---|---|---|---|---|
| SK-29 | Kantafstand højst 100 mm (når muligt) | K-09 | måles | Koden sidder længere end 100 mm fra pakkens nærmeste kant. Scriptet kender etikettens kant, ikke pakkens panelkant, og ville give falske fund på store emballager | `VURDER` (ikke implementeret) | ikke lavet |
| SK-30 | Tillæg: højde ikke over hovedkodens, 5X lyszone til højre for tillægget, cifrene over tillægget i samme højde og med 0,5X luft | K-13, K-06 | måles | Tillægget er højere, har for lidt lyszone eller cifrene står forkert. Scriptet måler kun afstanden til hovedkoden | `VURDER` (ikke implementeret) | ikke lavet |
| SK-31 | UPC-A og UPC-E: første og sidste ciffer formindsket til højst 4 moduler bredde, 5 moduler (UPC-E 3) fra yderste guard bar | K-06 | måles | Cifrene afviger. Kun relevant for UPC. Kilden siger "bør" | `VURDER` (ikke implementeret) | ikke lavet |
| SK-32 | 2D-kode: lyszone 1X (DataMatrix) eller 4X (QR) på alle sider, kvalitet 1.5/12/660 | K-15 | måles | Lyszonen er for lille. Scriptet måler modulstørrelse, ikke lyszonen | `VURDER` (ikke implementeret) | ikke lavet |
| SK-33 | HRI ved GS1 DataBar og 2D: (01) og 14 cifre, undtagen når 2D står ved siden af en lineær kode med HRI eller er til forbrugerengagement (K-24) | K-24 | vurderes | Teksten mangler eller er forkert, og ingen af undtagelserne gælder. Teksten ved 2D-koder kan ikke knyttes til koden sikkert | `SE_SELV` (ikke implementeret) | ikke lavet |
| SK-34 | Bundmærkning på store, tunge varer (over 13 kg eller to mål over 450 mm) | K-25 | menneske | Kræver viden om varen | `VURDER` (ikke implementeret) | ikke lavet |

## Åbne punkter, før tjekpunkterne kan bruges

1. **Måleusikkerhed** (SK-02, SK-04, SK-06): se SKILL.md, "Målingens usikkerhed", for hvordan den er fundet, og hvad der ikke er afprøvet.
2. **Afkortet højde** (SK-02): om en aftalt afvigelse skal stå som fund eller kun som note, er brugerens valg. Scriptet giver `RET` på GS1's tal.
3. **Kontrast** (SK-10): om `RET` skal bruges under en bestemt grænse, kræver en verifier-sammenligning.
4. **Kantafstand og fold** (SK-11): om 8 mm også gælder folder inde på pakken, er ikke afgjort i GS1 v26.
5. **2D uden 1D** (SK-22): afsnit 8 (Application Standard Profiles) skal læses.

Godkendt af / dato: ikke godkendt

