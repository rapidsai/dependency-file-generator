from .rapids_env_generator import main as reg
from ._version import __version__ as version
import argparse
import sys
from os.path import dirname, abspath


def generate_env_obj(name, matrix_values, includes):
    if not (matrix_values and includes):
        return {}
    columns = matrix_values.split(";")
    matrix = {}
    for column in columns:
        [key, values] = column.split("=")
        values = values.split(",")
        if len(values) > 1:
            values = [values[0]]
            print(
                "The CLI configuration only supports a single matrix combination.",
                file=sys.stderr,
            )
            print(f"Keeping '{values[0]}' for '{key}'", file=sys.stderr)
        matrix[key] = values
    return {name: {"matrix": matrix, "includes": includes.split(",")}}


def validate_args(args):
    if args.matrix and not args.includes:
        raise Exception("The --includes flag must be used with --matrix")
    if args.includes and not args.matrix:
        raise Exception("The --matrix flag must be used with --includes")


def main():
    parser = argparse.ArgumentParser(
        description=f"Generates environment files for RAPIDS libraries (version: {version})"
    )
    parser.add_argument(
        "--env_name",
        default="tmp_env",
        help="When used with --matrix and --includes, sets the name of the generated environment",
    )
    parser.add_argument(
        "--config",
        default="conda/environments/envs.yaml",
        help="path to YAML config file",
    )

    inclusive_group = parser.add_argument_group("mutually inclusive")
    inclusive_group.add_argument(
        "--matrix",
        help="string representing which matrix combination should be generated. i.e. --matrix='cuda_version=11.5;arch=amd64'",
    )
    inclusive_group.add_argument(
        "--includes",
        help="dependency lists from config file to include in output",
    )

    exclusive_group = parser.add_argument_group(
        "mutually exclusive"
    ).add_mutually_exclusive_group()
    exclusive_group.add_argument(
        "--stdout",
        action="store_true",
        default=False,
        help="Whether to print output to stdout",
    )
    exclusive_group.add_argument(
        "--output_path", help="The directory to write the output files to"
    )

    args = parser.parse_args()
    if not (args.stdout or args.output_path):
        args.output_path = dirname(abspath(args.config))
    validate_args(args)
    env = generate_env_obj(args.env_name, args.matrix, args.includes)
    reg(args.config, env, args.output_path, args.stdout)
