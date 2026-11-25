"""Builds PDF versions of the case studies from the Markdown files.

Run from this folder:  python3 build_pdf.py   (writes to docs/pdf/)
Needs the Python package `markdown` and Google Chrome (headless print to PDF).
"""
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "docs" / "pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 13mm 15mm 13mm 15mm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 9.4pt; line-height: 1.34; color: #1d2430; }
h1 { font-size: 20pt; color: #0f1b2d; margin: 0 0 4pt 0; }
h2 { font-size: 12pt; color: #1f5f8b; margin: 11pt 0 4pt 0; padding-bottom: 2pt; border-bottom: 0.8pt solid #c9d3de; page-break-after: avoid; }
p { margin: 0 0 5pt 0; }
ul, ol { margin: 0 0 6pt 0; padding-left: 16pt; }
li { margin: 0 0 2pt 0; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 10pt 0; font-size: 9pt; page-break-inside: avoid; }
th, td { border: 0.6pt solid #c9d3de; padding: 4pt 6pt; vertical-align: top; text-align: left; }
th { background: #e8f0f7; }
blockquote { margin: 6pt 0 10pt 0; padding: 6pt 10pt; background: #f1f3f6; border-left: 3pt solid #6b7785; font-size: 9pt; }
blockquote p { margin: 0; }
img { width: 84%; display: block; margin: 2pt auto 6pt auto; page-break-inside: avoid; }
code { font-family: Menlo, monospace; font-size: 8.5pt; }
a { color: #1f5f8b; text-decoration: none; }
em { color: #5b6675; }
"""


def build(md_name: str, pdf_name: str, title: str) -> None:
    text = (HERE / md_name).read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables"])
    html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>'
    tmp = HERE / f"_{md_name}.html"
    tmp.write_text(html, encoding="utf-8")
    out = OUT / pdf_name
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", tmp.as_uri()], check=True, capture_output=True)
    tmp.unlink()
    print("written:", out)


if __name__ == "__main__":
    build("case-study-da.md", "CameleonProof_case_study_DA.pdf", "CameleonProof - case study (dansk)")
    build("case-study-en.md", "CameleonProof_case_study_EN.pdf", "CameleonProof - case study (English)")
    sys.exit(0)
