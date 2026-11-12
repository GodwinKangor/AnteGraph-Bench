# Benchmark design

This repository implements the engineering core of Antegraph-Bench v0.1:
semantic change detection, concrete counterexamples, and ordered approval-path
comparison for a deliberately small procurement language. It is independent of
the Antegraph product and does not use its output as an answer key.

Twenty synthetic cases span threshold changes, boundary operators, added/removed
roles, department exceptions, interacting rules, order changes, equivalent
rewrites and unreachable mutations. Every case enumerates 48 requests. There are
both changed and equivalent pairs. Expected T1 and selected T3 paths are explicitly
asserted in the generator; stored witnesses come from exhaustive enumeration.
Tests compare every path with a second evaluator written using comprehensions.
This cross-check is useful but is not human review or formal verification.

The first publication is intentionally a preview. Manual review, broader cases,
additional role-diff metrics, research comparison, and packaging for a package
index remain future work. A 100% reference self-check is expected and supplies
no evidence of an external candidate's quality.

Synthetic sample corpus: 150 stable IDs, seed 20261112, generator 1.0. It is
separate from the finite-domain oracle. No real-world representativeness is claimed.

Protocol version and policy/data schema version are 1.0. Python package version
is 0.1.0.dev1. Versioning these separately allows later dataset expansion without
silently changing interpreter semantics.
