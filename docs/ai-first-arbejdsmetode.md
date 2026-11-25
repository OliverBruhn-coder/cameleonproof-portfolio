# AI-first arbejdsmetode

*Hvordan jeg bygger software med AI-kodeagenter, og hvem der gør hvad.*

## Arbejdsdelingen

| | Ansvar |
|---|---|
| **Mig** | Problemforståelse og afgrænsning, prioritering, krav og acceptkriterier, regler og kilder, systemdesign og tekniske valg, statusmodel, testmetode, gennemgang af resultater, drift og dialog med kunden |
| **AI-kodeagenter** (Claude Code m.fl.) | Implementering af hele opgaver ud fra skrevne direktiver: kode, tests, rapporter, deployment-opsætning og dokumentation |
| **Uafhængige agenter** | Laver testfiler uden at kende målekoden, blindtester uden facit og læser kilderne igen mod originalerne |

Agenterne skriver koden. Mit review er rettet mod adfærd og påstande: hvad systemet gør på kendte filer, hvad det melder, og om hvert fund kan føres tilbage til en kilde.

## Sådan ser en opgave ud

1. **Direktiv:** mål, afgrænsning, acceptkriterier og stop-punkter, hvor agenten skal spørge.
2. **Implementering:** agenten løser hele opgaven på sin egen gren eller i sit eget worktree.
3. **Verificering:** tests og regression kører, og resultatet holdes op mod kendte filer.
4. **Uafhængig gentest:** en frisk agent, der ikke har set facit eller tidligere resultater, tester rettelsen.
5. **Log:** hvad der er gjort, hvad gentesten viste, og hvad den ikke dækker. Så commit.

## Faste regler for agenterne (uddrag)

- Opfind aldrig regler, grænseværdier, paragraffer eller kilder. Mangler der noget, skrives "ikke verificeret".
- Et resultat må aldrig konkludere "godkendt", kun "ingen fund på de tjekkede punkter" med en liste over det, der ikke er tjekket.
- Kundefiler forbliver lokalt og kommer aldrig i git eller online.
- Slet aldrig uden at spørge. Flyt hellere filen til en mappe til sletning.
- Den, der byggede et område, laver ikke selv kildekontrollen.

## Hvad der har ændret sig det seneste halve år

| Før (foråret 2026) | Nu (november 2026) |
|---|---|
| Ét direktiv og én pull request pr. opgave. Jeg gennemgik resultatet selv | Uafhængige agenter blindtester hver rettelse uden facit |
| Mange regler på én gang (110 regelkort) | Ét regelområde ad gangen med primærkilder og testfiler fra rigtige korrekturrunder |
| Testtal som tegn på kvalitet | Revisioner af, om testene faktisk fanger fejl. Fx havde 37 af 52 regler aldrig udløst deres fejlgren |
| Et AI-skøn kunne blive til en blokerende fejl (fundet ved en revision i august) | AI må højst foreslå. Domme kommer fra almindelig kode, og et menneske afgør det, der kræver skøn |
| Arbejdsgange i enkelte samtaler | Genanvendelige skills: kildetjekker, områdebygger og faste skabeloner |

## Hvornår almindelig kode er bedre end AI

- **Når svaret skal være præcist og gentageligt.** Det gælder målinger i millimeter, kontrolcifre og tærskler.
- **Når et fund skal kunne spores til en regel og en kilde.**
- **Når samme opgave køres mange gange.** Et script er billigere og hurtigere end et modelkald.

AI bruges til at læse kontekst, skelne mellem fx nettoindhold og drænet vægt, skrive svaret i klart sprog og lave uafhængige testvarianter. Det AI producerer om regler og kilder, kontrolleres altid mod originalen.
