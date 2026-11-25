# GS1-krav bag tjekkene

Kun krav fra GS1 General Specifications v26 (Release 26.0, Ratified, Jan 26). Hvert krav har et tjekpunkt-ID (`tjekpunkter.md`) og et kilde-ID (`kilder.md`) med afsnit og sidetal. Status for alle: fundet i primærkilde, ikke bekræftet af en ekspert. Sekundære kilder (GS1 Danmark 2021, ISO/IEC 15416, GS1 Ten steps) er ikke primærkilder og står ikke som krav.

## Hvordan der måles

- Koden findes og nummeret læses med zxing. Alt i mm måles på stregerne i en gengivelse ved 1200 dpi (0,021 mm pr. pixel). Usikkerheden står i `SKILL.md` under "Målingens usikkerhed".
- X (modulbredden) er stregernes samlede bredde delt med antal moduler (95 for EAN-13 og UPC-A, 67 for EAN-8, 51 for UPC-E). Stregerne tælles ud fra symbolets opbygning.
- Højden er de rækker, hvor stregerne er mørke og mellemrummene lyse. Mørk baggrund og cifre tæller derfor ikke med. Det passer med GS1: højden er stregerne uden cifre og uden de forlængede guard bars (5.2.3.2).
- Cifrene læses fra PDF'ens tekst, eller med Tesseract (OCR), når de er omdannet til kurver. Findes Tesseract ikke, læser Claude dem på billedet.
- Lyszoner måles i inspektionsbåndet (10 til 90 % af højden) og i rødt lys som scanneren (den røde kanal): rød, orange, pink og brun bund er lys for scanneren, sort, blå og grøn er mørk.
- Kan koden ikke læses i gråtoner, læses den igen i rødt lys.
- Skærer stanselinjen stregerne, er højden den del, der ligger inden for stanselinjen.
- Målestokken: PDF'er fra InDesign og Illustrator er 1:1. Oplyses etikettens format med `--format`, bekræfter scriptet det ved at finde en ramme med de mål. Bliver X urimelig uden bekræftet målestok, er status `tvivl`, og mm-krav dømmes kun `VURDER`.

Tekniske markeringer i magenta (stanselinjer, mål) tæller kun som ikke-trykte, når `--teknisk-magenta` er sat. Etikettens format kan oplyses med `--format`, så målestokken kan bekræftes.

## Kravene

`Status ved fund` er den, scriptet giver. `RET` kræver, at kilden siger "skal" med et tal, og at målingen er sikker. "Bør" og "når muligt" giver `VURDER`.

| Tjekpunkt | Krav | Kilde-ID og sted | Status ved fund |
|---|---|---|---|
| SK-01 | X mindst 0,264 mm (80 %) og højst 0,660 mm (200 %). Nominel X er 0,330 mm (100 %). 80 til 85 % giver ingen handling. Fodnote (*): 0,249 til 0,264 mm er kun lovligt ved on-demand-print (termisk, laser) | K-01. Tabel 5-44 (5.12.3.1) med fodnote (*), 5.2.3.1 | `RET` under 0,249 og over 0,660 mm. `VURDER` fra 0,249 til 0,264 mm, fordi scriptet ikke ved, hvordan der trykkes |
| SK-02 | Stregehøjde mindst 69,24 x X for EAN-13, UPC-A, UPC-E (22,85 mm ved 100 %, 18,28 mm ved 80 %) og 55,24 x X for EAN-8 (18,23 mm og 14,58 mm). Faktorerne er afledt af tabellen. Kravet regnes af den målte X. Under X 0,264 mm (on-demand) siger fodnote (*), at området aldrig bør være mindre end for X 0,264 mm, så højden kan i så fald kræve 18,28 mm. Scriptet regner 69,24 x X Skærer stanselinjen stregerne, tæller kun delen inden for | K-02, K-03. Tabel 5-44 med fodnote (**), 5.2.3.2, 6.3.3.4 | `RET` under kravet med margin. GS1 tillader afkortning, når den er "absolut nødvendig" (6.3.3.4), og så skal den størst mulige højde bruges. Om det er nødvendigt, afgør scriptet ikke |
| SK-03 | Guard bars (start, midte, slut) forlænges 5X nedad | K-04. 5.2.3.2 | `RET` |
| SK-04 | Lyszone: EAN-13 11X venstre og 7X højre. EAN-8 7X og 7X. UPC-A 9X og 9X. UPC-E 9X og 7X | K-05. Tabel 5-44, 5.2.3.4 | `RET` |
| SK-05 | Nummeret i klar tekst under koden. Alle indkodede cifre vises | K-06. 5.2.5 | `RET` |
| SK-06 | Mindst 0,5X luft mellem cifrenes top og stregernes bund | K-06. 5.2.5 | `RET` |
| SK-07 | Cifrenes skrift bør være mindst 2 mm høj. (Scriptets omregning fra cifrenes højde til skriftstørrelse er ikke verificeret) | K-07. 4.14 regel 2.a.iii | `VURDER` |
| SK-08 | Cifrene er koden i klar tekst. Læses som tekst i PDF'en (afvigelse giver `RET`) eller med OCR (afvigelse giver `VURDER`, fordi OCR kan tage fejl) | K-06. 5.2.5 | `RET` eller `VURDER` |
| SK-09 | Cifrene ligger inden for stanselinjen. Afledt: cifre, der er skåret af, er ikke vist | K-06 (afledt). 5.2.5 | `RET` |
| SK-10 | Mørke streger på lys bund. Kontrasten måles i rødt lys. Under 40 % kan koden ikke nå samlet 1.5, og 40 til 55 % er tæt på. 55 % er ikke fundet i GS1 | K-08. Tabel 5-44 (1.5/06/660), 5.12.5.11.1 | `VURDER`. Scriptets kontrast er en tilnærmelse |
| SK-11 | Når muligt ikke tættere end 8 mm og ikke længere end 100 mm fra pakkens nærmeste kant. Måles til etikettens faktiske stanselinje (rektangulær, rund eller formet). Går koden ud over den og skæres af, er det `RET` (aldrig på kanter og stanselinjer, 6.2.3.3). Maksimum 100 mm måles ikke (SK-29) | K-09, K-10. 6.3.3.3, 6.2.3.3 | `VURDER` under 8 mm. `RET` ved afskåret kode |
| SK-12 | Aldrig kode med lyszoner på perforeringer, stanselinjer, sømme, rygge, kanter, snævre buer, folder, flapper, overlap og ru overflade | K-10. 6.2.3.3 | `VURDER`. Scriptet kan ikke se, hvad en linje er |
| SK-13 | Mindst én stregkode på en vare til kassen | K-11. 6.3.1 | `VURDER`. Om varen skal scannes, ved kun du |
| SK-14 | Gyldigt kontrolciffer (SHALL i symbolafsnittene, beregning i 7.9.1) | K-21. 5.2.2.1 til 5.2.2.3, 7.9.1 | `RET` |
| SK-15 | ITF-14 bruges til varer, der ikke forventes at passere kassen | K-12. 5.1.1 (beskrivende) | `VURDER` |
| SK-16 | Ikke to forskellige GTIN på samme vare. Indre koder i en multipack skjules helt. Samme GTIN i alle koder til samme formål | K-11, K-17. 6.3.1, 4.15.1 pkt. 2 | `VURDER` |
| SK-17 | Tillæg (EAN-2 og EAN-5): mindst 7X (EAN-13, UPC-E) eller 9X (UPC-A), højst 12X mellem hovedkode og tillæg, samme X. EAN-8: ikke angivet i tabellen | K-13. 5.2.3.6, tabel 5-44 (s. 410) | `RET` for EAN-13, UPC-A, UPC-E. `VURDER` for EAN-8 |
| SK-18 | Rund flade: vinkel under 30 grader ud til kodens kant, ellers stregerne på tværs (ladder). Mindste diameter efter tabel 6-2 for picket fence. Tabellen har ingen række for X 0,330. Ligger X mellem to rækker, er diameteren mellem de to rækkers værdier, og så er svaret `VURDER` | K-14. 6.2.3.2, tabel 6-1 og 6-2 | `RET` under den lavere række. `VURDER` mellem rækker |
| SK-19 | GS1 DataMatrix, Data Matrix og QR med Digital Link til kassen: modul 0,396 til 0,990 mm (tabel 5-46). Tabel 5-45 (AI 8200) har højst 0,743 mm | K-15. Tabel 5-45 og 5-46 | `RET` |
| SK-20 | GS1 Digital Link i ukomprimeret form | K-16. Tabel 5-46 fodnote (**) | `VURDER` |
| SK-21 | 2D-koden bærer samme GTIN som stregkoden | K-17. 4.15.1 pkt. 2 og 8 | `RET` ved forskelligt GTIN. `VURDER` ved intet GTIN |
| SK-22 | 2D skal bruges ud over EAN/UPC. GS1 henviser til profiler i afsnit 8 for 2D uden 1D (ikke læst) | K-18. Tabel 5-45 (tekst efter), 4.15.4 pkt. 1 | `VURDER` |
| SK-23 | Hele 2D-koden inklusive lyszoner bør ligge inden for en radius på 50 mm fra stregkodens centrum | K-19. 6.3.3.1 | `VURDER` |
| SK-24 | GS1-128: højst 48 datategn og 165,10 mm inklusive lyszoner. Scriptet måler uden lyszoner. Lyszonerne er mindst 10X hver (5.4.6.3) | K-20. 5.4.1, 5.4.4.3, 5.4.6.3 | `RET` ved mere end 48 tegn eller bredde alene over 165,10 mm. `VURDER`, hvis bredden uden lyszoner er mellem 152 og 165,10 mm |
| SK-25 | Printkvalitet mindst 1.5/06/660 og lyszoner på det trykte. Kun med verifier | K-08, K-05. Tabel 5-44 | `EFTER_TRYK` |
| SK-26 | Cifrenes skrift tydelig. Fed, kursiv, lys eller smal bør ikke bruges | K-07. 4.14 regel 2.a | `SE_SELV` |
| SK-27 | Placering efter emballagetype (se `se-efter.md`) | K-22. 6.3.3 og 6.4 | `SE_SELV` |
| SK-28 | Ikke rundt om hjørner, under flapper eller på ru overflade | K-10. 6.2.3.3 | `SE_SELV` |

Ikke implementeret i scriptet (står i dommen under "Ikke tjekket"): SK-29 til SK-34 (se `tjekpunkter.md`).

## Det GS1 ikke siger (så scriptet ikke dømmer RET på det)

- Ingen afstand på 8 mm til en fold eller svejsning inde på pakken. GS1 siger kun "aldrig på" (6.2.3.3). 8 mm er til pakkens kant, og "når muligt" (6.3.3.3).
- Intet forbud mod ITF-14 på forbrugerpakning med de ord. 5.1.1 er en beskrivelse.
- Intet krav om, at koden skal vende som teksten, for scanningen: GS1 siger, at lodrette streger er foretrukne, og at det ikke gør nogen forskel (6.2.3). Undtagelse: for plastpakkede varer (6.5.5.2, s. 504 til 505) og kasser (6.5.6.3, s. 507) står der, at retningen SHALL stemme med grafik og tekst. Ikke undersøgt, om det gælder fødevareemballage.
- Intet om pladsholder-koder som begreb. Men præfikset 0000000 er et begrænset cirkulationsnummer (1.2.2.2.1, tabel 1-4, K-26), som ikke må bruges i åbne miljøer. Derfor `VURDER`, ikke `RET`.
- Intet om, at stregerne skal trykkes i én farve (Ten steps er ikke læst).
- Ingen 55 %-grænse for kontrast (ISO/IEC 15416 er ikke læst).
