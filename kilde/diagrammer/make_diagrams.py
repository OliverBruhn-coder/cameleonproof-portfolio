"""Tegner portefoljens diagrammer som SVG paa dansk og engelsk.

Koer:  python3 make_diagrams.py   (skriver til docs/assets/diagrams/)
Ret ordlyden i TEXT og TEXT2. Ingen afhaengigheder.

Diagram 05 til 10 er tegnet efter Olivers egne AS-IS- og TO-BE-diagrammer og beslutningsnoter,
uden navne paa kunder og personer. 01 til 04 er tegnet efter projektets filer.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "diagrams"

INK, MUTED = "#0f1b2d", "#5b6675"
CODE, CODE_BG = "#1f5f8b", "#e8f0f7"
AI, AI_BG = "#b7791f", "#fbf1e1"
HUMAN, HUMAN_BG = "#2e7d5b", "#e6f2ec"
INFRA, INFRA_BG = "#6b7785", "#f1f3f6"
WARN, WARN_BG = "#b3412e", "#fbe9e6"
FONT = "Helvetica, Arial, sans-serif"


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.parts = w, h, []
        self.title = title

    def box(self, x, y, w, h, lines, stroke=CODE, fill=CODE_BG, bold_first=True, size=13, dash=False, rx=8, align="middle"):
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>')
        lh = size * 1.32
        top = y + h / 2 - (len(lines) - 1) * lh / 2 + size * 0.35
        tx = x + w / 2 if align == "middle" else x + 12
        for i, line in enumerate(lines):
            weight = "700" if (i == 0 and bold_first) else "400"
            col = INK if i == 0 else MUTED
            s = size if i == 0 else size - 1.5
            self.parts.append(f'<text x="{tx}" y="{top + i * lh:.1f}" text-anchor="{align}" font-size="{s}" font-weight="{weight}" fill="{col}">{escape(line)}</text>')

    def group(self, x, y, w, h, label, stroke=INFRA, fill="#ffffff"):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.4" stroke-dasharray="6 5"/>')
        self.parts.append(f'<text x="{x + 14}" y="{y + 22}" font-size="13" font-weight="700" fill="{stroke}">{escape(label)}</text>')

    def arrow(self, x1, y1, x2, y2, label=None, color=INFRA, dash=False, lx=None, ly=None):
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.8" marker-end="url(#a-{color[1:]})"{d}/>')
        if label:
            lx = (x1 + x2) / 2 if lx is None else lx
            ly = (y1 + y2) / 2 - 6 if ly is None else ly
            self.parts.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11.5" fill="{MUTED}">{escape(label)}</text>')

    def text(self, x, y, s, size=12, color=MUTED, anchor="start", weight="400"):
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(s)}</text>')

    def render(self):
        markers = "".join(
            f'<marker id="a-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
            for c in (INFRA, CODE, AI, HUMAN, WARN))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" font-family="{FONT}">'
                f'<title>{escape(self.title)}</title><defs>{markers}</defs>'
                f'<rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.parts) + "</svg>")


TEXT = {
    "da": {
        "arch_title": "CameleonProof v1: overordnet systemarkitektur",
        "machine": "Medarbejderens maskine",
        "server": "Server (Docker bag HTTPS)",
        "browser": ["Browser", "upload og gennemgang"],
        "connector": ["Lokal connector", "kun læsning, kun lokalt"],
        "share": ["Bureauets filserver", "produktdata, fx varenummer"],
        "webapp": ["Webapplikation (FastAPI)", "login, adgang pr. sag"],
        "pipeline": ["Korrekturpipeline", "læs, kalibrér, mål, vurdér"],
        "rules": ["Regelkort (YAML)", "110 i alt, 42 aktive i fladen"],
        "sources": ["Kilderegister", "side og ordret citat"],
        "db": ["Database (SQLite)", "sager, kørsler, fund, vurderinger"],
        "report": ["Rapport", "JSON og HTML"],
        "vision": ["Claude vision", "kun ved 'kan ikke tjekke',", "højst rådgivende"],
        "ci": ["GitHub Actions", "2.179 testcases og regressionsbaseline,", "deploy kun når alt er grønt"],
        "pdf": "PDF og produktdata",
        "ask": "spørger om produktdata",
        "never": "serveren når aldrig filserveren",
        "flow_title": "Dataflow fra upload til resultat",
        "steps": [
            ["1. Upload", "PDF hashes,", "sag registreres"],
            ["2. Læs artwork", "PDF-struktur,", "OCR som fallback"],
            ["3. Skala", "mm fra format,", "krydstjek mod ramme"],
            ["4. Hvilke regler?", "gælder, gælder ikke,", "mangler grundlag"],
            ["5. Mål", "almindelig kode,", "med måleusikkerhed"],
            ["6. Status pr. regel", "og kilde-", "henvisning"],
            ["7. Rapport", "til designer og", "korrekturlæser"],
        ],
        "out": [["Skal rettes", "målt uden for kravet"], ["Kræver vurdering", "tæt på grænsen eller usikker"],
                ["Kan ikke tjekkes", "måling mangler, aldrig bestået"], ["Ingen fund", "på de tjekkede punkter"]],
        "missing": "Mangler en måling, bliver reglen 'kan ikke tjekkes'. Aldrig 'bestået' uden måling.",
        "roles_title": "Samspillet mellem regelmotor, AI og menneske",
        "lane_code": "Regelmotor (almindelig kode)",
        "lane_ai": "AI (sprogmodel)",
        "lane_human": "Menneske",
        "code_items": ["Måler stregkode, cifferhøjde, afstande", "Sammenligner med tærskel og margin", "Giver: skal rettes / ingen fund /", "kan ikke tjekkes", "Samme input giver samme svar"],
        "ai_items": ["Læser kontekst og tekst", "Foreslår placering, når layout svigter", "(v1: højst rådgivende)", "Skriver rapporten i klart sprog", "Laver uafhængige testvarianter"],
        "human_items": ["Afgør 'kræver vurdering'", "Kender kundeaftaler og undtagelser", "Kan acceptere en afvigelse,", "men dommen står", "Godkender regler og kilder"],
        "verdict": "Kun regelmotoren kan give en dom. AI kan foreslå, mennesket afgør det, der kræver skøn.",
        "proc_title": "CameleonProof v2: ét regelområde ad gangen",
        "proc": [
            ["1. Afgræns", "områdeark"],
            ["2. Kilder", "primærkilder,", "version, SHA-256"],
            ["3. Tjekpunkter", "ID pegende på", "kilde-ID"],
            ["4. Skill", "målescript +", "SKILL.md"],
            ["5. Test", "rene filer,", "kendte fejl"],
            ["6. Blindtest", "frisk agent", "uden facit"],
            ["7. Pilot", "konkrete", "korrekturopgaver"],
        ],
        "loop": "Hver fejl, der slipper igennem, bliver en ny testfil",
        "done_rule": "Først færdig, når en agent uden facit har gentestet den, og alle resultater er rigtige.",
        "areas": "Bygget indtil nu: stregkode (v2.1), nettoindhold og ℮-mærke (v0.6), allergener (v0.1)",
    },
    "en": {
        "arch_title": "CameleonProof v1: system architecture",
        "machine": "Employee's machine",
        "server": "Server (Docker behind HTTPS)",
        "browser": ["Browser", "upload and review"],
        "connector": ["Local connector", "read-only, local only"],
        "share": ["Agency file share", "product facts, e.g. GTIN"],
        "webapp": ["Web application (FastAPI)", "login, access per case"],
        "pipeline": ["Proofing pipeline", "read, calibrate, measure, judge"],
        "rules": ["Rule cards (YAML)", "110 in total, 42 active in the UI"],
        "sources": ["Source registry", "page and verbatim quote"],
        "db": ["Database (SQLite)", "cases, runs, findings, reviews"],
        "report": ["Report", "JSON and HTML"],
        "vision": ["Claude vision", "only on 'cannot check',", "advisory at most"],
        "ci": ["GitHub Actions", "2,179 test cases and regression baseline,", "deploy only when all green"],
        "pdf": "PDF and product facts",
        "ask": "asks for product facts",
        "never": "the server never reaches the file share",
        "flow_title": "Data flow from upload to result",
        "steps": [
            ["1. Upload", "PDF hashed,", "case registered"],
            ["2. Read artwork", "PDF structure,", "OCR as fallback"],
            ["3. Scale", "mm from format,", "cross-check frame"],
            ["4. Which rules?", "applies, does not,", "lacks evidence"],
            ["5. Measure", "plain code,", "with uncertainty"],
            ["6. Status per rule", "and source", "citation"],
            ["7. Report", "for designer and", "proofreader"],
        ],
        "out": [["Must fix", "measured outside the requirement"], ["Needs judgement", "near the limit or uncertain"],
                ["Cannot check", "measurement missing, never a pass"], ["No findings", "on the items checked"]],
        "missing": "A missing measurement makes the rule 'cannot check'. Never 'pass' without a measurement.",
        "roles_title": "How the rule engine, AI and people share the work",
        "lane_code": "Rule engine (plain code)",
        "lane_ai": "AI (language model)",
        "lane_human": "Person",
        "code_items": ["Measures barcode, digit height, distances", "Compares with threshold and margin", "Returns: must fix / no finding /", "cannot check", "Same input, same answer"],
        "ai_items": ["Reads context and text", "Suggests location when layout fails", "(v1: advisory at most)", "Writes the report in plain language", "Creates independent test variants"],
        "human_items": ["Decides 'needs judgement'", "Knows client agreements and exceptions", "Can accept a deviation,", "but the verdict stands", "Approves rules and sources"],
        "verdict": "Only the rule engine gives a verdict. AI can suggest; a person decides what needs judgement.",
        "proc_title": "CameleonProof v2: one rule area at a time",
        "proc": [
            ["1. Scope", "area sheet"],
            ["2. Sources", "primary sources,", "version, SHA-256"],
            ["3. Checkpoints", "each ID points", "to a source ID"],
            ["4. Skill", "measuring script", "+ SKILL.md"],
            ["5. Test", "clean files,", "known faults"],
            ["6. Blind test", "fresh agent,", "no answer key"],
            ["7. Pilot", "real proofing", "tasks"],
        ],
        "loop": "Every fault that slips through becomes a new test file",
        "done_rule": "Done only when an agent without the answer key has retested it and every result is correct.",
        "areas": "Built so far: barcode (v2.1), net quantity and e-mark (v0.6), allergens (v0.1)",
    },
}


def architecture(t):
    s = Svg(960, 560, t["arch_title"])
    s.text(20, 30, t["arch_title"], 17, INK, weight="700")
    s.group(20, 50, 280, 400, t["machine"])
    s.box(45, 90, 230, 66, t["browser"], INFRA, INFRA_BG)
    s.box(45, 230, 230, 66, t["connector"], INFRA, INFRA_BG)
    s.box(45, 360, 230, 66, t["share"], INFRA, INFRA_BG)
    s.arrow(160, 156, 160, 228, t["ask"], lx=230, ly=196)
    s.arrow(160, 296, 160, 358)
    s.group(360, 50, 580, 400, t["server"])
    s.box(385, 90, 250, 66, t["webapp"], CODE, CODE_BG)
    s.box(385, 200, 250, 66, t["pipeline"], CODE, CODE_BG)
    s.box(670, 90, 245, 56, t["rules"], CODE, CODE_BG)
    s.box(670, 160, 245, 56, t["sources"], CODE, CODE_BG)
    s.box(670, 230, 245, 56, t["db"], CODE, CODE_BG)
    s.box(670, 300, 245, 56, t["report"], CODE, CODE_BG)
    s.box(385, 320, 250, 80, t["vision"], AI, AI_BG, dash=True)
    s.arrow(275, 123, 383, 123)
    s.text(326, 108, t["pdf"], 10.5, MUTED, anchor="middle")
    s.arrow(510, 156, 510, 198)
    s.arrow(635, 220, 668, 118)
    s.arrow(635, 228, 668, 188)
    s.arrow(635, 240, 668, 258)
    s.arrow(635, 250, 668, 322)
    s.arrow(510, 318, 510, 268, color=AI, dash=True)
    s.text(160, 472, t["never"], 11.5, WARN, anchor="middle")
    s.box(360, 470, 580, 74, t["ci"], HUMAN, HUMAN_BG)
    s.arrow(650, 470, 650, 452, color=HUMAN)
    return s.render()


def dataflow(t):
    s = Svg(1000, 420, t["flow_title"])
    s.text(20, 30, t["flow_title"], 17, INK, weight="700")
    w, gap, y = 126, 16, 60
    for i, step in enumerate(t["steps"]):
        x = 20 + i * (w + gap)
        color, bg = (CODE, CODE_BG)
        s.box(x, y, w, 96, step, color, bg, size=12.5)
        if i < len(t["steps"]) - 1:
            s.arrow(x + w, y + 48, x + w + gap - 1, y + 48, color=CODE)
    s.box(20 + 4 * (w + gap), 200, w, 64, ["AI (v1)", "kun ved 'kan ikke tjekke'" if t["flow_title"].startswith("Dataflow fra") else "only on 'cannot check'"], AI, AI_BG, dash=True, size=12)
    s.arrow(20 + 4 * (w + gap) + w / 2, 200, 20 + 4 * (w + gap) + w / 2, 158, color=AI, dash=True)
    cols = [(WARN, WARN_BG), (AI, AI_BG), (INFRA, INFRA_BG), (HUMAN, HUMAN_BG)]
    ow, ox = 230, 20
    for i, (lines, (c, bg)) in enumerate(zip(t["out"], cols)):
        s.box(ox + i * (ow + 16), 300, ow, 64, lines, c, bg, size=13)
    xr = 20 + 6 * (w + gap) + w / 2
    s.parts.append(f'<path d="M{xr},156 L{xr},280 L{ox + ow / 2},280" fill="none" stroke="{CODE}" stroke-width="1.8"/>')
    for i in range(4):
        cx = ox + i * (ow + 16) + ow / 2
        s.arrow(cx, 280, cx, 297, color=CODE)
    s.text(500, 400, t["missing"], 12.5, INK, anchor="middle", weight="700")
    return s.render()


def roles(t):
    s = Svg(960, 356, t["roles_title"])
    s.text(20, 30, t["roles_title"], 17, INK, weight="700")
    lanes = [(t["lane_code"], t["code_items"], CODE, CODE_BG), (t["lane_ai"], t["ai_items"], AI, AI_BG), (t["lane_human"], t["human_items"], HUMAN, HUMAN_BG)]
    for i, (name, items, c, bg) in enumerate(lanes):
        x = 20 + i * 315
        s.box(x, 55, 290, 200, [name] + [""] + items, c, bg, size=14, align="start")
    s.arrow(310, 155, 333, 155, color=CODE)
    s.arrow(625, 155, 648, 155, color=AI)
    s.box(20, 280, 920, 56, [t["verdict"]], INK, "#ffffff", size=14)
    return s.render()


def process(t):
    s = Svg(1000, 345, t["proc_title"])
    s.text(20, 30, t["proc_title"], 17, INK, weight="700")
    w, gap, y = 124, 18, 60
    for i, step in enumerate(t["proc"]):
        x = 20 + i * (w + gap)
        c, bg = (HUMAN, HUMAN_BG) if i == 6 else ((AI, AI_BG) if i == 5 else (CODE, CODE_BG))
        s.box(x, y, w, 90, step, c, bg, size=12.5)
        if i < len(t["proc"]) - 1:
            s.arrow(x + w, y + 45, x + w + gap - 1, y + 45, color=CODE)
    # feedback loop from pilot back to test
    x_pilot = 20 + 6 * (w + gap) + w / 2
    x_test = 20 + 4 * (w + gap) + w / 2
    s.parts.append(f'<path d="M{x_pilot},{y + 90} L{x_pilot},{y + 140} L{x_test},{y + 140} L{x_test},{y + 92}" fill="none" stroke="{WARN}" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#a-{WARN[1:]})"/>')
    s.text((x_pilot + x_test) / 2, y + 160, t["loop"], 12, WARN, anchor="middle")
    s.box(20, 250, 960, 44, [t["done_rule"]], INK, "#ffffff", size=13.5)
    s.text(500, 325, t["areas"], 12.5, MUTED, anchor="middle")
    return s.render()



TEXT2 = {
    "da": {
        "tl_title": "Forløbet: fra speciale til én skill pr. regelområde",
        "tl": [
            ("2025", ["Speciale om", "prissætning.", "Behovet ses"]),
            ("Feb 2026", ["Version 1", "startes som", "websystem"]),
            ("Jul 2026", ["Afgrænsning.", "Først kun", "bureauets filer"]),
            ("Aug 2026", ["Revision af", "fødevarereglerne:", "5 falske godkendelser"]),
            ("Sep 2026", ["På server bag", "HTTPS. AS-IS-", "revision af koden"]),
            ("Okt 2026", ["Grilling:", "15 beslutninger,", "de tre prøver"]),
            ("Nov 2026", ["TO-BE med", "12 moduler", "og brugerrejse"]),
            ("21. nov 2026", ["Retningsskift:", "én skill pr.", "regelområde"]),
        ],
        "tl_now": "Nu: de nye skills afprøves i et pilotforløb med konkrete korrekturopgaver",
        "rev_title": "Revisionen: hvad den fandt, og hvad jeg besluttede",
        "rev_checked": "Efterprøvet",
        "rev_found": "Fund",
        "rev_decided": "Besluttet",
        "rev_rows": [
            (["Fødevarereglerne", "august 2026"], ["5 måder, en fejl kunne", "slippe igennem som bestået"]),
            (["Testdækning", "august 2026"], ["37 af 52 regler havde aldrig", "udløst deres fejlgren"]),
            (["31 syntetiske fejlfiler", "september 2026"], ["30 af 42 regler fangede fejlen,", "6 reagerede ikke"]),
            (["Hele koden (AS-IS)", "september 2026"], ["Hvert udsagn mærket", "VERIFIED, PARTIAL eller UNKNOWN"]),
        ],
        "rev_conclusion": ["Reglerne var bedre til", "at frikende end til", "at dømme"],
        "rev_dec": [
            ["Ubeviste regler skjules", "fødevarereglerne vises ikke,", "før de har bestået"],
            ["De tre prøver", "før en regel må", "give en rød fejl"],
            ["Retningsskift", "ét regelområde ad gangen,", "som en skill"],
        ],
        "mat_title": "Modenhed: en regel skal bevise, at den kan fange en fejl",
        "mat": [
            (["SKJULT", "Ikke valideret endnu.", "Vises ikke. Kører kun", "i valideringen"], "INFRA"),
            (["TJEK", "Ingen falske fejl, men aldrig", "set dumpe, eller kilden er", "ikke bekræftet. Højst", "'tjek dette', blokerer aldrig"], "AI"),
            (["BEVIST", "Har bestået alle", "tre prøver.", "Kan give en rød fejl"], "HUMAN"),
        ],
        "mat_tests": ["De tre prøver", "1. Ingen falske røde fejl på godkendte filer",
                      "2. Set dumpe mindst én gang, på en", "    rigtig eller en syntetisk fejl", "3. Fangstraten er målt"],
        "abs_title": "Når noget forventet ikke er der, kræver hver forklaring sin egen handling",
        "abs": [
            (["Ikke endnu", "Forventes senere,", "fx i en senere", "korrekturrunde"], "INFRA"),
            (["Andres ansvar", "En anden part", "står inde for det"], "INFRA"),
            (["Ikke relevant", "Hører til en", "anden flade.", "Skrives med navn"], "INFRA"),
            (["Mangler", "Skal være der nu", "og er der ikke.", "Fejl, hvis bevist"], "WARN"),
            (["Forkert", "Er der, men", "stemmer ikke.", "Fejl, hvis bevist"], "WARN"),
        ],
        "abs_foot": ["Fase og ansvar afgør tilstanden. Er de ukendte, gætter systemet ikke, men viser 'tjek'.",
                     "'Kan ikke tjekke' er systemets egen blindhed, ikke en sjette tilstand."],
        "jr_title": "Brugerrejsen: fra syv trin til fire",
        "jr_old_label": "Version 1",
        "jr_old": [["Log ind"], ["Upload"], ["Bekræft", "sag"], ["Tast", "varenummer"], ["Vælg emballage", "og diameter"], ["Vent uden", "fremdrift"], ["Læs alle regler", "i tre faner"]],
        "jr_new_label": "TO-BE",
        "jr_new": [["Log ind"], ["Slip PDF'en"], ["Se fremdrift"], ["Læs kun det, der", "kræver handling"]],
        "jr_foot": "Formularen vises kun, når noget mangler eller er i konflikt. Fakta hentes af forbindelsen på medarbejderens maskine.",
        "me_title": "Metoden vælges pr. opgave, men kvalitetskravet er det samme",
        "me_center": ["Den bedste løsning", "det konkrete sted"],
        "me_opts": ["Kode", "AI", "Værktøj", "Skill", "Workflow", "En blanding"],
        "me_rules": [
            ["Samme kvalitetskrav", "En kontrol vises først, når den har", "bestået de tre prøver, uanset metode"],
            ["Kan svaret variere, er det et forslag", "Vises som 'tjek dette'.", "Et menneske bekræfter"],
            ["Data bliver, hvor de må være", "Kundens filer går kun derhen,", "hvor bureauet har sagt ja"],
        ],
    },
    "en": {
        "tl_title": "The journey: from thesis to one skill per rule area",
        "tl": [
            ("2025", ["Thesis on", "pricing. The", "need is spotted"]),
            ("Feb 2026", ["Version 1", "starts as a", "web system"]),
            ("Jul 2026", ["Scope set.", "The agency's", "own files first"]),
            ("Aug 2026", ["Audit of the", "food rules:", "5 false passes"]),
            ("Sep 2026", ["On a server", "behind HTTPS.", "AS-IS code audit"]),
            ("Oct 2026", ["Grilling:", "15 decisions,", "the three tests"]),
            ("Nov 2026", ["TO-BE with", "12 modules", "and user journey"]),
            ("21 Nov 2026", ["Change of", "direction: one", "skill per area"]),
        ],
        "tl_now": "Now: the new skills are being tried in a pilot with real proofing tasks",
        "rev_title": "The audit: what it found, and what I decided",
        "rev_checked": "Checked",
        "rev_found": "Found",
        "rev_decided": "Decided",
        "rev_rows": [
            (["The food rules", "August 2026"], ["5 ways an error could", "slip through as a pass"]),
            (["Test coverage", "August 2026"], ["37 of 52 rules had never", "triggered their fail branch"]),
            (["31 synthetic error files", "September 2026"], ["30 of 42 rules caught the error,", "6 did not react"]),
            (["All the code (AS-IS)", "September 2026"], ["Every claim marked", "VERIFIED, PARTIAL or UNKNOWN"]),
        ],
        "rev_conclusion": ["The rules were better", "at acquitting than", "at convicting"],
        "rev_dec": [
            ["Unproven rules hidden", "the food rules stay hidden", "until they pass"],
            ["The three tests", "before a rule may", "raise a red fail"],
            ["Change of direction", "one rule area at a time,", "as a skill"],
        ],
        "mat_title": "Maturity: a rule must prove it can catch an error",
        "mat": [
            (["HIDDEN", "Not validated yet.", "Not shown. Runs only", "in validation"], "INFRA"),
            (["CHECK", "No false fails, but never", "seen failing, or the source", "is not confirmed. At most", "'check this', never blocks"], "AI"),
            (["PROVEN", "Has passed all", "three tests.", "May raise a red fail"], "HUMAN"),
        ],
        "mat_tests": ["The three tests", "1. No false red fails on approved files",
                      "2. Seen failing at least once, on a", "    real or a synthetic error", "3. The catch rate is measured"],
        "abs_title": "When something expected is missing, each explanation needs its own action",
        "abs": [
            (["Not yet", "Expected later,", "e.g. in a later", "proofing round"], "INFRA"),
            (["Someone else's", "Another party", "vouches for it"], "INFRA"),
            (["Not relevant", "Belongs to another", "surface. Named", "explicitly"], "INFRA"),
            (["Missing", "Should be there", "now and is not.", "Fail if proven"], "WARN"),
            (["Wrong", "Is there, but", "does not match.", "Fail if proven"], "WARN"),
        ],
        "abs_foot": ["Phase and responsibility decide the state. If they are unknown, the system does not guess but shows 'check'.",
                     "'Cannot check' is the system's own blindness, not a sixth state."],
        "jr_title": "The user journey: from seven steps to four",
        "jr_old_label": "Version 1",
        "jr_old": [["Log in"], ["Upload"], ["Confirm", "case"], ["Type", "GTIN"], ["Pick package", "and diameter"], ["Wait with no", "progress"], ["Read every rule", "in three tabs"]],
        "jr_new_label": "TO-BE",
        "jr_new": [["Log in"], ["Drop the PDF"], ["See progress"], ["Read only what", "needs action"]],
        "jr_foot": "The form appears only when something is missing or in conflict. Facts are fetched by the connector on the employee's machine.",
        "me_title": "The method is chosen per task, but the quality bar is the same",
        "me_center": ["The best solution", "for that exact spot"],
        "me_opts": ["Code", "AI", "Tool", "Skill", "Workflow", "A mix"],
        "me_rules": [
            ["Same quality bar", "A check is shown only after it has", "passed the three tests, whatever the method"],
            ["If the answer can vary, it is a suggestion", "Shown as 'check this'.", "A person confirms"],
            ["Data stays where it may be", "Client files only go where", "the agency has said yes"],
        ],
    },
}
COL = {"INFRA": (INFRA, INFRA_BG), "AI": (AI, AI_BG), "HUMAN": (HUMAN, HUMAN_BG), "WARN": (WARN, WARN_BG), "CODE": (CODE, CODE_BG)}


def timeline(t):
    s = Svg(1000, 360, t["tl_title"])
    s.text(20, 30, t["tl_title"], 17, INK, weight="700")
    n = len(t["tl"])
    x0, x1, y = 70, 930, 175
    s.parts.append(f'<line x1="{x0 - 30}" y1="{y}" x2="{x1 + 40}" y2="{y}" stroke="{INFRA}" stroke-width="2"/>')
    for i, (dato, linjer) in enumerate(t["tl"]):
        x = x0 + i * (x1 - x0) / (n - 1)
        c = HUMAN if i == n - 1 else (WARN if i in (3, 4) else CODE)
        s.parts.append(f'<circle cx="{x:.1f}" cy="{y}" r="7" fill="#ffffff" stroke="{c}" stroke-width="2.4"/>')
        op = i % 2 == 0
        ty = y - 30 if op else y + 38
        s.text(x, ty if op else ty, dato, 13, c, anchor="middle", weight="700")
        for j, l in enumerate(linjer):
            yy = (ty - 18 * (len(linjer) - j)) if op else (ty + 18 * (j + 1))
            s.text(x, yy, l, 12, INK if j == 0 else MUTED, anchor="middle")
    s.box(20, 300, 960, 40, [t["tl_now"]], HUMAN, HUMAN_BG, size=13.5)
    return s.render()


def revision(t):
    s = Svg(1000, 470, t["rev_title"])
    s.text(20, 30, t["rev_title"], 17, INK, weight="700")
    for x, h in ((20, t["rev_checked"]), (250, t["rev_found"]), (720, t["rev_decided"])):
        s.text(x, 62, h.upper(), 11.5, MUTED, weight="700")
    for i, (chk, fund) in enumerate(t["rev_rows"]):
        y = 74 + i * 92
        s.box(20, y, 200, 72, chk, INFRA, INFRA_BG, size=13)
        s.box(250, y, 250, 72, fund, WARN, WARN_BG, size=12.5, bold_first=False)
        s.arrow(220, y + 36, 248, y + 36)
        s.arrow(500, y + 36, 528, 236 + (i - 1.5) * 18, color=WARN)
    s.box(530, 186, 160, 100, t["rev_conclusion"], INK, "#ffffff", size=13, bold_first=False)
    for i, d in enumerate(t["rev_dec"]):
        y = 96 + i * 102
        s.box(720, y, 260, 80, d, HUMAN, HUMAN_BG, size=13)
        s.arrow(690, 236, 718, y + 40, color=HUMAN)
    return s.render()


def maturity(t):
    s = Svg(1000, 400, t["mat_title"])
    s.text(20, 30, t["mat_title"], 17, INK, weight="700")
    for i, (linjer, col) in enumerate(t["mat"]):
        c, bg = COL[col]
        x, y, h = 20 + i * 215, 230 - i * 70, 120 + i * 70
        s.box(x, y, 200, h, linjer, c, bg, size=13.5)
    s.box(670, 160, 310, 160, t["mat_tests"], HUMAN, "#ffffff", size=13, align="start")
    return s.render()


def absence(t):
    s = Svg(1000, 330, t["abs_title"])
    s.text(20, 30, t["abs_title"], 17, INK, weight="700")
    for i, (linjer, col) in enumerate(t["abs"]):
        c, bg = COL[col]
        s.box(20 + i * 194, 60, 178, 140, linjer, c, bg, size=13.5)
    s.box(20, 230, 960, 70, t["abs_foot"], INK, "#ffffff", size=13, bold_first=False)
    return s.render()


def journey(t):
    s = Svg(1000, 330, t["jr_title"])
    s.text(20, 30, t["jr_title"], 17, INK, weight="700")
    s.text(20, 66, t["jr_old_label"].upper(), 11.5, MUTED, weight="700")
    w, gap = 122, 17
    for i, step in enumerate(t["jr_old"]):
        x = 20 + i * (w + gap)
        s.box(x, 78, w, 60, step, INFRA, INFRA_BG, size=12.5, bold_first=False)
        if i < len(t["jr_old"]) - 1:
            s.arrow(x + w, 108, x + w + gap - 1, 108)
    s.text(20, 176, t["jr_new_label"].upper(), 11.5, MUTED, weight="700")
    w2, gap2 = 220, 26
    for i, step in enumerate(t["jr_new"]):
        x = 20 + i * (w2 + gap2)
        s.box(x, 188, w2, 60, step, HUMAN, HUMAN_BG, size=13, bold_first=False)
        if i < len(t["jr_new"]) - 1:
            s.arrow(x + w2, 218, x + w2 + gap2 - 1, 218, color=HUMAN)
    s.text(500, 290, t["jr_foot"], 12.5, INK, anchor="middle")
    return s.render()


def method(t):
    s = Svg(1000, 400, t["me_title"])
    s.text(20, 30, t["me_title"], 17, INK, weight="700")
    s.box(390, 60, 220, 60, t["me_center"], INK, "#ffffff", size=14)
    w, gap = 140, 20
    tot = len(t["me_opts"]) * w + (len(t["me_opts"]) - 1) * gap
    x0 = (1000 - tot) / 2
    for i, o in enumerate(t["me_opts"]):
        x = x0 + i * (w + gap)
        c, bg = (AI, AI_BG) if i == 1 else ((CODE, CODE_BG) if i == 0 else (INFRA, INFRA_BG))
        s.box(x, 160, w, 44, [o], c, bg, size=13.5)
        s.arrow(500, 120, x + w / 2, 158, color=INFRA)
    for i, r in enumerate(t["me_rules"]):
        s.box(20 + i * 327, 250, 306, 110, r, HUMAN, HUMAN_BG, size=13)
    return s.render()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ("da", "en"):
        t = {**TEXT[lang], **TEXT2[lang]}
        for name, fn in (("01_architecture", architecture), ("02_dataflow", dataflow), ("03_rules_ai_human", roles),
                         ("04_v2_process", process), ("05_timeline", timeline), ("06_revision", revision),
                         ("07_maturity", maturity), ("08_absence", absence), ("09_journey", journey), ("10_method", method)):
            (OUT / f"{name}_{lang}.svg").write_text(fn(t), encoding="utf-8")
    print("written:", len(list(OUT.glob("*.svg"))), "SVG files in", OUT)
