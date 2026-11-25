# Teknisk oversigt

*Kort reference. Uddybning, diagrammer og baggrund står i [case study'en](case-study-da.md).*

## Version 1: websystemet (februar til september 2026)

| Del | Teknik | Bemærkning |
|---|---|---|
| Brugerflade | Browser (React) | Upload, rapport og gennemgang pr. sag |
| Backend | Python, FastAPI | Login og adgang pr. sag. Adgangskoder hashes med scrypt, sessioner er HMAC-signerede, og første login sker med engangskode |
| PDF og stregkode | PyMuPDF, zxing-cpp | Geometri, tekst og stregkode læses fra PDF'ens struktur |
| OCR | Tesseract | Fallback, når teksten ikke kan læses direkte |
| Regler | YAML-regelkort | Tærskler, betingelser og kilde-ID. 110 kort, hvoraf 42 stregkoderegler er aktive i fladen |
| Kilder | Kilderegister | Side og ordret citat. 40 af 42 stregkoderegler kontrolleres automatisk mod kildedokumentet |
| Data | SQLite | Sager, kørsler, fakta, fund, vurderinger og accepterede undtagelser |
| Produktdata | Lokal connector | Kører på medarbejderens maskine, kan kun læse og svarer kun lokalt. Serveren når aldrig filserveren |
| AI | Claude vision (Haiku) | Kun når layoutanalysen giver "kan ikke tjekke". Kræver mindst 0,75 i sikkerhed og kan højst give et rådgivende svar |
| Drift | Docker bag HTTPS, GitHub Actions | Test, så deploy og så healthcheck. Deploy sker kun ved grønt build |
| Test | pytest | 2.179 testcases, regressionsbaseline på 10 rigtige designs (1.110 låste resultater) og 35 syntetiske fejlvarianter |

**Pipeline (11 trin, forenklet):**

1. Upload og hash.
2. Læs artwork, kolofon og teknisk lag.
3. Skala og kalibrering.
4. Emballageform.
5. Hvilke regler gælder?
6. Mål og sammenlign.
7. Eventuelt et rådgivende AI-forslag.
8. Status pr. regel.
9. Kildehenvisning.
10. Samlet dom.
11. Rapport i JSON og HTML.

**Statusser pr. regel:** bestået, fejl, rådgivende, kan ikke tjekkes, kræver manuel vurdering, gælder ikke. Den samlede dom kan aldrig blive "bestået", hvis et punkt står som "kan ikke tjekkes".

## Version 2: ét regelområde ad gangen (siden november 2026)

| Del | Indhold |
|---|---|
| `SKILL.md` | Instruktion til modellen: brugeren (grafiker eller korrekturlæser), statusser, levering i tre dele (ret / vurder selv / ikke tjekket) |
| Målescript (Python) | Måler i PDF'en: cifferhøjde fra skriftens konturer, ℮-mærkets størrelse og placering, stregkodens geometri |
| Referencer | `kilder.md` (primærkilder med version og hentedato), `tjekpunkter.md` (ID → kilde-ID), originaler med SHA-256 |
| Statusser | ret, vurder, se selv, efter tryk, ikke målt, ingen fund. Aldrig "godkendt" |
| Hjælpeskills | Kildetjekker (kilde-ID'er, SHA-256 og tal, der ikke står i kilden) og områdebygger (opretter nye områder efter samme proces) |

**Bygget indtil nu:** stregkode (v2.1), nettoindhold og ℮-mærke (v0.6) og allergener (v0.1).

**Planlagt:** en fælles PDF-profil, der måles én gang til alle områder, en samleskill og flere områder (næringsdeklaration, dato og opbevaring, økologi).

## Hvorfor disse valg

- **Regler som data:** En ny regel eller en ændret tærskel kræver ikke ny kode, og hver regel bærer sin kilde.
- **Almindelig kode til domme:** Måling i hundrededele af millimeter skal være præcis, gentagelig og sporbar.
- **SQLite og én server:** Det passer til et lille bureau med få samtidige brugere. Det er enkelt at drive og tage backup af.
- **Skills i version 2:** Korrekturlæseren kan arbejde i et værktøj, hun allerede har. Hvert område kan bygges, testes og forbedres for sig.
