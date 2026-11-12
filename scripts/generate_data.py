"""Reproduce synthetic fixtures. No human review is implied by generation."""
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from antegraph_bench.runner import oracle

ROOT = Path(__file__).resolve().parents[1]


def condition(field, op, value):
    return {"field": field, "op": op, "value": value}


def rule(roles, *conditions):
    return {"append": roles, "when": list(conditions)}


def policy(*rules):
    return {"schema_version": "1.0", "rules": list(rules)}


def main():
    manager = rule(["Manager"])
    finance = rule(["Finance"], condition("amount_cents", ">", 1000000))
    security = rule(["Security"], condition("category", "==", "software"))
    legal = rule(["Legal"], condition("category", "==", "services"))
    engineering = rule(["Director"], condition("department", "==", "engineering"))
    # Each tuple explicitly specifies expected semantics for the T3 request and T1.
    specs = [
        ("threshold", "raise", [manager, finance], [manager, rule(["Finance"], condition("amount_cents", ">", 1500000))], True, ["Manager", "Finance"], ["Manager"]),
        ("threshold", "lower", [manager, rule(["Finance"], condition("amount_cents", ">", 1500000))], [manager, finance], True, ["Manager"], ["Manager", "Finance"]),
        ("boundary", "inclusive", [manager, finance], [manager, rule(["Finance"], condition("amount_cents", ">=", 1000000))], True, ["Manager", "Finance"], ["Manager", "Finance"]),
        ("boundary", "zero", [manager], [manager, rule(["Finance"], condition("amount_cents", "==", 0))], True, ["Manager"], ["Manager"]),
        ("added", "security", [manager], [manager, security], True, ["Manager"], ["Manager", "Security"]),
        ("added", "multiple", [manager], [manager, rule(["Security", "Legal"])], True, ["Manager"], ["Manager", "Security", "Legal"]),
        ("removed", "security", [manager, security], [manager], True, ["Manager", "Security"], ["Manager"]),
        ("removed", "legal", [manager, legal], [manager], True, ["Manager"], ["Manager"]),
        ("department", "add", [manager], [manager, engineering], True, ["Manager"], ["Manager", "Director"]),
        ("department", "move", [manager, engineering], [manager, rule(["Director"], condition("department", "==", "sales"))], True, ["Manager", "Director"], ["Manager"]),
        ("interacting", "duplicate", [manager, finance], [manager, finance, finance], False, ["Manager", "Finance"], ["Manager", "Finance"]),
        ("interacting", "conjunction", [manager, security], [manager, rule(["Security"], condition("category", "==", "software"), condition("department", "==", "sales"))], True, ["Manager", "Security"], ["Manager"]),
        ("ordering", "swap", [manager, finance], [finance, manager], True, ["Manager", "Finance"], ["Finance", "Manager"]),
        ("ordering", "roles", [rule(["Manager", "Legal"])], [rule(["Legal", "Manager"])], True, ["Manager", "Legal"], ["Legal", "Manager"]),
        ("equivalent", "singleton", [manager, security], [manager, rule(["Security"], condition("category", "in", ["software"]))], False, ["Manager", "Security"], ["Manager", "Security"]),
        ("equivalent", "exclusive", [manager, security, legal], [manager, legal, security], False, ["Manager", "Security"], ["Manager", "Security"]),
        ("noop", "unreachable", [manager], [manager, rule(["CFO"], condition("amount_cents", ">", 999999999))], False, ["Manager"], ["Manager"]),
        ("noop", "identical", [manager, finance], [manager, finance], False, ["Manager", "Finance"], ["Manager", "Finance"]),
        ("equivalent", "integer", [manager, finance], [manager, rule(["Finance"], condition("amount_cents", ">=", 1000001))], False, ["Manager", "Finance"], ["Manager", "Finance"]),
        ("interacting", "dedup_roles", [rule(["Manager", "Finance"])], [rule(["Manager", "Manager", "Finance", "Manager"])], False, ["Manager", "Finance"], ["Manager", "Finance"]),
    ]
    domain = {"amount_cents": [0, 999999, 1000000, 1000001, 1250000, 1500000, 1500001, 2000000],
              "category": ["software", "services", "hardware"], "department": ["engineering", "sales"]}
    request = dict(amount_cents=1250000, currency="USD", category="software", department="engineering")
    for i, (category, name, old, new, changed, old_path, new_path) in enumerate(specs, 1):
        case = dict(schema_version="1.0", case_id=f"{category}-{name}", category=category,
                    provenance="synthetic_generated", generator_version="1.0", review_status="pending_human_review",
                    mutation=name, old_policy=policy(*old), new_policy=policy(*new), domain=domain, request=request)
        expected = oracle(case)
        assert (expected["changed"], expected["old_path"], expected["new_path"]) == (changed, old_path, new_path)
        case["expected"] = expected
        (ROOT / "data/cases" / f"{i:02d}-{case['case_id']}.json").write_text(json.dumps(case, indent=2) + "\n")
    rng = random.Random(20261112)
    samples = [dict(id=f"req-{i:03d}", amount_cents=rng.randint(0, 2000000), currency="USD",
                    category=rng.choice(domain["category"]), department=rng.choice(domain["department"]))
               for i in range(1, 151)]
    (ROOT / "data/requests.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in samples))
    (ROOT / "examples/threshold_change.json").write_text((ROOT / "data/cases/01-threshold-raise.json").read_text())


if __name__ == "__main__":
    main()
