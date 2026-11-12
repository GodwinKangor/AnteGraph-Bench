"""Exhaustive oracle over a declared Cartesian product, never an unbounded proof."""
from itertools import product
from .reference import evaluate, require, validate_request


def enumerate_domain(domain):
    require(isinstance(domain, dict) and set(domain) == {"amount_cents", "category", "department"},
            "invalid domain fields")
    require(all(isinstance(v, list) and v for v in domain.values()), "empty or invalid domain axis")
    for amount, category, department in product(domain["amount_cents"], domain["category"], domain["department"]):
        request = dict(amount_cents=amount, currency="USD", category=category, department=department)
        validate_request(request)
        yield request


def in_domain(request, domain):
    validate_request(request)
    return all(request[k] in domain[k] for k in ("amount_cents", "category", "department"))


def counterexample(old, new, domain):
    # Materialize to validate the entire domain, even if the first point differs.
    requests = list(enumerate_domain(domain))
    return next((r for r in requests if evaluate(old, r) != evaluate(new, r)), None)
