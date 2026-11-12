# AnteGraph-Bench

**See the consequences before they happen.**

A small, reproducible benchmark for detecting changes in required human approvals
when a procurement policy changes. Python 3.10+; standard-library runtime; synthetic data only.

**Status: v0.1 preview (`0.1.0.dev1`).** Includes 20 policy pairs and 150 sample
requests. All fixtures pass exhaustive finite-domain checks and a second evaluator.
Human review of the fixtures remains pending. This preview does not satisfy the
original design's human-reviewed release gate and makes no novelty claim.

## Run from a fresh checkout

```sh
git clone https://github.com/GodwinKangor/AnteGraph-Bench.git
cd AnteGraph-Bench
python3 -m venv .venv
. .venv/bin/activate
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m antegraph_bench.cli --output reports/reference.json
```

This workflow needs no downloaded Python dependencies. Optional installation:
`python -m pip install -e .` exposes the `antegraph-bench` command. Run from the
repository root or supply `--cases /path/to/data/cases`. The distribution contains
the Python runner; datasets and reports live in the repository.

## Tasks and candidate protocol

- **T1:** detect whether any approval sequence differs over the declared domain.
- **T2:** return an in-domain request demonstrating a difference, or `null` for equivalent policies.
- **T3:** return the exact old/new approval sequences for the supplied `request`.

The runner launches an executable once per case, writes one JSON object to stdin,
and expects one JSON result on stdout. Arguments are passed directly without a shell.
Diagnostics belong on stderr. Default timeout: 10 seconds per case. Place
`--candidate` last:

```sh
python -m antegraph_bench.cli --output reports/demo.json \
  --candidate python examples/reference_candidate.py
```

The example candidate shares the reference interpreter: its scores test wiring,
not independent correctness or Antegraph product performance. Run trusted executables;
the subprocess interface is not a sandbox.

Input contains `schema_version`, `case_id`, `old_policy`, `new_policy`, `domain`,
and `request`. Answer keys are omitted. Required output:

```json
{
  "case_id": "threshold-raise",
  "changed": true,
  "counterexample": {
    "amount_cents": 1250000,
    "currency": "USD",
    "category": "software",
    "department": "engineering"
  },
  "old_path": ["Manager", "Finance"],
  "new_path": ["Manager"]
}
```

The paths describe the input `request`, which may differ from the returned
counterexample. See [schemas](schemas) and [policy semantics](docs/POLICY_SEMANTICS.md).
The runner scores required fields per task; invalid fields fail their task, while
other valid tasks remain scorable. Extra metadata is ignored by scoring; the published
result schema describes the canonical output. Missing/mismatched case IDs fail all tasks.

## Results and limits

JSON reports include overall and per-category T1 accuracy, precision, recall,
false positives/negatives; T2 valid witness, in-domain and equivalent-null rates;
and T3 exact path match. A zero denominator is `null`. Runtime is secondary and
machine-dependent. Candidate failures remain in the denominator. CLI exits 2 for
setup/fixture errors and 1 for candidate execution or structural errors; incorrect
predictions are valid scored results and do not alone change exit status.

The checked-in [reference report](reports/reference.json) is a self-check, not a
competitive evaluation. Timing fields vary between runs. Ground truth covers each
case's **48-request Cartesian domain only**, never all possible purchases. The
150 seeded sample requests are a separate impact-analysis corpus; they are not
used to establish equivalence and may fall outside scenario domains.

## Reproduce and extend

```sh
python scripts/generate_data.py
python -m unittest discover -s tests -v
python -m antegraph_bench.cli --output reports/reference.json
```

Generator version 1.0 uses seed `20261112`. Fixture schema version is `1.0`.
To add a case, provide a unique ID, mutation/category, provenance, review status,
old/new policies, a finite domain, a T3 request, and the stored oracle answer.
Add independently calculated boundary assertions and review the full domain diff.
The runner rejects stale expected answers. Do not claim human review until a human
has recorded it. Invalid requests/policies are tested as validation errors rather
than counted as semantic-change pairs.

Code and synthetic data are MIT licensed. No private procurement records, employee
identities, external policy adaptations, or Antegraph product outputs are included.
See [design](docs/BENCHMARK_DESIGN.md), [review checklist](docs/RELEASE_CHECKLIST.md),
and [research agenda](docs/RELATED_WORK.md).
