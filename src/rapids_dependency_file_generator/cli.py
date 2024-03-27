import argparse
import os
import warnings

import yaml

from ._version import __version__ as version
from .constants import OutputTypes, default_channels, default_dependency_file_path
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

    codependent_args = parser.add_argument_group("optional, but codependent")
    codependent_args.add_argument(
        "-f",
        "--file-key",
        help="The file key from `dependencies.yaml` to generate",
    )
    codependent_args.add_argument(
        "--file_key",
        dest="file_key_deprecated",
        help="Deprecated alias for --file-key",
    )
    codependent_args.add_argument(
        "-o",
        "--output",
        help="The output file type to generate",
        choices=[
            str(x)
            for x in [
                OutputTypes.CONDA,
                OutputTypes.PYPROJECT,
                OutputTypes.REQUIREMENTS,
            ]
        ],
    )
    codependent_args.add_argument(
        "-m",
        "--matrix",
        help=(
            "String representing which matrix combination should be generated, "
            'such as `--matrix "cuda=11.5;arch=x86_64"`. May also be an empty string'
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
            f"{OutputTypes.CONDA} or no --output"
        ),
    )
    parser.add_argument(
        "--prepend-channels",
        dest="prepend_channels_deprecated",
        help=(
            "A string representing a list of conda channels to prepend to the list of "
            "channels. Channels should be separated by a semicolon, such as "
            '`--prepend-channels "my_channel;my_other_channel"`. This option is '
            f"only valid with --output {OutputTypes.CONDA} or no --output."
            "DEPRECATED: Use --prepend-channel instead."
        ),
    )

    args = parser.parse_args(argv)

    if args.file_key_deprecated:
        warnings.warn(
            "The use of --file_key is deprecated. Use -f or --file-key instead."
        )
    if not args.file_key:
        args.file_key = args.file_key_deprecated

    dependent_arg_keys = ["file_key", "output", "matrix"]
    dependent_arg_values = [getattr(args, key) is None for key in dependent_arg_keys]
    if any(dependent_arg_values) and not all(dependent_arg_values):
        raise ValueError(
            "The following arguments must be used together:"
            + "".join([f"\n  {x}" for x in ["--file-key", "--output", "--matrix"]])
        )

    if args.prepend_channels_deprecated:
        warnings.warn(
            "The use of --prepend-channels is deprecated. Use --prepend-channel instead."
        )
        args.prepend_channels.extend(args.prepend_channels_deprecated.split(";"))
    if args.prepend_channels and args.output and args.output != str(OutputTypes.CONDA):
        raise ValueError(
            f"--prepend-channel is only valid with --output {OutputTypes.CONDA}"
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
        parsed_config["files"] = {
            args.file_key: {
                **parsed_config["files"][args.file_key],
                "matrix": matrix,
                "output": args.output,
            }
        }

    if args.prepend_channels:
        parsed_config["channels"] = args.prepend_channels + parsed_config.get(
            "channels", default_channels
        )

    if args.clean:
        delete_existing_files(args.clean)

    make_dependency_files(parsed_config, args.config, to_stdout)
