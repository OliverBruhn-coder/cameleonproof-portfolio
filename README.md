# CameleonProof

**Oliver Bruhn Lyngaa Wegeberg**, cand.merc. og AI-first udvikler.

Korrektur af emballagedesign med AI-kodeagenter og almindelig kode. Hele forløbet fra forretningsproblem til system: analysen, første version, min egen revision af den, et nyt design og retningsskiftet til én skill pr. regelområde.

**Start på websiden: [oliverbruhn-coder.github.io/cameleonproof-portfolio](https://oliverbruhn-coder.github.io/cameleonproof-portfolio/)** ([English](https://oliverbruhn-coder.github.io/cameleonproof-portfolio/en/))

> Systemet er under løbende udvikling og afprøves i et pilotforløb med konkrete korrekturopgaver hos Cameleon.

## Hvad ligger her

| Mappe | Indhold |
|---|---|
| [`docs/`](docs/) | Websiden på dansk og engelsk, diagrammerne og casen som PDF ([dansk](docs/pdf/CameleonProof_case_study_DA.pdf), [engelsk](docs/pdf/CameleonProof_case_study_EN.pdf)) |
| [`stregkodekorrektur/`](stregkodekorrektur/) | En offentlig udgave af stregkode-skillen fra version 2: vejledning, målescript, kilder, opdigtede testfiler, tests og en eksempelkørsel |
| [`kilde/`](kilde/) | Kilderne til diagrammerne og PDF'erne |

## Prøv koden

```bash
cd stregkodekorrektur
python -m unittest discover -s tests -v
python scripts/maal.py testfiler/demo_etiket.pdf --ud resultat --format 100x60
```

Kræver Python 3.10 eller nyere. Scriptet installerer selv PyMuPDF, zxing-cpp, NumPy og Pillow, hvis de mangler.

## Hvad ligger ikke her

Koden, regelbasen og bureauets filer i det fulde system er fortrolige. Bureauets interne tal, kundedata, kundepraksis og bureauets skabeloner er ikke med. Testfilerne er opdigtede og bruger et nummer fra GS1's område for begrænset cirkulation.

## Rettigheder

Vises som arbejdsprøve. Alle rettigheder forbeholdes. Koden må læses og køres for at vurdere den, men ikke genbruges.

## English summary

Proofing of packaging artwork with AI coding agents and plain code, told as the whole journey from business problem to system. **Start with the website: [oliverbruhn-coder.github.io/cameleonproof-portfolio/en](https://oliverbruhn-coder.github.io/cameleonproof-portfolio/en/).** The folder `stregkodekorrektur/` holds a public edition of the barcode skill (in Danish, like its users) with tests and an example run. Shown as a work sample. All rights reserved.

Kontakt: [linkedin.com/in/oliver-bruhn-71607317a](https://linkedin.com/in/oliver-bruhn-71607317a)
