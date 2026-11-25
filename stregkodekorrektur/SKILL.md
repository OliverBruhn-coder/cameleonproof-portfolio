---
name: stregkodekorrektur
description: Stregkodekorrektur af emballagedesign. Måler EAN/UPC-stregkoden (og GS1 QR, DataMatrix, GS1-128) i en PDF på stregerne selv og tjekker størrelse, højde, lyszoner, cifre, kontrast, kantafstand, fold- og stanselinjer og varenummer mod GS1 General Specifications v26 og angiver målingens usikkerhed. Brug når nogen uploader et design, en etiket eller en korrektur-PDF og spørger til stregkoden, EAN, GTIN, varenummeret, om koden kan scannes, eller bare beder om korrektur af koden. Version 2.1, offentlig udgave med kun GS1-laget.
---

# Stregkodekorrektur

Version 2.1. Brugeren er grafiker eller korrekturlæser på et designbureau. Svaret skal sige tre ting: hvad skal rettes, hvad skal hun selv tage stilling til, og hvad kan skillen ikke tjekke.

**Status.** Tjekpunkterne er bygget på GS1 General Specifications v26 (se `references/kilder.md`), men ingen ekspert har gennemgået dem. Det står i dommen. Intet her er juridisk rådgivning.

**Offentlig udgave.** Kun GS1-laget er med. Kundepraksis og et bureaus egne skabeloner og arbejdsmåder er taget ud. Vises som arbejdsprøve. Alle rettigheder forbeholdes.

**Arbejdsdeling.** `scripts/maal.py` måler. Det er den eneste kilde til tal i mm og til statusser. Du ser på billederne, spørger efter det der mangler, og forklarer. En status fra scriptet står som den er. Ser du noget på billedet, der taler imod, skriver du det ved siden af som "set på billedet".

**Hvorfor ingen "godkendt".** En korrektur kan kun sige, at der ikke er fundet noget på de tjekkede punkter. `INGEN_FUND` betyder det og ikke mere. Skriv altid, hvad der ikke blev tjekket. Brug aldrig "godkendt", "OK" eller "i orden" om koden eller filen.

## 1. Mål

```bash
python <skill>/scripts/maal.py "<fil>" --ud <arbejdsmappe>/maaling [--gtin <produktets GTIN>] [--diameter 73] [--format 100x60] [--teknisk-magenta]
```

`<skill>` er mappen med denne fil. Billedfiler kræver `--dpi`. Scriptet installerer selv det, det mangler. Fejler det, så vis fejlen og stop.

Færdig når `maaling.json` er læst: `fil_tjek`, `tjek` for hver kode (hvert tjek har `tjekpunkt`, `kilde_id`, `lag` (GS1 eller varedata) og ofte `usikkerhed`), `sider_info` (oplyst format og målestok), `forbehold`, `ingen_fund_paa`, `ikke_tjekket` og `usikkerhed`.

Flere filer i samme samtale: kør scriptet på hver fil, og saml spørgsmålene fra trin 3 i én besked.

## 2. Se

Guard bars ses bedst på `kode_<N>_raa.png`, fordi den røde ramme på oversigten dækker dem. Åbn `oversigt_s<N>.png` og for hver kode `kode_<N>.png` og `kode_<N>_raa.png`. Gå `references/se-efter.md` igennem for hver kode. Er der ingen kode (`kode_findes`), så se efter på oversigten, om der står en hvid boks, en pladsholder eller en kode scriptet ikke kunne læse.

Færdig når hvert punkt i se-efter.md har et svar (ingen bemærkning, problem eller kan ikke ses), og hvert `SE_SELV`-tjek og hvert `VURDER` på `cifre_tekst` er afgjort ved at læse cifrene på billedet. "Ingen bemærkning" gælder kun det ene punkt, aldrig hele koden.

I dommen står kun de punkter, hvor du ser et problem eller en tvivl. De øvrige samles i én linje: "Set på billedet uden bemærkning: ..." og i "Ikke tjekket".

## 3. Spørg

Saml spørgsmålene i én besked, kort og uden fagord, før du giver dommen:

- `varenummer` er `VURDER`: hvad er produktets GTIN ifølge kunden?
- `hoejde` er `RET`: er den lave højde aftalt med kunden eller trykkeriet? Nævn tallene. Spørg én gang i samtalen som et ja eller nej, ikke for hver fil. Er den aftalt, står punktet stadig som `RET` på GS1's tal, men flyttes til "Kendt afvigelse (oplyst af dig)".
- `kode_findes` er `VURDER`: skal denne del have en stregkode? (En forside-etiket, hvor koden tiltrykkes, en vægtvare, et kolli eller et låg har ofte ingen.)
- Koden sidder på en rund flade og løber rundt om den: hvad er diameteren? Er det en bøtte-etiket (`krumning` med "Ø ca. ... ved koden"), så spørg om etiketten går hele vejen rundt.
- Målestokken er `tvivl`: er PDF'en eksporteret i 100 %? Kender brugeren etikettens format, så kør igen med `--format`.
- Du kan ikke se emballagetypen eller panelet: hvad er det?

Kør trin 1 igen med svarene (`--gtin`, `--diameter`, `--format`). "Ved ikke" er et svar. Punktet står så åbent i resultatet.

Færdig når hvert spørgsmål er besvaret eller udtrykkeligt står åbent.

## 4. Lever

Skabeloner og tone: `references/levering.md`.

1. Dom i chatten, med målingens usikkerhed, "ingen fund på" og "ikke tjekket".
2. `kode_<N>.png` for hver kode, der har et fund.
3. Korrekturnotat som `Stregkodekorrektur_<filnavn>.md`.
4. Mailudkast, når noget skal rettes eller afklares. Spørg, før noget sendes.

Færdig når dom og notat er leveret, hver `RET` og `VURDER` har sted, tal, krav, usikkerhed og hvad der skal gøres, og listen "ikke tjekket" står i dommen (mail kun ved fund).

## Statusser

| Status | Betyder | I dommen |
|---|---|---|
| `RET` | Målingen er sikker, og et GS1-krav med "skal" og et tal er ikke opfyldt, også med målingens usikkerhed | Skal rettes |
| `VURDER` | Tæt på grænsen, kilden siger kun "bør" eller "når muligt", målingen er en tilnærmelse, eller det kræver viden om varen | Tag stilling til |
| `SE_SELV` | Kun billedet kan svare | Dit svar fra trin 2 |
| `EFTER_TRYK` | Kræver verifier på prøvetryk | Kan først tjekkes på tryk |
| `IKKE_MAALT` | Kunne ikke måles, og hvorfor står der | Kan ikke tjekkes her |
| `INGEN_FUND` | Intet fundet på dette punkt | Aldrig det samme som i orden eller godkendt |

`RET` bruges kun på GS1-krav. Én undtagelse: har brugeren selv oplyst produktets GTIN, og koden bærer et andet nummer, er det `RET`, fordi nummeret er oplyst af brugeren.

## Målingens usikkerhed (siges altid i dommen)

Størrelser i mm måles på stregerne i en gengivelse ved 1200 dpi (0,021 mm pr. pixel). Scriptet bruger en margin på **0,05 mm** (ca. 2 pixel) på højde, guard bars og lyszoner. Sig det sådan, at en grafiker forstår det: "Målingen kan være ca. 0,05 mm forkert, så selv med den usikkerhed er koden for lav." Er et fund tættere på grænsen end marginen, er det `VURDER`, ikke `RET`. En værdi lige under kravet, men inden for marginen, er også `VURDER` ("tæt på grænsen"). Er den lige over kravet, er det `INGEN_FUND`; nævn gerne, at den er tæt på.

Hvordan marginen er fundet, og hvad der ikke er afprøvet: marginen er valgt ud fra pixelstørrelsen. Den er afprøvet 2026-11-22 på 14 selvlavede vektor-PDF'er (EAN-13 med kendt X, højde og lyszone). Målingerne afveg højst 0,01 mm på højde, lyszoner og guard bars og højst 0,0002 mm på X (under 0,1 %). Den er ikke afprøvet på billedfiler, drejede koder, farvet baggrund eller trykte filer, og ikke mod en verifier. Sig ikke mere end det. Kontrasten er en tilnærmelse og ikke en verifier-måling. Tallene gælder det, der er tegnet i PDF'en, ikke et tryk.

## Hvad skillen ikke ved

- Om koden kan scannes i butikken (kræver en verifier på prøvetrykket, SK-25).
- Om nummeret er produktets rigtige GTIN (kræver kundens varedata).
- Om delen skal have en stregkode, og om afkortet højde er "absolut nødvendig" (GS1 6.3.3.4).
- ISO/IEC 15416, GS1 Ten steps og GS1's Application Standard Profiles (afsnit 8) er ikke læst. Intet er bekræftet af en ekspert.
- UPC-A: koden læses som EAN-13 med 0 først, så UPC-A's lyszoner (9X og 9X) og tillægsafstand (9X) tjekkes ikke fuldt ud. Nummeret kan ses på, at det starter med 0.
- Punkterne SK-29 til SK-34 er fundet i GS1, men ikke bygget ind i scriptet (se `references/tjekpunkter.md`).
- Om en ændring i GS1-reglerne er kommet siden `references/kilder.md` sidst blev tjekket. Tjek kilderne igen før en ny version.

## Versionsnote

2.1-offentlig (2026-11-25): offentlig udgave. Kundepraksis og et bureaus egne skabeloner er taget ud. Etikettens format og teknisk magenta kan oplyses med `--format` og `--teknisk-magenta`. GS1-målingerne er uændrede: alle 20 testfiler giver samme mål og statusser som den interne udgave.

2.1 (2026-11-22): rettet efter et uafhængigt kildetjek. Tillæg kræver mindst 9X ved UPC-A (7X ved EAN-13 og UPC-E). X fra 0,249 til 0,264 mm er `VURDER` (lovligt ved on-demand-print), ikke `RET`. GS1-128 dømmes `RET` kun når bredden uden lyszoner alene er over 165,10 mm. Kilderne er rettet for skrift, kontrolciffer, poser, dåse-multipack, 8 mm og HRI ved 2D (se `references/kilder.md`). Værdier lige under kravet (inden for marginen) er `VURDER`. Samme afstand mellem kode og tillæg giver ét fund (SK-17), ikke to.

## Kilder

`references/kilder.md` har hver regel med kilde-ID, sted i originalen og status. `references/kilder-sha256.txt` har kontrolsummer for de originaler, der er læst. GS1's PDF'er er ophavsretligt beskyttede og ligger ikke her. Hent dem hos GS1 og GS1 Denmark. `references/tjekpunkter.md` har tjekpunkterne. `references/gs1-krav.md` har GS1-kravene. Læs dem, når en bruger spørger "hvorfor er det en regel?", eller når et fund skal forklares nærmere.
