"""Tests af måle-scriptet på opdigtede testfiler med kendt facit.

Kør fra mappen stregkodekorrektur:
    python -m unittest discover -s tests -v

Testfilerne i ../testfiler er lavet med gen.py, gen2.py og gen3.py. Facit står i cases.json
(X og højde), cases2.json (lyszoner) og cases3.json (forventet status). Nummeret 2000000000015
er fiktivt: præfiks 20 er begrænset cirkulation og er ikke tildelt en virksomhed (GS1 v26 tabel 1-4).
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROD = Path(__file__).resolve().parent.parent
SCRIPT = ROD / "scripts" / "maal.py"
TESTFILER = ROD / "testfiler"
TOL_MM = 0.05          # samme margin som scriptet bruger
TOL_X_MM = 0.001
STATUSSER = {"RET", "VURDER", "SE_SELV", "EFTER_TRYK", "IKKE_MAALT", "INGEN_FUND"}


def kør(fil, *ekstra):
    ud = Path(tempfile.mkdtemp(prefix="maal_"))
    subprocess.run([sys.executable, str(SCRIPT), str(TESTFILER / fil), "--ud", str(ud), *ekstra],
                   check=True, capture_output=True)
    return json.loads((ud / "maaling.json").read_text(encoding="utf-8"))


def tjek_af(resultat):
    alle = list(resultat["fil_tjek"])
    for k in resultat["koder"]:
        alle.extend(k["tjek"])
    return alle


def status(resultat, tjek_id):
    return {t["id"]: t["status"] for t in tjek_af(resultat)}.get(tjek_id)


class TestMaal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((TESTFILER / "cases.json").read_text())
        cls.cases2 = json.loads((TESTFILER / "cases2.json").read_text())
        cls.cases3 = json.loads((TESTFILER / "cases3.json").read_text())
        cls.res = {}
        for c in cls.cases + cls.cases2 + cls.cases3:
            navn = Path(c["fil"]).name
            cls.res[navn] = kør(navn)

    def test_x_og_hoejde_maales_praecist(self):
        for c in self.cases:
            maal = self.res[Path(c["fil"]).name]["koder"][0]["maal"]
            with self.subTest(fil=c["fil"]):
                self.assertAlmostEqual(maal["X_mm"], c["X"], delta=TOL_X_MM)
                self.assertAlmostEqual(maal["hoejde_mm"], c["hoejde"], delta=TOL_MM)

    def test_lyszoner_maales_praecist(self):
        for c in self.cases2:
            maal = self.res[c["fil"]]["koder"][0]["maal"]
            with self.subTest(fil=c["fil"]):
                self.assertAlmostEqual(maal["lyszone_v_mm"], c["gl"], delta=TOL_MM)
                self.assertAlmostEqual(maal["lyszone_h_mm"], c["gr"], delta=TOL_MM)

    def test_forventet_status_ved_grænsetilfælde(self):
        for c in self.cases3:
            forventet = c["forventet"].split(": ", 1)[1].split()[0]
            tjek_id = "tillaeg" if "+ 2" in c["forventet"] else "stoerrelse"
            with self.subTest(fil=c["fil"], forventet=c["forventet"]):
                self.assertEqual(status(self.res[c["fil"]], tjek_id), forventet)

    def test_kun_kendte_statusser_og_aldrig_godkendt(self):
        for navn, r in self.res.items():
            for t in tjek_af(r):
                with self.subTest(fil=navn, tjek=t["id"]):
                    self.assertIn(t["status"], STATUSSER)

    def test_kun_gs1_og_varedata(self):
        """Den offentlige udgave har ingen kundepraksis: hvert tjek er GS1 eller en sammenligning med varedata."""
        for navn, r in self.res.items():
            for t in tjek_af(r):
                with self.subTest(fil=navn, tjek=t["id"]):
                    self.assertIn(t["lag"], {"GS1", "varedata", None})

    def test_varenummer_sammenlignes_med_oplyst_gtin(self):
        self.assertEqual(status(kør("syn_00.pdf", "--gtin", "2000000000015"), "varenummer"), "INGEN_FUND")
        self.assertEqual(status(kør("syn_00.pdf", "--gtin", "2000000000022"), "varenummer"), "RET")
        self.assertEqual(status(self.res["syn_00.pdf"], "varenummer"), "VURDER")

    def test_demo_etiket(self):
        """Demoen: for lav kode (RET) tæt på kanten (VURDER), og formatet bekræfter målestokken."""
        r = kør("demo_etiket.pdf", "--format", "100x60")
        self.assertEqual(status(r, "hoejde"), "RET")
        self.assertEqual(status(r, "kant"), "VURDER")
        self.assertEqual(status(r, "stoerrelse"), "INGEN_FUND")
        self.assertEqual(r["sider_info"]["1"]["maalestok"]["status"], "bekraeftet")

    def test_format_bruges_til_maalestok(self):
        r = kør("syn_00.pdf", "--format", "100x60")
        self.assertEqual(r["sider_info"]["1"]["format_mm"], [100.0, 60.0])
        self.assertIn("oplyste format", r["sider_info"]["1"]["maalestok"]["tekst"])


if __name__ == "__main__":
    unittest.main()
