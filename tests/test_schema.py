import jsonschema


def test_schema_is_valid(schema):
    jsonschema.Draft7Validator.check_schema(schema)
