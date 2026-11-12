"""Small, strict interpreter. Rules combine in source order, first role wins."""
FIELDS = {"amount_cents", "currency", "category", "department"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_request(request):
    require(isinstance(request, dict), "request must be an object")
    require(FIELDS <= request.keys() <= FIELDS | {"id"}, "invalid request fields")
    require(type(request["amount_cents"]) is int and request["amount_cents"] >= 0,
            "amount_cents must be a nonnegative integer")
    require(request["currency"] == "USD", "only USD is supported")
    for field in ("category", "department"):
        require(isinstance(request[field], str) and bool(request[field]), f"invalid {field}")
    if "id" in request:
        require(isinstance(request["id"], str) and bool(request["id"]), "invalid id")


def validate_policy(policy):
    require(isinstance(policy, dict) and set(policy) == {"schema_version", "rules"},
            "invalid policy fields")
    require(policy["schema_version"] == "1.0", "unsupported schema_version")
    require(isinstance(policy["rules"], list), "rules must be an array")
    for rule in policy["rules"]:
        require(isinstance(rule, dict) and set(rule) == {"when", "append"}, "invalid rule")
        require(isinstance(rule["append"], list) and bool(rule["append"]), "append must be nonempty")
        require(all(isinstance(r, str) and r for r in rule["append"]), "invalid role")
        require(isinstance(rule["when"], list), "when must be an array")
        for cond in rule["when"]:
            require(isinstance(cond, dict) and set(cond) == {"field", "op", "value"}, "invalid condition")
            field, op, value = cond["field"], cond["op"], cond["value"]
            require(field in {"amount_cents", "category", "department"}, "unsupported field")
            require(op in {">", ">=", "==", "in"}, "unsupported operator")
            require(op not in {">", ">="} or field == "amount_cents", "numeric comparison required")
            values = value if op == "in" else [value]
            require(isinstance(values, list) and bool(values), "in requires nonempty array")
            require(all(type(v) is int and v >= 0 for v in values) if field == "amount_cents"
                    else all(isinstance(v, str) and v for v in values), "invalid condition value")


def evaluate(policy, request):
    validate_policy(policy)
    validate_request(request)
    path = []
    for rule in policy["rules"]:
        matches = True
        for cond in rule["when"]:
            actual, value, op = request[cond["field"]], cond["value"], cond["op"]
            match = (actual > value if op == ">" else actual >= value if op == ">="
                     else actual == value if op == "==" else actual in value)
            matches = matches and match
        if matches:
            for role in rule["append"]:
                if role not in path:
                    path.append(role)
    return path


def compare_paths(old, new):
    shared = set(old) & set(new)
    return {"old_path": old, "new_path": new,
            "added_approvals": [r for r in new if r not in old],
            "removed_approvals": [r for r in old if r not in new],
            "order_changed": [r for r in old if r in shared] != [r for r in new if r in shared]}
