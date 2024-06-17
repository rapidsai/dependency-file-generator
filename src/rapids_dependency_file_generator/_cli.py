import argparse
import os

from ._config import Output, load_config_from_file
from ._constants import default_dependency_file_path
from ._rapids_dependency_file_generator import (
    delete_existing_files,
    make_dependency_files,
)
from ._version import __version__ as version


def validate_args(argv):
    parser = argparse.ArgumentParser(
        description=f"Generates dependency files for RAPIDS libraries (version: {version})."
    )
    parser.add_argument(
        "-c",
        "--config",
        default=default_dependency_file_path,
        help="Path to YAML config file.",
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
        "--file-key",
        help="The file key from `dependencies.yaml` to generate.",
    )
    codependent_args.add_argument(
        "--output",
        help="The output file type to generate.",
        choices=[
            x.value
            for x in [
                Output.CONDA,
                Output.PYPROJECT,
                Output.REQUIREMENTS,
            ]
        ],
    )
    codependent_args.add_argument(
        "--matrix",
        help=(
            "String representing which matrix combination should be generated, "
            'such as `--matrix "cuda=11.5;arch=x86_64"`. May also be an empty string.'
        ),
    )

    parser.add_argument(
        "--prepend-channel",
        action="append",
        default=[],
        dest="prepend_channels",
        help=(
            "A string representing a conda channel to prepend to the list of "
            "channels. This option is only valid with --output "
            f"{Output.CONDA.value} or no --output. May be specified multiple times."
        ),
    )

    args = parser.parse_args(argv)

    dependent_arg_keys = ["file_key", "output", "matrix"]
    dependent_arg_values = [getattr(args, key) is None for key in dependent_arg_keys]
    if any(dependent_arg_values) and not all(dependent_arg_values):
        raise ValueError(
            "The following arguments must be used together:"
            + "".join([f"\n  {x}" for x in ["--file-key", "--output", "--matrix"]])
        )

    if args.prepend_channels and args.output and args.output != Output.CONDA.value:
        raise ValueError(f"--prepend-channel is only valid with --output {Output.CONDA.value}")

    # If --clean was passed without arguments, default to cleaning from the root of the
    # tree where the config file is.
    if args.clean == "":
        args.clean = os.path.dirname(os.path.abspath(args.config))

    return args


def generate_matrix(matrix_arg):
    if not matrix_arg:
        return None
    matrix = {}
    for matrix_column in matrix_arg.split(";"):
        key, val = matrix_column.split("=")
        matrix[key] = [val]
    return matrix


def main(argv=None) -> None:
    args = validate_args(argv)

    parsed_config = load_config_from_file(args.config)

    matrix = generate_matrix(args.matrix)
    to_stdout = all([args.file_key, args.output, args.matrix is not None])

    if to_stdout:
        file_keys = [args.file_key]
        output = {Output(args.output)}
    else:
        file_keys = list(parsed_config.files.keys())
        output = None

    if args.clean:
        delete_existing_files(args.clean)

    make_dependency_files(
        parsed_config=parsed_config,
        file_keys=file_keys,
        output=output,
        matrix=matrix,
        prepend_channels=args.prepend_channels,
        to_stdout=to_stdout,
    )
