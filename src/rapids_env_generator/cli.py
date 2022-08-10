from .rapids_env_generator import main as reg
from ._version import __version__ as version
from .constants import GeneratorTypes, default_dependency_file_path
import yaml
import argparse


def generate_file_obj(config_file, file_key, file_type, cuda_version, arch):
    if not (config_file and file_key and file_type and cuda_version and arch):
        return {}
    with open(config_file, "r") as f:
        parsed_config = yaml.load(f, Loader=yaml.FullLoader)
    matrix = {"cuda_version": [cuda_version], "arch": [arch]}
    parsed_config["files"][file_key]["matrix"] = matrix
    parsed_config["files"][file_key]["generate"] = file_type
    return {file_key: parsed_config["files"][file_key]}


def validate_args(args):
    mutually_exclusive_arg_keys = ["file_key", "generate", "cuda_version", "arch"]
    mutually_exclusive_arg_values = []
    for i in range(len(mutually_exclusive_arg_keys)):
        mutually_exclusive_arg_values.append(
            getattr(args, mutually_exclusive_arg_keys[i])
        )
    if any(mutually_exclusive_arg_values) and not all(mutually_exclusive_arg_values):
        raise Exception(
            "The following arguments are mutually exclusive and must be used together:"
            + "".join([f"\n  --{x}" for x in mutually_exclusive_arg_keys])
        )


def main():
    parser = argparse.ArgumentParser(
        description=f"Generates environment files for RAPIDS libraries (version: {version})"
    )
    parser.add_argument(
        "--config",
        default=default_dependency_file_path,
        help="path to YAML config file",
    )

    inclusive_group = parser.add_argument_group("optional, but mutually inclusive")
    inclusive_group.add_argument(
        "--file_key",
        help="The file key to generate",
    )
    inclusive_group.add_argument(
        "--generate",
        help="The file type to generate",
        choices=[str(x) for x in [GeneratorTypes.CONDA, GeneratorTypes.REQUIREMENTS]],
    )
    inclusive_group.add_argument(
        "--cuda_version",
        help="The CUDA version used for generating the output",
    )
    inclusive_group.add_argument(
        "--arch",
        help="The architecture version used for generating the output",
    )

    args = parser.parse_args()
    validate_args(args)
    env = generate_file_obj(
        args.config, args.file_key, args.generate, args.cuda_version, args.arch
    )
    reg(args.config, env)
