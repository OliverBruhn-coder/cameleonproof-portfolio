# Stregkodekorrektur (offentlig udgave)

En Claude-skill, der tjekker stregkoden i et emballagedesign mod GS1. Den er en del af CameleonProof version 2, hvor hvert regelområde er sin egen skill.

**Offentlig udgave.** Kun GS1-laget er med. Kundepraksis og et bureaus egne skabeloner og arbejdsmåder er taget ud af koden og teksterne. GS1-målingerne er de samme som i den interne udgave: alle 20 testfiler giver samme mål og statusser. Vises som arbejdsprøve. Alle rettigheder forbeholdes.

## Sådan er den bygget

| Del | Hvad den gør |
|---|---|
| [`SKILL.md`](SKILL.md) | Vejledningen til Claude: mål, se, spørg, lever. Skillen må aldrig skrive "godkendt" |
| [`scripts/maal.py`](scripts/maal.py) | Måler koden på selve stregerne i en gengivelse ved 1200 dpi og giver en status pr. tjekpunkt. Det er den eneste kilde til tal og statusser |
| [`references/`](references/) | Tjekpunkter, GS1-krav med afsnit og sidetal, kildeliste, hvad Claude selv skal se efter på billedet, og skabeloner til svaret |
| [`testfiler/`](testfiler/) | Opdigtede PDF'er med kendt facit og de scripts, der har lavet dem |
| [`tests/`](tests/) | Automatiske tests, der holder målingerne op mod facit |

Arbejdsdelingen er princippet i hele projektet: almindelig kode måler og giver status, AI læser billedet og forklarer, og et menneske afgør det, der kræver viden om varen.

## Statusser

`RET`, `VURDER`, `SE_SELV`, `EFTER_TRYK`, `IKKE_MAALT` og `INGEN_FUND`. `INGEN_FUND` betyder kun, at der ikke er fundet noget på det tjekkede punkt. Det er aldrig en godkendelse.

## Kør den

Kræver Python 3.10 eller nyere. Scriptet installerer selv PyMuPDF, zxing-cpp, NumPy og Pillow, hvis de mangler.

```bash
python scripts/maal.py testfiler/demo_etiket.pdf --ud resultat --format 100x60
```

Resultatet er `maaling.json` og billeder af koden med målene tegnet ind.

## Test

```bash
python -m unittest discover -s tests -v
```

Testene tjekker, at X (modulbredden) måles inden for 0,001 mm, højde og lyszoner inden for 0,05 mm, at grænsetilfælde får den forventede status, at der kun findes de seks statusser, og at alle tjek er GS1 eller en sammenligning med et oplyst varenummer.

Testfilerne bruger det opdigtede nummer 2000000000015. Præfiks 20 er begrænset cirkulation og er ikke tildelt en virksomhed (GS1 v26 tabel 1-4). Der er ingen kunde-, produkt- eller firmanavne.

## Kilder

GS1 General Specifications v26 (Release 26.0, januar 2026) og GS1 Denmarks vejledning om EAN-stregkoder. Hvert tjekpunkt peger på afsnit og side i [`references/kilder.md`](references/kilder.md). GS1's PDF'er er ophavsretligt beskyttede og ligger ikke her. [`references/kilder-sha256.txt`](references/kilder-sha256.txt) viser, præcis hvilke udgaver der er læst.
