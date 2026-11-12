# Policy semantics 1.0

A policy has exactly `schema_version: "1.0"` and a `rules` array. Each rule has
exactly `when` (a conjunction of conditions) and `append` (a nonempty role array).
An empty conjunction always matches; an empty policy requires no approvals.

Conditions contain exactly `field`, `op`, and `value`. `amount_cents` accepts `>`,
`>=`, `==` with nonnegative integer operands, or `in` with a nonempty array of
nonnegative integers. `category` and `department` accept `==` with a nonempty string
or `in` with a nonempty array of nonempty strings. Booleans are not integers here.
No implicit conversion, currency conversion, wildcard, negation, or override exists.
Strings compare exactly and case-sensitively.

Evaluate all rules in source order. Matching rules append roles in listed order.
Deduplicate globally by first occurrence. Rules combine; nothing short-circuits,
denies, or removes a role. An approval path is an ordered list of required role
names, not a simulation of employees or elapsed time.

Requests require a nonnegative integer `amount_cents`, literal `currency: "USD"`,
and nonempty string `category` and `department`. Optional `id` is a nonempty string
and has no semantic effect. Unknown fields, missing fields, invalid operands,
unsupported operators and unsupported versions raise `ValueError`; they never
silently produce an empty path. Policies are validated even when no rule matches.

A domain has three nonempty arrays: `amount_cents`, `category`, `department`.
All Cartesian combinations use USD. Enumeration follows array order. T1 compares
ordered paths across the entire product. T2 chooses the first difference; any
valid in-domain difference is accepted from a candidate. A request ID is ignored
for membership. Equivalence holds only within this declared finite domain.

T3 additions/removals preserve new/old path order respectively. `order_changed`
compares the relative order of common roles: inserting a new role does not alone
count as reordering existing roles. This preview scores exact paths; separate
added/removed precision/recall and order accuracy remain planned extensions.
