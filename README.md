# CameleonProof: automatisk korrektur af emballagedesign

**Oliver Bruhn Lyngaa Wegeberg**, cand.merc. og AI-first udvikler. Jeg omsætter forretningsproblemer til software med AI-kodeagenter.

CameleonProof er et klientprojekt for emballagedesignbureauet Cameleon Creatives A/S i Aarhus. Systemet kontrollerer trykfærdige emballagedesign mod regelbaserede krav, foreløbig stregkoder og dele af fødevaremærkningen. Det siger tydeligt, hvad der skal rettes, hvad et menneske skal vurdere, og hvad det ikke kunne tjekke.

> **Status:** Systemet er under løbende udvikling og afprøves i et pilotforløb med konkrete korrekturopgaver hos Cameleon. Første version (et websystem) kom på server i september 2026, men blev ikke taget i brug. Anden version bygges ét regelområde ad gangen.

## Start her

| Materiale | Format |
|---|---|
| **Case study (dansk)**: problem, metode, arkitektur, test, status | [Læs på GitHub](docs/case-study-da.md) · [PDF](docs/pdf/CameleonProof_case_study_DA.pdf) |
| **Case study (English)** | [Read on GitHub](docs/case-study-en.md) · [PDF](docs/pdf/CameleonProof_case_study_EN.pdf) |
| **Præsentation**, 7 slides | [PDF](docs/pdf/CameleonProof_praesentation_DA.pdf) · [HTML](docs/presentation-da.html) |
| **Teknisk oversigt** | [docs/teknisk-oversigt.md](docs/teknisk-oversigt.md) |
| **AI-first arbejdsmetode, min rolle og agenternes rolle** | [docs/ai-first-arbejdsmetode.md](docs/ai-first-arbejdsmetode.md) |
| **Status og begrænsninger** | [docs/status-og-begraensninger.md](docs/status-og-begraensninger.md) |
| **Arkitekturdiagrammer** | [docs/diagrams/](docs/diagrams/) |
| **Syntetisk kodeeksempel** af en regelkontrol, der aldrig giver falsk "bestået" | [example/](example/) |

## Projektet på et minut

- **Problemet:** Ledelsen anslår, at bureauet laver flere hundrede korrekturer af emballagedesign om året á cirka en time. Min egen analyse af bureauets data peger på samme størrelsesorden. Det er skøn og ikke målte besparelser.
- **Hvordan det startede:** Jeg så behovet under mit speciale hos bureauet og foreslog selv projektet.
- **Princippet:** Systemet må aldrig give et falsk "bestået". Mangler en måling, bliver svaret "kan ikke tjekke", og det skriver aldrig "godkendt".
- **Arbejdsdelingen:** Domme kommer fra almindelig kode, der måler i PDF'en. AI læser kontekst og skriver svaret, og et menneske afgør det, der kræver skøn.
- **Metoden:** AI-kodeagenter skriver koden ud fra mine direktiver. Uafhængige agenter, der ikke kender facit, blindtester hver rettelse.

## Min rolle og AI-agenternes rolle

| | |
|---|---|
| **Mig** | Fandt behovet, foreslog projektet, afgrænsning og prioritering, krav og acceptkriterier, regler og kilder, systemdesign, statusmodel, testmetode, drift og dialog med bureauet |
| **AI-kodeagenter** | Kode, tests, rapporter, deployment-opsætning og dokumentation ud fra skrevne direktiver |
| **Uafhængige agenter** | Laver testfiler uden at kende målekoden, blindtester uden facit og kontrollerer kilderne mod originalerne |

## Nøgletal og hvad de dækker

| Tal | Hvad det er |
|---|---|
| 2.179 | Automatiske testcases i version 1 (1.823 testfunktioner, nogle med flere input). Ved sidste kørsel bestod 2.129, og 48 blev sprunget over. |
| 10 og 1.110 | Rigtige, godkendte designs i regressionsbaselinen og de låste resultater for dem |
| 42 og 40 | Aktive stregkoderegler i version 1 og dem, hvis kildecitat kontrolleres automatisk |
| 37 af 52 | Fødevareregler, der ifølge en revision aldrig havde udløst deres fejlgren. Derfor er de ikke slået til. |
| 12 af 14 | Fejlvarianter fundet i første blindtest af nettoindhold-skillen, uden falsk "ret" på de 6 fejlfri filer |

## Hvad repoet ikke indeholder

CameleonProof-koden, regelbasen, bureauets filer, kundenavne og interne data er fortrolige og ligger ikke her. Koden i [`example/`](example/) er et selvstændigt, syntetisk eksempel med fiktive regler, skrevet til dette portfolio. Den er ikke CameleonProof-implementeringen.

## English summary

CameleonProof is a client project for Cameleon Creatives, a Danish packaging design agency. It checks print-ready packaging artwork against rule-based requirements: barcodes so far, and parts of the food labelling rules. Its core rule is that it never gives a false pass. Verdicts come from plain code that measures the PDF. AI reads context and writes the answer, and a person decides what needs judgement. I found the need, proposed the project and own requirements, rules, design, testing and operations. AI coding agents write the code.

**Status:** under continuous development and being piloted on real proofing tasks at the agency. The first version, a web system, was deployed in September 2026 but not taken into use.

**Read more:** [case study in English](docs/case-study-en.md) ([PDF](docs/pdf/CameleonProof_case_study_EN.pdf)).

## Kontakt

[linkedin.com/in/oliver-bruhn-71607317a](https://linkedin.com/in/oliver-bruhn-71607317a)

---
© Oliver Bruhn Lyngaa Wegeberg. Tekst, diagrammer og kode må ikke genbruges uden tilladelse.
