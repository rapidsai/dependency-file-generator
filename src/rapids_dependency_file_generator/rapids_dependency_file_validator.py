"""Logic for validating dependency files."""

import json
import textwrap

import jsonschema
import pkg_resources
from jsonschema.exceptions import best_match

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
    errors = list(validator.iter_errors(dependencies))
    if len(errors) > 0:
        print("The provided dependency file contains schema errors.")
        best_matching_error = best_match(errors)
        print("\n", textwrap.indent(str(best_matching_error), "\t"), "\n")
        raise RuntimeError("The provided dependencies data is invalid.")
