"""Synthetic, illustrative rule check. NOT the CameleonProof implementation.

Written for this portfolio to show two design principles in a few lines:

1. Rules are data, not code. Each rule card names its threshold, its
   measurement margin and its source.
2. A missing or uncertain measurement is never a pass. The engine reports
   what it could not check, and the overall result is never "approved".

The rules, thresholds and sample labels are fictitious. The only real
algorithm here is the public GS1 mod-10 check digit.

Usage:
    python3 rulecheck.py samples/clean.json
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

RULES_FILE = Path(__file__).parent / "rules" / "synthetic_rules.json"

# Per-rule statuses
FIX = "FIX"                    # clearly outside the requirement
REVIEW = "REVIEW"              # within the measurement margin, or low confidence
NOT_MEASURED = "NOT_MEASURED"  # the measurement is missing
MANUAL = "MANUAL"              # a person has to look; the engine does not judge
NO_FINDING = "NO_FINDING"      # measured, and inside the requirement

# Overall results. There is deliberately no "APPROVED".
OVERALL_FIX = "FIX_REQUIRED"
OVERALL_REVIEW = "REVIEW_REQUIRED"
OVERALL_MANUAL = "NO_FINDINGS_PENDING_MANUAL_CHECKS"
OVERALL_CLEAN = "NO_FINDINGS_ON_CHECKED_ITEMS"


@dataclass
class Finding:
    rule_id: str
    status: str
    detail: str
    source: str


def gtin_check_digit_ok(gtin: str) -> bool:
    """Public GS1 mod-10 algorithm. Deterministic code, no AI needed."""
    if not gtin.isdigit() or len(gtin) not in (8, 12, 13, 14):
        return False
    body, check = gtin[:-1], int(gtin[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def _measurement(facts: dict, field: str) -> dict | None:
    m = facts.get("measurements", {}).get(field)
    if m is None or m.get("value") is None:
        return None
    return m


def check_rule(rule: dict, facts: dict) -> Finding:
    rid, src, kind = rule["id"], rule["source"], rule["kind"]

    if kind == "manual":
        return Finding(rid, MANUAL, rule["question"], src)

    if kind == "presence":
        texts = facts.get("texts")
        if texts is None:  # text extraction failed; absence is not proven
            return Finding(rid, NOT_MEASURED, "text could not be read", src)
        found = any(rule["text"].lower() in t.lower() for t in texts)
        return Finding(rid, NO_FINDING if found else FIX,
                       f"'{rule['text']}' {'found' if found else 'not found'}", src)

    m = _measurement(facts, rule["field"])
    if m is None:
        return Finding(rid, NOT_MEASURED, f"no measurement for {rule['field']}", src)

    if kind == "checksum":
        ok = gtin_check_digit_ok(str(m["value"]))
        return Finding(rid, NO_FINDING if ok else FIX,
                       f"check digit {'valid' if ok else 'invalid'} ({m['value']})", src)

    if kind == "minimum":
        value, limit, margin = float(m["value"]), rule["min"], rule["margin"]
        detail = f"{value} {rule['unit']} measured, minimum {limit} {rule['unit']} (margin {margin})"
        if m.get("confidence") == "low":
            return Finding(rid, REVIEW, detail + ", low-confidence measurement", src)
        if value < limit - margin:
            return Finding(rid, FIX, detail, src)
        if value < limit:
            return Finding(rid, REVIEW, detail + ", within the measurement margin", src)
        return Finding(rid, NO_FINDING, detail, src)

    raise ValueError(f"unknown rule kind: {kind}")


def overall(findings: list[Finding]) -> str:
    statuses = {f.status for f in findings}
    if FIX in statuses:
        return OVERALL_FIX
    if statuses & {REVIEW, NOT_MEASURED}:
        return OVERALL_REVIEW
    if MANUAL in statuses:
        return OVERALL_MANUAL
    return OVERALL_CLEAN


def run(facts: dict, rules: list[dict]) -> tuple[str, list[Finding]]:
    findings = [check_rule(r, facts) for r in rules]
    return overall(findings), findings


def load_rules() -> tuple[list[dict], list[str]]:
    data = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    return data["rules"], data["not_covered"]


def main(path: str) -> None:
    rules, not_covered = load_rules()
    facts = json.loads(Path(path).read_text(encoding="utf-8"))
    result, findings = run(facts, rules)
    print(f"Label: {facts.get('label_id', path)}  (synthetic example)")
    for f in findings:
        print(f"  {f.rule_id:7} {f.status:13} {f.detail}  [{f.source}]")
    print(f"Overall: {result}")
    print("Not checked by this example: " + "; ".join(not_covered))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent / "samples" / "clean.json"))
