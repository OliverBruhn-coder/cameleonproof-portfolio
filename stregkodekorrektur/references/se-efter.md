# Se efter

Det scriptet ikke kan måle. Svar for hver kode: ingen bemærkning, problem (sig hvad), eller kan ikke ses. "Ingen bemærkning" gælder kun det ene punkt, aldrig hele koden.

Punkterne 2, 4 og 5 til 6 svarer til tjekpunkterne SK-26, SK-27 og SK-28 i `tjekpunkter.md`.

## Koden selv (`kode_<N>_raa.png`)

1. **Cifrene.** Scriptet læser dem (som tekst i PDF'en eller med OCR). Er `cifre_tekst` `INGEN_FUND`, passer
   de med koden. Er den `VURDER` eller `SE_SELV`, så læs dem selv ciffer for ciffer og sammenlign
   med nummeret. Første ciffer står til venstre for koden (EAN-13).
2. **Cifrenes skrift.** Almindelig, ikke fed, ikke kursiv, ikke sammenpresset, ikke skåret af.
   GS1 anbefaler OCR-B og tillader andre tydelige skrifter. Fed, kursiv, lys eller smal bør ikke bruges (GS1 v26 4.14 regel 2.a, SK-26).
3. **Noget lyst i de hvide felter.** Scriptet måler mørke ting. Se efter svag tekst, lys grafik
   eller en farvekant tæt på stregerne.
4. **Redigeret som billede.** Skæve, slørede, strakte eller afskårne streger tyder på at koden
   er skaleret eller beskåret i stedet for genereret.

## Placeringen (`oversigt_s<N>.png`)

5. **Panel og kvadrant.** Hvor sidder koden? Sammenlign med tabellen herunder for
   emballagetypen (spørg, hvis den ikke fremgår af filen).
6. **Fold, svejsning, skæring.** Ligger koden over eller tæt på en fold, en svejsesøm, en
   perforering, et hjørne eller under en flap? Lilla på oversigten: linjer gennem koden. Har filen en forklaring af linjetyperne
   (fx "Pliage / folding"), så brug den til at afgøre om linjen er en fold.
7. **Flere koder.** Er der en anden stregkode eller QR-kode på siden? Kan begge ses samtidig på
   den færdige pakke?
8. **Orientering.** Stregerne lodrette (picket fence) er foretrukket. Ligger koden på en rund
   flade og står stregerne parallelt med aksen, gælder diameterkravet (spørg efter diameteren).
9. **Ingen kode i filen.** Står der en hvid boks, en pladsholder eller "EAN" uden streger? Er det
   en del der normalt ikke har kode (forside-etiket hvor koden tiltrykkes, vægtvare, kolli, låg)?

## Placering efter emballagetype (GS1 v26 6.3.3 og 6.4.1 til 6.4.18, K-22)

| Type | Hvor |
|---|---|
| Æske, karton, sleeve | Nederste højre kvadrant bagpå. Ingen særlige hensyn. |
| Pose | 6.3.3.6 siger, at koden bør sidde midt på bagsiden, ca. en tredjedel oppe fra bunden og så langt fra kanten som kantreglen tillader (bør, ikke skal). Foretrukken placering i 6.4.1: nederste højre kvadrant af bagsiden, væk fra kanten. |
| Flaske, glas, krukke | Nederste højre kvadrant bagpå. Aldrig på halsen (6.4.3). Det samme gælder halsen på en kande (6.4.8). "Skulder" er ikke nævnt i GS1 v26. |
| Dåse, bøtte, tube | Nederste højre kvadrant bagpå. Fuger og rygge skal undgås (6.4.5). |
| Bakke | Nederste højre hjørne af toppen (6.4.13). |
| Folie, krympefilm | Plan flade uden folder, krøl eller svejsesøm. Det er ikke en egen type i GS1 v26. Reglen er 6.2.3.3 (SK-28). |
| Multipack | Nederste højre kvadrant bagpå (6.4.10). Multipackens kode skal være den eneste synlige (6.3.1). På dåse-multipacks bør top og bund undgås. |
| Ægkarton | Højre halvdel af bagsiden, over hængslet (6.4.7). |

## Sådan skriver du det

Skriv kun det du kan se, og mærk det "set på billedet". Mål i mm kommer fra `maaling.json`.
Er du enig med scriptet, så skriv det på én linje.
