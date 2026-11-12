"""Version 1.0 protocol: one JSON case on stdin, one JSON result on stdout."""
import json
from pathlib import Path
import subprocess
from time import perf_counter
from .enumerate_domain import counterexample, in_domain
from .reference import evaluate, compare_paths, require
from .metrics import summarize


def load_cases(directory):
    cases = [json.loads(p.read_text()) for p in sorted(Path(directory).glob("*.json"))]
    require(bool(cases), "no cases found")
    require(len({c["case_id"] for c in cases}) == len(cases), "duplicate case IDs")
    return cases


def oracle(case):
    witness = counterexample(case["old_policy"], case["new_policy"], case["domain"])
    request = case["request"]
    require(in_domain(request, case["domain"]), "T3 request outside domain")
    return {"case_id": case["case_id"], "changed": witness is not None, "counterexample": witness,
            **compare_paths(evaluate(case["old_policy"], request), evaluate(case["new_policy"], request))}


def score(case, result, expected):
    errors = []
    if not isinstance(result, dict):
        result = {}
        errors.append("result must be an object")
    identity = result.get("case_id") == case["case_id"]
    if not identity:
        errors.append("missing or mismatched case_id")
    changed = result.get("changed")
    t1 = identity and type(changed) is bool and changed == expected["changed"]
    witness = result.get("counterexample")
    inside = False
    t2 = identity and "counterexample" in result and witness is None and not expected["changed"]
    if witness is not None:
        try:
            inside = in_domain(witness, case["domain"])
            t2 = identity and inside and evaluate(case["old_policy"], witness) != evaluate(case["new_policy"], witness)
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(str(exc))
    t3 = identity and all(isinstance(result.get(k), list) and result[k] == expected[k]
                         for k in ("old_path", "new_path"))
    return dict(case_id=case["case_id"], category=case["category"], expected_changed=expected["changed"],
                predicted_changed=changed if type(changed) is bool else None,
                t1=t1, t2=t2, t3=t3, counterexample_in_domain=inside,
                has_counterexample=witness is not None, errors=errors)


def run(cases, command=None, timeout=10):
    rows = []
    started = perf_counter()
    for case in cases:
        expected = oracle(case)
        require(case["expected"] == expected, f"stale ground truth: {case['case_id']}")
        result, failure = expected, None
        case_started = perf_counter()
        if command:
            # Answer keys and review notes never cross the candidate boundary.
            payload = {k: case[k] for k in ("schema_version", "case_id", "old_policy", "new_policy", "domain", "request")}
            try:
                proc = subprocess.run(command, input=json.dumps(payload), text=True,
                                      capture_output=True, timeout=timeout, check=True)
                result = json.loads(proc.stdout)
            except (subprocess.SubprocessError, OSError, ValueError) as exc:
                result, failure = {}, str(exc)
        row = score(case, result, expected)
        row["runtime_seconds"] = perf_counter() - case_started
        if failure:
            row["errors"].append(failure)
        rows.append(row)
    return {"schema_version": "1.0", "mode": "candidate" if command else "reference-self-check",
            "overall": summarize(rows),
            "by_category": {c: summarize([r for r in rows if r["category"] == c])
                            for c in sorted({r["category"] for r in rows})},
            "runtime_seconds": perf_counter() - started, "results": rows}
