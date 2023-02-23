import argparse
import os

import yaml

from ._version import __version__ as version
from .constants import OutputTypes, default_dependency_file_path
from .rapids_dependency_file_generator import (
    delete_existing_files,
    make_dependency_files,
)
from .rapids_dependency_file_validator import validate_dependencies


def validate_args(argv):
    parser = argparse.ArgumentParser(
        description=f"Generates dependency files for RAPIDS libraries (version: {version})"
    )
    parser.add_argument(
        "--config",
        default=default_dependency_file_path,
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--clean",
        nargs="?",
        default=None,
        const="",
        help=(
            "Delete any files previously created by dfg before running. An optional "
            "path to clean may be provided, otherwise the current working directory "
            "is used as the root from which to clean."
        ),
    )

    codependent_args = parser.add_argument_group("optional, but codependent")
    codependent_args.add_argument(
        "--file_key",
        help="The file key from `dependencies.yaml` to generate",
    )
    codependent_args.add_argument(
        "--output",
        help="The output file type to generate",
        choices=[str(x) for x in [OutputTypes.CONDA, OutputTypes.REQUIREMENTS]],
    )
    codependent_args.add_argument(
        "--matrix",
        help=(
            "String representing which matrix combination should be generated, "
            'such as `--matrix "cuda=11.5;arch=x86_64"`. May also be an empty string'
        ),
    )

    args = parser.parse_args(argv)
    dependent_arg_keys = ["file_key", "output", "matrix"]
    dependent_arg_values = [getattr(args, key) is None for key in dependent_arg_keys]
    if any(dependent_arg_values) and not all(dependent_arg_values):
        raise ValueError(
            "The following arguments must be used together:"
            + "".join([f"\n  --{x}" for x in dependent_arg_keys])
        )

    # If --clean was passed without arguments, default to cleaning from the root of the
    # tree where the config file is.
    if args.clean == "":
        args.clean = os.path.dirname(os.path.abspath(args.config))

    return args


def generate_matrix(matrix_arg):
    if not matrix_arg:
        return {}
    matrix = {}
    for matrix_column in matrix_arg.split(";"):
        key, val = matrix_column.split("=")
        matrix[key] = [val]
    return matrix


def main(argv=None):
    args = validate_args(argv)

    with open(args.config) as f:
        parsed_config = yaml.load(f, Loader=yaml.FullLoader)

    validate_dependencies(parsed_config)

    matrix = generate_matrix(args.matrix)
    to_stdout = all([args.file_key, args.output, args.matrix is not None])

    if to_stdout:
        includes = parsed_config["files"][args.file_key]["includes"]
        parsed_config["files"] = {
            args.file_key: {
                "matrix": matrix,
                "output": args.output,
                "includes": includes,
            }
        }

    if args.clean:
        delete_existing_files(args.clean)
    make_dependency_files(parsed_config, args.config, to_stdout)
