# Syntetisk eksempel: en regelkontrol, der aldrig giver falsk "bestået"

> **Dette er ikke CameleonProof-koden.** Det er et selvstændigt, illustrativt eksempel, skrevet til dette portfolio. Reglerne, grænseværdierne ("SYN-SPEC") og etiketterne er opdigtede. Den eneste rigtige algoritme er GS1's offentlige kontrolciffer (mod 10). Eksemplet læser ikke PDF-filer. Det tager imod de målinger, en PDF-læser ville levere, som JSON.

Eksemplet viser to af CameleonProofs designprincipper på cirka 150 linjer Python uden afhængigheder:

1. **Regler er data.** Hvert regelkort i [`rules/synthetic_rules.json`](rules/synthetic_rules.json) har tærskel, måleusikkerhed og kilde.
2. **En manglende eller usikker måling er aldrig "bestået".** Den samlede status kan ikke blive "godkendt". Det bedste svar er "ingen fund på de tjekkede punkter", og rapporten siger altid, hvad der ikke blev tjekket.

## Kør det

```bash
cd example
python3 rulecheck.py samples/borderline.json
python3 -m unittest discover -s tests -v
```

## Statusser

| Pr. regel | Betydning |
|---|---|
| `FIX` | Målt uden for kravet |
| `REVIEW` | Inden for måleusikkerheden, eller målt med lav sikkerhed |
| `NOT_MEASURED` | Målingen mangler. Det bliver aldrig til bestået |
| `MANUAL` | Et menneske skal se efter |
| `NO_FINDING` | Målt og inden for kravet |

Samlet: `FIX_REQUIRED`, `REVIEW_REQUIRED`, `NO_FINDINGS_PENDING_MANUAL_CHECKS` eller `NO_FINDINGS_ON_CHECKED_ITEMS`. Der findes bevidst ingen `APPROVED`.

## Eksempelfiler

| Fil | Hvad den viser | Samlet resultat |
|---|---|---|
| `clean.json` | Alt målt og inden for kravet | `NO_FINDINGS_PENDING_MANUAL_CHECKS` (farvekontrast kræver et menneske) |
| `missing_measurement.json` | Cifferhøjden kunne ikke måles | `REVIEW_REQUIRED` |
| `wrong_check_digit.json` | Forkert kontrolciffer i stregkodenummeret | `FIX_REQUIRED` |
| `borderline.json` | Lige under grænsen inden for marginen, og en måling med lav sikkerhed | `REVIEW_REQUIRED` |
| `unreadable_text.json` | Teksten kunne ikke læses, så fravær er ikke bevist | `REVIEW_REQUIRED` |

Stregkodenumrene ligger i GS1's interval 200-299 til intern brug, så de kan ikke tilhøre et rigtigt produkt.

## Testene

Syv tests dækker hver eksempelfil og en egenskab: Fjernes en hvilken som helst måling, bliver reglen `NOT_MEASURED` og aldrig `NO_FINDING`.

---

*English: a standalone, synthetic illustration of two CameleonProof design principles: rules as data, and a missing or uncertain measurement is never a pass. Fictitious rules, not the real implementation.*
