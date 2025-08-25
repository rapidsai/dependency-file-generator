"""Logic for validating dependency files."""

import importlib.resources
import json
import sys
import textwrap
import typing
import warnings

import jsonschema
from jsonschema.exceptions import best_match

SCHEMA = json.loads(importlib.resources.files(__package__).joinpath("schema.json").read_bytes())

__all__ = [
    "UnusedDependencySetWarning",
]


class UnusedDependencySetWarning(UserWarning):
    pass


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

    unused_dependency_sets = set(dependencies["dependencies"].keys())
    unused_dependency_sets.difference_update(
        i for file_config in dependencies["files"].values() for i in file_config["includes"]
    )
    for dep in sorted(unused_dependency_sets):
        warnings.warn(f'Dependency set "{dep}" is not referred to anywhere in "files:"', UnusedDependencySetWarning)
