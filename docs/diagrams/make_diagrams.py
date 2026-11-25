"""Generates the four case-study diagrams as SVG, in Danish and English.

Run:  python3 make_diagrams.py      (writes *_da.svg and *_en.svg next to this file)
Edit the TEXT dictionary to change wording. No dependencies.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent

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
        "missing": "Mangler en måling, bliver reglen 'kan ikke tjekkes'. Systemet skriver aldrig 'godkendt'.",
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
        "done_rule": "En rettelse er først færdig, når en agent, der ikke har set facit, har gentestet den.",
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
        "missing": "A missing measurement makes the rule 'cannot check'. The system never says 'approved'.",
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
        "done_rule": "A fix is only done when an agent that has not seen the answer key has retested it.",
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
    s.box(20 + 4 * (w + gap), 200, w, 64, ["AI (v1)", "kun ved 'kan ikke tjekke'" if t is TEXT["da"] else "only on 'cannot check'"], AI, AI_BG, dash=True, size=12)
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


if __name__ == "__main__":
    for lang, t in TEXT.items():
        for name, fn in (("01_architecture", architecture), ("02_dataflow", dataflow), ("03_rules_ai_human", roles), ("04_v2_process", process)):
            (OUT / f"{name}_{lang}.svg").write_text(fn(t), encoding="utf-8")
    print("written:", sorted(p.name for p in OUT.glob("*.svg")))
