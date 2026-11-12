import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from antegraph_bench.reference import evaluate, compare_paths, validate_policy, validate_request
from antegraph_bench.enumerate_domain import enumerate_domain, counterexample
from antegraph_bench.runner import load_cases, oracle, run, score

ROOT = Path(__file__).resolve().parents[1]
CASES = load_cases(ROOT / "data/cases")


def independent_evaluator(policy, request):
    """Separate comprehension evaluator; no calls to reference.evaluate."""
    def matches(c):
        actual, operand = request[c["field"]], c["value"]
        if c["op"] == "in":
            return actual in operand
        if c["op"] == "==":
            return actual == operand
        if c["op"] == ">":
            return actual > operand
        return actual >= operand
    roles = [role for rule in policy["rules"] if all(matches(c) for c in rule["when"])
             for role in rule["append"]]
    return list(dict.fromkeys(roles))


class BenchmarkTests(unittest.TestCase):
    def test_all_answers_and_independent_domain_check(self):
        for case in CASES:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(oracle(case), case["expected"])
                differences = []
                for request in enumerate_domain(case["domain"]):
                    paths = []
                    for key in ("old_policy", "new_policy"):
                        independent = independent_evaluator(case[key], request)
                        self.assertEqual(evaluate(case[key], request), independent)
                        paths.append(independent)
                    differences.append(paths[0] != paths[1])
                self.assertEqual(any(differences), case["expected"]["changed"])

    def test_explicit_boundaries(self):
        case = CASES[0]
        expectations = [(0, False, False), (999999, False, False), (1000000, False, False),
                        (1000001, True, False), (1250000, True, False),
                        (1499999, True, False), (1500000, True, False), (1500001, True, True),
                        (2000000, True, True), (999999999, True, True)]
        for amount, old, new in expectations:
            with self.subTest(amount=amount):
                request = dict(case["request"], amount_cents=amount)
                self.assertEqual("Finance" in evaluate(case["old_policy"], request), old)
                self.assertEqual("Finance" in evaluate(case["new_policy"], request), new)

    def test_invalid_requests(self):
        for patch in ({"amount_cents": True}, {"amount_cents": -1}, {"amount_cents": 1.5},
                      {"currency": "EUR"}, {"department": ""}, {"category": None}, {"extra": 1}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate_request(dict(CASES[0]["request"], **patch))
        request = dict(CASES[0]["request"])
        del request["amount_cents"]
        with self.assertRaises(ValueError):
            validate_request(request)

    def test_invalid_policy(self):
        for patch in ({"op": "<"}, {"field": "currency"}, {"value": True}, {"op": "in", "value": []}):
            policy = copy.deepcopy(CASES[0]["old_policy"])
            policy["rules"][1]["when"][0].update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate_policy(policy)

    def test_path_order(self):
        self.assertTrue(compare_paths(["A", "B"], ["B", "A"])["order_changed"])
        self.assertFalse(compare_paths(["A", "B"], ["A", "C", "B"])["order_changed"])

    def test_wrong_task_does_not_hide_other_scores(self):
        case = CASES[0]
        expected = oracle(case)
        result = dict(expected, changed=False, counterexample=dict(case["request"], amount_cents=42))
        row = score(case, result, expected)
        self.assertFalse(row["t1"])
        self.assertFalse(row["t2"])
        self.assertTrue(row["t3"])

    def test_invalid_output(self):
        for result in (None, [], {}, {"case_id": CASES[0]["case_id"], "changed": 1}):
            row = score(CASES[0], result, oracle(CASES[0]))
            self.assertFalse(row["t1"])
            self.assertFalse(row["t2"])
            self.assertFalse(row["t3"])

    def test_out_of_domain_witness(self):
        case = CASES[0]
        result = dict(oracle(case), counterexample=dict(case["request"], amount_cents=1250001))
        self.assertFalse(score(case, result, oracle(case))["t2"])

    def test_empty_domain(self):
        domain = dict(CASES[0]["domain"], amount_cents=[])
        with self.assertRaises(ValueError):
            counterexample(CASES[0]["old_policy"], CASES[0]["new_policy"], domain)

    def test_candidate_protocol(self):
        report = run(CASES, [sys.executable, str(ROOT / "examples/reference_candidate.py")])
        self.assertEqual(report["overall"]["t1_accuracy"], 1)
        self.assertEqual(report["overall"]["t2_valid_counterexample_rate"], 1)
        self.assertEqual(report["overall"]["t2_equivalent_null_rate"], 1)
        self.assertEqual(report["overall"]["t3_exact_path_rate"], 1)

    def test_failure_and_timeout(self):
        for command, timeout in (([sys.executable, "-c", "print('invalid')"], 5),
                                 ([sys.executable, "-c", "import time; time.sleep(2)"], .01)):
            report = run(CASES[:1], command, timeout)
            self.assertTrue(report["results"][0]["errors"])
            self.assertEqual(report["overall"]["t1_accuracy"], 0)

    def test_no_answer_key_leak(self):
        script = "import json,sys; c=json.load(sys.stdin); assert 'expected' not in c; print('{}')"
        report = run(CASES[:1], [sys.executable, "-c", script])
        self.assertFalse(any("returned non-zero" in e for e in report["results"][0]["errors"]))

    def test_generation_is_reproducible(self):
        files = list((ROOT / "data").rglob("*.json")) + [ROOT / "data/requests.jsonl"]
        before = {p: p.read_bytes() for p in files}
        subprocess.run([sys.executable, str(ROOT / "scripts/generate_data.py")], check=True)
        self.assertEqual(before, {p: p.read_bytes() for p in files})
        self.assertEqual(len((ROOT / "data/requests.jsonl").read_text().splitlines()), 150)


if __name__ == "__main__":
    unittest.main()
