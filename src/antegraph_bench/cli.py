import argparse
import json
from pathlib import Path
import sys
from .runner import load_cases, run


def main():
    parser = argparse.ArgumentParser(description="Finite-domain procurement policy benchmark")
    parser.add_argument("--cases", type=Path, default=Path("data/cases"))
    parser.add_argument("--output", type=Path, default=Path("reports/latest.json"))
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--candidate", nargs=argparse.REMAINDER, help="executable and arguments; place last")
    args = parser.parse_args()
    try:
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        report = run(load_cases(args.cases), args.candidate, args.timeout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"{report['mode']}: {report['overall']['cases']} cases; "
          f"T1={report['overall']['t1_accuracy']:.1%}; "
          f"T3={report['overall']['t3_exact_path_rate']:.1%}; report={args.output}")
    return 1 if any(r["errors"] for r in report["results"]) else 0


if __name__ == "__main__":
    sys.exit(main())
