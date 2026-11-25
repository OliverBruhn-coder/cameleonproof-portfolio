# Levering

Dansk, kort og konkret, som en kollega skriver. Ingen tankestreger, ingen pynteord. Tal i mm med to decimaler. Fortæl altid, hvor sikker målingen er. Brug aldrig "godkendt", "OK" eller "i orden" om koden eller filen. Skriv "ingen fund på de tjekkede punkter" og list, hvad der ikke blev tjekket.

"Koden kan læses i filen" er ikke det samme som "koden kan scannes i butikken". Det sidste afgøres med en verifier på prøvetrykket. Skriv derfor, hvad målingen gælder: "tegnet i PDF'en", ikke "på tryk". Står målestokken ikke fast, så skriv: "Målestokken kunne ikke bekræftes, så størrelsen i mm er ikke målt."

Eksemplerne herunder er opfundne. Nummeret 2000000000015 er fiktivt: det har gyldigt kontrolciffer, men starter med 20, som GS1 bruger til begrænset cirkulation (ikke tildelt en virksomhed). Brug aldrig et rigtigt varenummer, kunde- eller produktnavn i eksempler.

## Dom i chatten

Én sætning med konklusionen. Derefter kun de grupper, der har indhold. Hvert punkt: hvad er målt, hvad er kravet, hvor sikker er målingen, og hvad skal der gøres. Slut med, hvad der er tjekket uden fund, og hvad der ikke er tjekket.

Kravet står som GS1-krav. Et oplyst varenummer (VD-01) er en sammenligning med varedata, ikke et GS1-krav.

```
Koden er for lav, og to punkter skal du selv tage stilling til.

**Skal rettes**
- Højden er 15,70 mm. Kravet er mindst 18,22 mm ved denne størrelse (86 %), efter GS1 tabel 5-44.
  Målingen kan være ca. 0,05 mm forkert (afprøvet var den højst 0,01 mm forkert), så selv med den
  usikkerhed er koden for lav. Ikke aftalt, så gør koden højere. GS1 tillader kun lav kode, når
  det er absolut nødvendigt (SK-02).

**Tag stilling til**
- Koden sidder 6,2 mm fra pakkens kant. GS1 siger "når muligt" mindst 8 mm, så det er ikke et ubetinget
  krav (SK-11).
- Kontrasten i rødt lys er ca. 48 %. GS1 skriver, at under 40 % ikke kan nå kravet. 48 % er tæt på
  grænsen, og scriptets tal er en tilnærmelse. Test med en scanner (SK-10).

**Kan først tjekkes på prøvetryk**
- Printkvalitet med verifier (SK-25).

Ingen fund på: størrelse (X 0,264 mm, 80 %), guard bars, lyszoner, cifrenes luft og indhold,
kontrolciffer, linjer gennem koden.
Ikke tjekket: om koden kan scannes i butikken, om nummeret er produktets rigtige (ikke oplyst),
om delen skal have en kode, cifrenes skrift, placering efter pakketype, og de punkter scriptet ikke
måler (se "Ikke tjekket" i notatet). Set på billedet: koden sidder nederst til højre på bagsiden.
```

Er højden oplyst som aftalt, så skriv den under **Kendt afvigelse (oplyst af dig)** med hvem og hvornår. Dommen på SK-02 er stadig, at GS1's tal ikke er opfyldt.

## Målingens usikkerhed (siges altid)

Sig det kort, så en grafiker forstår det: "Målingen kan være ca. 0,05 mm forkert." Det er en margin, scriptet bruger (ca. 2 pixel i gengivelsen). Tallet kommer fra `maaling.json`, feltet `usikkerhed`. Er et fund tættere på grænsen end marginen, er det `VURDER`, ikke `RET`.

Hvad der er afprøvet, og hvad der ikke er: på 14 selvlavede vektor-PDF'er (EAN-13) afveg målingerne højst 0,01 mm på højde, lyszoner og guard bars, og højst 0,0002 mm på X. Sig ikke, at marginen er "kalibreret" eller gælder alle filer. Den er ikke afprøvet på billedfiler, drejede koder, farvet baggrund eller trykte filer. Kontrasten er en tilnærmelse og ikke en verifier-måling. Tallene i mm gælder det, der er tegnet i PDF'en, ikke et tryk.

## Notat (`Stregkodekorrektur_<filnavn>.md`)

```
# Stregkodekorrektur: <filnavn>
<dato> · skill version 2.1 (offentlig udgave) · ikke gennemgået af en ekspert

## Koden
EAN-13 2000000000015 · side 2 · størrelse 80 % (X 0,263 mm) · højde 16,10 mm · bredde 25,00 mm

## Målestok og usikkerhed
<målestok fra maaling.json> Målingen kan være ca. 0,05 mm forkert. <afprøvet og ikke afprøvet, fra
feltet usikkerhed>

## Skal rettes
### <titel> (SK-02)
Målt: ... · Krav: ... · Kilde: GS1 v26 tabel 5-44 (K-02) · Usikkerhed: ...
<hvad der skal gøres>

## Tag stilling til
## Kendt afvigelse (oplyst af brugeren)
## Kan først tjekkes på prøvetryk
## Set på billedet
<dine svar fra se-efter, mærket som vurdering>
## Oplyst af brugeren
<GTIN, aftalt højde, emballage, med navn og dato>
## Ingen fund på de tjekkede punkter
<liste fra maaling.json, ingen_fund_paa. Det er ikke en godkendelse>
## Ikke tjekket
<ikke_tjekket fra maaling.json, og forbehold>
```

Tal og statusser i notatet er scriptets. Dine iagttagelser står kun under "Set på billedet". Hvert punkt har tjekpunkt-ID i parentes (SK-02, VD-01), så en kollega kan slå reglen op i `references/tjekpunkter.md`. Kilden står dér og i `references/kilder.md`.

## Mailudkast

Kun når noget skal rettes eller afklares hos kunden eller trykkeriet. I grafikerens navn. Én mail, ét formål. Spørg, før noget sendes.

```
Emne: Stregkode på <produkt>, rettelse før tryk

Hej <navn>

Jeg har tjekket stregkoden på <fil>. Koden kan læses i filen, og nummeret passer med koden, men én ting skal rettes:

Koden er 15,70 mm høj. Ved den størrelse vi bruger, kræver GS1 mindst 18,22 mm. Målingen kan være ca. 0,05 mm
forkert, så koden er stadig for lav. Kan du gøre den højere uden at ændre bredden? Der ser ud til at være plads
over koden.

Jeg har ikke tjekket, om koden kan scannes i butikken (det kræver en verifier på prøvetrykket), og ikke
om nummeret er det rigtige for produktet. Notatet er vedhæftet og viser, hvad der er tjekket og ikke tjekket.

Hilsen <navn>
```

Til kunden, når noget skal afklares: forklar kort hvorfor, og stil ét spørgsmål. Skriv aldrig, at resten er i orden eller godkendt.
