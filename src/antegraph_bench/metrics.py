"""Aggregate independent task scores; empty denominators are null."""
def ratio(n, d):
    return n / d if d else None


def summarize(rows):
    tp = sum(r["t1"] and r["expected_changed"] for r in rows)
    fp = sum(r["predicted_changed"] is True and not r["expected_changed"] for r in rows)
    fn = sum(r["predicted_changed"] is not True and r["expected_changed"] for r in rows)
    changed = [r for r in rows if r["expected_changed"]]
    equivalent = [r for r in rows if not r["expected_changed"]]
    return {"cases": len(rows), "t1_accuracy": ratio(sum(r["t1"] for r in rows), len(rows)),
            "t1_precision": ratio(tp, tp + fp), "t1_recall": ratio(tp, tp + fn),
            "false_positives": fp, "false_negatives": fn,
            "t2_valid_counterexample_rate": ratio(sum(r["t2"] for r in changed), len(changed)),
            "t2_equivalent_null_rate": ratio(sum(r["t2"] for r in equivalent), len(equivalent)),
            "t2_in_domain_rate": ratio(sum(r["counterexample_in_domain"] for r in rows),
                                       sum(r["has_counterexample"] for r in rows)),
            "t2_false_counterexamples": sum(r["has_counterexample"] for r in equivalent),
            "t3_exact_path_rate": ratio(sum(r["t3"] for r in rows), len(rows))}
