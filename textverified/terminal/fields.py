"""Schema-derived validation shared by the CLI and purchase screens."""
import copy
import difflib
import json
from pathlib import Path
from decimal import Decimal
from jsonschema import Draft7Validator

METADATA = json.loads(Path(__file__).with_name("fields.json").read_text(encoding="utf-8"))
DURATION_ALIASES = {
    "1d": "oneDay",
    "3d": "threeDay",
    "7d": "sevenDay",
    "14d": "fourteenDay",
    "30d": "thirtyDay",
    "90d": "ninetyDay",
    "1y": "oneYear",
}


def descriptor(operation):
    operation = operation.replace(".quote", ".buy")
    if operation not in METADATA["operations"]:
        raise ValueError("Unknown operation; use verification.buy or rental.buy")
    return METADATA["operations"][operation]


def json_schema(schema):
    schema = copy.deepcopy(schema)

    def visit(node):
        if isinstance(node, dict):
            nullable = node.pop("nullable", False)
            for value in node.values():
                visit(value)
            if nullable:
                original = node.copy()
                node.clear()
                node["anyOf"] = [original, {"type": "null"}]
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)
    return schema


def merge_inputs(operation, sources):
    fields = descriptor(operation)["fields"]
    aliases = {name: f for f in fields for name in (f["client_field_name"], f["api_field_name"])}
    result = {}
    for source in sources:
        for name, value in source.items():
            if name not in aliases:
                matches = difflib.get_close_matches(name, aliases)
                raise ValueError("Unknown field %s%s" % (name, ("; did you mean " + matches[0]) if matches else ""))
            field = aliases[name]
            wire = field["api_field_name"]
            if wire in result:
                raise ValueError("Conflicting assignments for " + name)
            if field["schema"].get("readOnly"):
                raise ValueError("Read-only field: " + name)
            result[wire] = value
    return result


def validate(operation, inputs):
    data = merge_inputs(operation, [inputs])
    if "duration" in data:
        data["duration"] = DURATION_ALIASES.get(data["duration"], data["duration"])
    schema = json_schema(descriptor(operation)["schema"])
    errors = sorted(Draft7Validator(schema).iter_errors(data), key=lambda e: str(e.path))
    if errors:
        error = errors[0]
        raise ValueError("%s: %s" % (".".join(map(str, error.path)) or "request", error.message))
    if not data.get("serviceName"):
        raise ValueError("A nonempty service is required")
    if data.get("maxPrice") is not None:
        amount = Decimal(str(data["maxPrice"]))
        if not amount.is_finite() or amount < 0:
            raise ValueError("Maximum price must be a finite nonnegative amount")
    if operation.startswith("verification") and data.get("serviceName") == "allservices":
        raise ValueError("Choose a specific verification service")
    return ValidatedRequest(data)


class ValidatedRequest:
    """Preserve omission, null, false, zero and empty values through transport."""

    def __init__(self, data):
        self.data = copy.deepcopy(data)

    def to_api(self):
        return copy.deepcopy(self.data)


def scalar(operation, assignment, as_json=False):
    if "=" not in assignment:
        raise ValueError("Expected FIELD=VALUE")
    name, value = assignment.split("=", 1)
    field = next(
        (f for f in descriptor(operation)["fields"] if name in (f["client_field_name"], f["api_field_name"])), None
    )
    if field is None:
        merge_inputs(operation, [{name: value}])
    if as_json:
        value = json.loads(value)
    elif field["schema"].get("type") == "boolean":
        if value.lower() not in ("true", "false"):
            raise ValueError("Boolean input must be true or false")
        value = value.lower() == "true"
    elif field["schema"].get("type") == "integer":
        value = int(value)
    elif field["schema"].get("type") == "number":
        value = float(Decimal(value))
    elif field["schema"].get("type") in ("array", "object"):
        raise ValueError("Use --set-json for " + name)
    return {name: value}
