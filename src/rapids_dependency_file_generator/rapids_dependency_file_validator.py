"""Logic for validating dependency files."""

import json
import sys
import textwrap

import jsonschema
import pkg_resources

SCHEMA = json.loads(pkg_resources.resource_string(__name__, "schema.json"))


def validate_dependencies(dependencies):
    """Valid a dictionary against the dependencies.yaml spec.

    Parameters
    ----------
    dependencies : dict
        The parsed dependencies.yaml file.

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If the dependencies do not conform to the schema
    """
    validator = jsonschema.Draft7Validator(SCHEMA)
    if not validator.is_valid(dependencies):
        for i, error in enumerate(validator.iter_errors(dependencies), start=1):
            print(f"Error #{i}:", file=sys.stderr)
            print(textwrap.indent(str(error), "\t"), file=sys.stderr)
        raise RuntimeError("The provided dependencies data is invalid.")
