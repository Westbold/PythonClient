"""Generate optional terminal descriptors without changing SDK generation."""
import json
from generate_enums import to_var_name


def generate_terminal_metadata(swagger, destination="textverified/terminal/fields.json"):
    """Generate terminal field descriptors from the same pinned SDK schema."""
    import hashlib
    from pathlib import Path

    def resolve(value):
        if isinstance(value, dict):
            if "$ref" in value:
                name = value["$ref"].split("/")[-1]
                return dict(resolve(swagger["components"]["schemas"][name]), schema_reference=value["$ref"])
            return {key: resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [resolve(item) for item in value]
        return value

    operations = {}
    for operation, name in {"verification.buy": "NewVerificationRequest", "rental.buy": "NewRentalRequest"}.items():
        schema = resolve(swagger["components"]["schemas"][name])
        descriptors = []
        for api_name, field_schema in schema["properties"].items():
            descriptors.append(
                dict(
                    operation_id=operation,
                    client_field_name=to_var_name(api_name),
                    python_field_name=to_var_name(api_name),
                    api_field_name=api_name,
                    required=api_name in schema.get("required", []),
                    has_default="default" in field_schema,
                    schema=field_schema,
                )
            )
        operations[operation] = dict(schema=schema, fields=descriptors, schema_reference=name)
    manifest = dict(
        schema_version=1,
        generator_version=1,
        api_version=swagger.get("info", {}).get("version"),
        schema_sha256=hashlib.sha256(
            json.dumps(swagger, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
    )
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    Path(destination).write_text(
        json.dumps(dict(manifest=manifest, operations=operations), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    from pathlib import Path

    generate_terminal_metadata(json.loads(Path("swagger.json").read_text(encoding="utf-8")))
