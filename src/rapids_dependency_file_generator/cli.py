from .rapids_dependency_file_generator import main as dfg
from ._version import __version__ as version
from .constants import GeneratorTypes, default_dependency_file_path
import yaml
import argparse


def generate_file_obj(config_file, file_key, file_type, matrix):
    if not (config_file and file_key and file_type and matrix):
        return {}
    with open(config_file, "r") as f:
        parsed_config = yaml.load(f, Loader=yaml.FullLoader)
    parsed_config["files"][file_key]["matrix"] = matrix
    parsed_config["files"][file_key]["generate"] = file_type
    return {file_key: parsed_config["files"][file_key]}


def validate_args(args):
    dependent_arg_keys = ["file_key", "generate", "matrix"]
    dependent_arg_values = []
    for i in range(len(dependent_arg_keys)):
        dependent_arg_values.append(getattr(args, dependent_arg_keys[i]))
    if any(dependent_arg_values) and not all(dependent_arg_values):
        raise ValueError(
            "The following arguments must be used together:"
            + "".join([f"\n  --{x}" for x in dependent_arg_keys])
        )


def generate_matrix(matrix_arg):
    matrix = {}
    for matrix_column in matrix_arg.split(";"):
        kv_pair = matrix_column.split("=")
        matrix[kv_pair[0]] = [kv_pair[1]]
    return matrix


def main():
    parser = argparse.ArgumentParser(
        description=f"Generates dependency files for RAPIDS libraries (version: {version})"
    )
    parser.add_argument(
        "--config",
        default=default_dependency_file_path,
        help="path to YAML config file",
    )

    codependent_args = parser.add_argument_group("optional, but codependent")
    codependent_args.add_argument(
        "--file_key",
        help="The file key from `dependencies.yaml` to generate",
    )
    codependent_args.add_argument(
        "--generate",
        help="The file type to generate",
        choices=[str(x) for x in [GeneratorTypes.CONDA, GeneratorTypes.REQUIREMENTS]],
    )
    codependent_args.add_argument(
        "--matrix",
        help='string representing which matrix combination should be generated, such as `--matrix "cuda=11.5;arch=x86_64"`',
    )

    args = parser.parse_args()
    validate_args(args)
    matrix = generate_matrix(args.matrix) if args.matrix else {}
    file = generate_file_obj(args.config, args.file_key, args.generate, matrix)
    dfg(args.config, file)
