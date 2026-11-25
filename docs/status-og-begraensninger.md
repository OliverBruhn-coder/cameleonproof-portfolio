# Status og begrænsninger

*Opdateret november 2026.*

## Status

Systemet er under løbende udvikling og afprøves i et pilotforløb med konkrete korrekturopgaver hos Cameleon.

| | Status |
|---|---|
| **Version 1** (websystem) | Bygget fra februar til september 2026 og lagt på server bag HTTPS i september 2026. Ikke taget i brug af bureauet. Kodeændringer står stille siden september. |
| **Version 2** (skills pr. område) | Stregkode v2.1, nettoindhold og ℮-mærke v0.6, allergener v0.1. Afprøves i pilotforløbet. Der er endnu ingen pilotresultater. |

## Begrænsninger, som er vigtige at kende

- **Brug:** Systemet indgår ikke i den daglige korrektur. Piloten er det første skridt.
- **Bureauets godkendelse:** Ingen områder er endnu gennemgået og godkendt af en fagperson hos Cameleon. Tjekpunkter og kilder er mine og agenternes arbejde, kontrolleret mod primærkilderne.
- **Dækning:** Kun regelbaserede krav, og kun i de nævnte områder. Kundekrav og layout er ikke med. Ifølge min gennemgang af korrekturrunderne er regelbaserede krav kun en mindre del af det, der rettes i praksis. Det er et skøn.
- **Filformater:** Version 1 er bygget til bureauets egne filkonventioner. Andre afsenderes filer er ikke valideret.
- **Fødevaremærkning i version 1:** 60 regelkort findes, men er ikke valideret og vises ikke i brugerfladen.
- **Testfiler:** Regressionsfilerne er gået til tryk og antages at være korrekte, men det er ikke uafhængigt verificeret. Mange fejlvarianter er syntetiske.
- **Kendte tekniske huller:**
  - Tekst, der er konverteret til kurver.
  - Fuld UPC-A-understøttelse.
  - Fælles PDF-profil og samleskill.
  - En række drifts- og sikkerhedspunkter i version 1, som skal lukkes før bredere brug.
- **Forretningstal:** Alle tal om tidsforbrug er skøn og ikke bekræftet af Cameleon. Systemet har endnu ikke dokumenteret en besparelse.

## Næste skridt

1. **De første pilottal:** fund pr. fil, falske alarmer og tid pr. korrektur.
2. **Bureauets gennemgang** af tjekpunkter og kilder for de tre områder.
3. **Fælles PDF-profil og samleskill.**
4. **Næste område:** næringsdeklaration.
