import argparse
import os

import yaml

from ._version import __version__ as version
from .constants import OutputTypes, default_dependency_file_path
from .rapids_dependency_file_generator import (
    delete_existing_files,
    get_requested_output_types,
    make_dependency_files,
)
from .rapids_dependency_file_validator import validate_dependencies


def validate_args(argv):
    parser = argparse.ArgumentParser(
        description=f"Generates dependency files for RAPIDS libraries (version: {version})"
    )
    parser.add_argument(
        "-c",
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
    parser.add_argument(
        "-f",
        "--file-key",
        "--file_key",
        nargs="*",
        dest="file_key",
        action="extend",
        default=[],
        help="The file key(s) from `dependencies.yaml` to generate",
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="*",
        action="extend",
        help="The output file type(s) to generate",
        default=[],
        choices=[
            str(x)
            for x in [
                OutputTypes.CONDA,
                OutputTypes.REQUIREMENTS,
                OutputTypes.PYPROJECT,
            ]
        ],
    )
    parser.add_argument(
        "-m",
        "--matrix",
        help=(
            "String representing which matrix combination should be generated, "
            'such as `--matrix "cuda=11.5;arch=x86_64"`. May also be an empty string'
        ),
    )
    parser.add_argument(
        "--cuda-suffix",
        default="-cu",
        help="The package name CUDA version suffix (defaults to -cu)",
    )
    parser.add_argument(
        "--stdout",
        default=False,
        action="store_true",
        help="Print the results to stdout",
    )

    args = parser.parse_args(argv)

    # If --clean was passed without arguments, default to cleaning from the root of the
    # tree where the config file is.
    if args.clean == "":
        args.clean = os.path.dirname(os.path.abspath(args.config))

    args.file_key = list(sorted(list(set(sorted(args.file_key)))))

    # default to conda and pyproject
    if len(args.output) == 0:
        args.output = [str(OutputTypes.CONDA), str(OutputTypes.PYPROJECT)]

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

    if len(args.file_key) > 0:
        parsed_config["files"] = {
            file_key: parsed_config["files"][file_key]
                for file_key in args.file_key
                    if parsed_config["files"].get(file_key, None) is not None
        }

    if len(args.output) > 0:
        files = {}
        for file_key, file_config in parsed_config["files"].items():
            outputs = get_requested_output_types(file_config["output"])
            outputs = list(filter(lambda output: output in outputs, args.output))
            if len(outputs) > 0:
                file_config["output"] = outputs
                files[file_key] = file_config
        parsed_config["files"] = files

    if len(matrix.keys()) > 0:
        for file_key, file_config in parsed_config["files"].items():
            file_config["matrix"] = matrix

    if args.clean:
        delete_existing_files(args.clean)

    make_dependency_files(parsed_config, args.config, args.stdout)
