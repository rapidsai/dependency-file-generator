"""Logic for validating dependency files."""

import importlib.resources
import json
import sys
import textwrap
import typing

import jsonschema
from jsonschema.exceptions import best_match

SCHEMA = json.loads(importlib.resources.files(__package__).joinpath("schema.json").read_bytes())


def validate_dependencies(dependencies: dict[str, typing.Any]) -> None:
    """Validate a dictionary against the dependencies.yaml spec.

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
        print("The provided dependency file contains schema errors.", file=sys.stderr)
        best_matching_error = best_match(errors)
        print("\n", textwrap.indent(str(best_matching_error), "\t"), "\n", file=sys.stderr)
        raise RuntimeError("The provided dependencies data is invalid.")
