"""Boundary cases from Cargo's requirement semantics and Project Z pins."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cargo_versions import satisfies


class CargoVersionTests(unittest.TestCase):
    def check_cases(self, cases):
        for version, requirement, expected in cases:
            with self.subTest(version=version, requirement=requirement):
                self.assertEqual(satisfies(version, requirement), expected)

    def test_project_z_exact_pins(self):
        self.check_cases([
            ("0.4.0", "=0.4.0", True),
            ("0.4.1", "=0.4.0", False),
            ("0.3.1", "=0.3.0", False),
            ("0.1.1-alpha.3", "=0.1.1-alpha.3", True),
            ("0.1.1-alpha.4", "=0.1.1-alpha.3", False),
        ])

    def test_default_and_caret_ranges(self):
        self.check_cases([
            ("1.2.3", "1.2.3", True),
            ("1.2.2", "1.2.3", False),
            ("1.9.0", "^1.2.3", True),
            ("2.0.0", "^1.2.3", False),
            ("1.2.0", "1.2", True),
            ("1.1.9", "1.2", False),
            ("1.99.99", "1", True),
            ("2.0.0", "1", False),
        ])

    def test_zero_major_compatibility(self):
        self.check_cases([
            ("0.2.9", "0.2.3", True),
            ("0.3.0", "0.2.3", False),
            ("0.2.0", "0.2", True),
            ("0.3.0", "0.2", False),
            ("0.0.3", "0.0.3", True),
            ("0.0.4", "0.0.3", False),
            ("0.0.99", "0.0", True),
            ("0.1.0", "0.0", False),
            ("0.99.99", "0", True),
            ("1.0.0", "0", False),
            ("0.0.0", "^0.0.0", True),
            ("0.0.1", "^0.0.0", False),
        ])

    def test_tilde_ranges(self):
        self.check_cases([
            ("1.2.3", "~1.2.3", True),
            ("1.2.2", "~1.2.3", False),
            ("1.2.99", "~1.2.3", True),
            ("1.3.0", "~1.2.3", False),
            ("1.2.0", "~1.2", True),
            ("1.3.0", "~1.2", False),
            ("1.99.0", "~1", True),
            ("2.0.0", "~1", False),
        ])

    def test_wildcard_spellings(self):
        for wildcard in ["*", "x", "X"]:
            self.check_cases([
                ("0.0.0", wildcard, True),
                ("9.9.9", wildcard, True),
                ("1.2.3-alpha", wildcard, False),
                ("1.9.8", f"1.{wildcard}", True),
                ("2.0.0", f"1.{wildcard}", False),
                ("1.2.99", f"1.2.{wildcard}", True),
                ("1.3.0", f"1.2.{wildcard}", False),
                ("1.99.99", f"1.{wildcard}.{wildcard}", True),
            ])

    def test_partial_exact_comparisons(self):
        self.check_cases([
            ("1.2.99", "=1.2", True),
            ("1.3.0", "=1.2", False),
            ("1.99.99", "=1", True),
            ("2.0.0", "=1", False),
            ("1.2.3", "=1.2.3", True),
            ("1.2.4", "=1.2.3", False),
        ])

    def test_partial_relational_boundaries(self):
        self.check_cases([
            ("1.99.99", ">1", False),
            ("2.0.0", ">1", True),
            ("1.2.99", ">1.2", False),
            ("1.3.0", ">1.2", True),
            ("1.0.0", ">=1", True),
            ("1.2.0", ">=1.2", True),
            ("0.99.99", "<1", True),
            ("1.0.0", "<1", False),
            ("1.1.99", "<1.2", True),
            ("1.2.0", "<1.2", False),
            ("1.99.99", "<=1", True),
            ("2.0.0", "<=1", False),
            ("1.2.99", "<=1.2", True),
            ("1.3.0", "<=1.2", False),
        ])

    def test_full_relational_boundaries(self):
        self.check_cases([
            ("1.2.3", ">1.2.3", False),
            ("1.2.4", ">1.2.3", True),
            ("1.2.3", ">=1.2.3", True),
            ("1.2.3", "<1.2.3", False),
            ("1.2.2", "<1.2.3", True),
            ("1.2.3", "<=1.2.3", True),
        ])

    def test_explicit_operator_keeps_wildcard_semantics(self):
        self.check_cases([
            ("1.2.99", ">1.2.*", False),
            ("1.3.0", ">1.2.*", True),
            ("1.9.9", "^1.2.*", True),
            ("1.3.0", "~1.2.*", False),
            ("2.0.0", "<=1.*", False),
        ])

    def test_conjunction_and_spaces(self):
        self.check_cases([
            ("1.2.3", " >= 1.2 , < 1.5 ", True),
            ("1.5.0", ">=1.2, <1.5", False),
            ("1.2.2", "<1.2, ^1.2.2", False),
            ("0.4.0", ">=0.3, <=0.4", True),
        ])

    def test_prerelease_eligibility(self):
        self.check_cases([
            ("1.0.0-alpha", "1.0", False),
            ("1.0.0-beta", "1.0.0-alpha", True),
            ("1.0.0", "1.0.0-alpha", True),
            ("1.2.0", "1.0.0-alpha", True),
            ("1.0.1-beta", "1.0.0-alpha", False),
            ("1.0.0-beta", ">=1.0.0-alpha, <2", True),
            ("1.0.0-beta", ">=1.0.0-alpha, <1.0.0", True),
            ("1.0.0-beta", ">=1.0.0-alpha, <=1.0", False),
            ("1.0.0-beta", ">=1.0.0-alpha, 1.*", False),
            ("1.0.0-beta", ">=1.0.0-alpha, ^1", True),
            ("1.0.0-beta", ">=1.0.0-alpha, ~1", False),
        ])

    def test_prerelease_numeric_and_identifier_order(self):
        chain = ["alpha", "alpha.1", "alpha.2", "alpha.10", "alpha.beta",
                 "beta", "beta.2", "beta.11", "rc.1"]
        for low, high in zip(chain, chain[1:]):
            self.check_cases([
                (f"1.2.3-{high}", f">1.2.3-{low}", True),
                (f"1.2.3-{low}", f">1.2.3-{high}", False),
            ])
        self.check_cases([
            ("1.2.3", ">1.2.3-rc.1", True),
            ("1.2.3-rc.1", ">=1.2.3", False),
            ("1.2.3-100000000000000000000", ">1.2.3-99999999999999999999", True),
        ])

    def test_build_metadata_is_ignored(self):
        self.check_cases([
            ("1.2.3+build.001", "=1.2.3+different", True),
            ("1.2.3+other", "^1.2.3+ignored", True),
            ("1.2.3-alpha.1+build", "=1.2.3-alpha.1+other", True),
        ])

    def test_invalid_versions(self):
        for version in ["", "1", "1.2", "v1.2.3", " 1.2.3", "1.2.3 ",
                        "01.2.3", "1.02.3", "1.2.03", "1.2.*", "1.2.3-",
                        "1.2.3+", "1.2.3-alpha..1", "1.2.3-alpha.01",
                        "1.2.3+build..1", "1.2.3-α", "18446744073709551616.0.0"]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                satisfies(version, "*")

    def test_invalid_requirements_fail_closed(self):
        for requirement in ["", " ", "||", "1 || 2", "1 - 2", "!=1.2.3",
                            "==1.2.3", "@1.2.3", ">=1.0 <2", "1,", ",1",
                            "1,,2", "*.*", "*, >=1", ">=1, *", "^*", "=*",
                            "1.*.2", "1.2-alpha", "1.2+build", "1.2.*-alpha",
                            "01.2.3", "1.02", "1.2.3-01", "1.2.3-",
                            "1.2.3+", "1.2.3+foo..bar", "1.2.3.4",
                            ">=\t1.0", "1.2\n", "18446744073709551616"]:
            with self.subTest(requirement=requirement), self.assertRaises(ValueError):
                satisfies("1.2.3", requirement)
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "<0, invalid")
        with self.assertRaises(ValueError):
            satisfies("1.2.3", ",".join([">=0"] * 33))

    def test_u64_boundary_is_valid(self):
        maximum = "18446744073709551615"
        self.assertTrue(satisfies(f"{maximum}.0.0", maximum))
        self.assertTrue(satisfies("1.2.3", ",".join([">=0"] * 32)))


if __name__ == "__main__":
    unittest.main()
