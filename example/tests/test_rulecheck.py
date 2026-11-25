"""Tests for the synthetic example. Run from the example/ folder:

    python3 -m unittest discover -s tests -v
"""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import rulecheck as rc  # noqa: E402


def load(name: str) -> dict:
    return json.loads((HERE / "samples" / name).read_text(encoding="utf-8"))


def statuses(findings):
    return {f.rule_id: f.status for f in findings}


class SyntheticRuleCheck(unittest.TestCase):
    def setUp(self):
        self.rules, _ = rc.load_rules()

    def test_clean_label_has_no_findings_but_is_never_approved(self):
        result, findings = rc.run(load("clean.json"), self.rules)
        self.assertEqual(result, rc.OVERALL_MANUAL)
        self.assertEqual(statuses(findings)["SYN-05"], rc.MANUAL)
        self.assertNotIn("APPROVED", result)

    def test_missing_measurement_is_not_measured_and_blocks_a_clean_result(self):
        result, findings = rc.run(load("missing_measurement.json"), self.rules)
        self.assertEqual(statuses(findings)["SYN-01"], rc.NOT_MEASURED)
        self.assertEqual(result, rc.OVERALL_REVIEW)

    def test_wrong_check_digit_must_be_fixed(self):
        result, findings = rc.run(load("wrong_check_digit.json"), self.rules)
        self.assertEqual(statuses(findings)["SYN-02"], rc.FIX)
        self.assertEqual(result, rc.OVERALL_FIX)

    def test_borderline_and_low_confidence_go_to_review(self):
        result, findings = rc.run(load("borderline.json"), self.rules)
        s = statuses(findings)
        self.assertEqual(s["SYN-01"], rc.REVIEW)  # 3.47 mm, inside the 0.05 mm margin
        self.assertEqual(s["SYN-03"], rc.REVIEW)  # low-confidence measurement
        self.assertEqual(result, rc.OVERALL_REVIEW)

    def test_unreadable_text_is_not_treated_as_missing_text(self):
        _, findings = rc.run(load("unreadable_text.json"), self.rules)
        self.assertEqual(statuses(findings)["SYN-04"], rc.NOT_MEASURED)

    def test_removing_any_measurement_never_yields_no_finding(self):
        """Property: for every measured rule, deleting its input must not pass."""
        clean = load("clean.json")
        for rule in self.rules:
            if "field" not in rule:
                continue
            facts = copy.deepcopy(clean)
            facts["measurements"][rule["field"]] = None
            finding = rc.check_rule(rule, facts)
            self.assertEqual(finding.status, rc.NOT_MEASURED, rule["id"])

    def test_gtin_check_digit(self):
        self.assertTrue(rc.gtin_check_digit_ok("2000000123455"))
        self.assertFalse(rc.gtin_check_digit_ok("2000000123456"))
        self.assertFalse(rc.gtin_check_digit_ok("20000001234X5"))


if __name__ == "__main__":
    unittest.main()
