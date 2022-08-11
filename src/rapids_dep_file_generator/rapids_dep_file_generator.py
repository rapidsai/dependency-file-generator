import itertools
import yaml
from collections import defaultdict
from os.path import join, relpath
from .constants import (
    arch_cuda_key_fmt,
    cli_name,
    conda_requirements_key,
    default_channels,
    default_conda_dir,
    default_requirements_dir,
    GeneratorTypes,
)


def dedupe(dependencies):
    deduped = [dep for dep in dependencies if not isinstance(dep, dict)]
    deduped = sorted(list(set(deduped)))
    dict_like_deps = [dep for dep in dependencies if isinstance(dep, dict)]
    dict_deps = defaultdict(list)
    for dep in dict_like_deps:
        for key, values in dep.items():
            dict_deps[key].extend(values)
            dict_deps[key] = sorted(list(set(dict_deps[key])))
    if dict(dict_deps):
        deduped.append(dict(dict_deps))
    return deduped


def grid(gridspec):
    """Yields the Cartesian product of a `dict` of iterables.

    The input ``gridspec`` is a dictionary whose keys correspond to
    parameter names. Each key is associated with an iterable of the
    values that parameter could take on. The result is a sequence of
    dictionaries where each dictionary has one of the unique combinations
    of the parameter values.
    """
    for values in itertools.product(*gridspec.values()):
        yield dict(zip(gridspec.keys(), values))


def make_dependency_file(
    file_type, name, config_file, output_path, conda_channels, dependencies
):
    relative_path_to_config_file = relpath(config_file, output_path)
    file_contents = f"""\
# This file was automatically generated. Changes should not be made directly to this file.
# Instead, edit {relative_path_to_config_file} and rerun `{cli_name}`.
"""
    if file_type == str(GeneratorTypes.CONDA):
        file_contents += yaml.dump(
            {
                "name": name,
                "channels": conda_channels,
                "dependencies": dependencies,
            }
        )
    if file_type == str(GeneratorTypes.REQUIREMENTS):
        file_contents += "\n".join(dependencies) + "\n"
    return file_contents


def get_file_types_to_generate(generate_value):
    if generate_value == str(GeneratorTypes.BOTH):
        return [str(GeneratorTypes.CONDA), str(GeneratorTypes.REQUIREMENTS)]
    if generate_value == str(GeneratorTypes.NONE):
        return []
    if generate_value == str(GeneratorTypes.CONDA) or generate_value == str(
        GeneratorTypes.REQUIREMENTS
    ):
        return [generate_value]
    raise Exception(
        "'generate' key can only be "
        + ", ".join([f"'{x}'" for x in GeneratorTypes])
        + "."
    )


def get_filename(file_type, file_prefix, cuda_version, arch):
    prefix = ""
    suffix = ""
    if file_type == str(GeneratorTypes.CONDA):
        suffix = ".yaml"
    if file_type == str(GeneratorTypes.REQUIREMENTS):
        suffix = ".txt"
        prefix = "requirements_"

    return f"{prefix}{file_prefix}_cuda-{cuda_version}_arch-{arch}{suffix}"


def get_output_path(file_type, file_config):
    output_path = "."
    if file_type == str(GeneratorTypes.CONDA):
        output_path = file_config.get("conda_dir", default_conda_dir)
    if file_type == str(GeneratorTypes.REQUIREMENTS):
        output_path = file_config.get("requirements_dir", default_requirements_dir)
    return output_path


def main(config_file, files):
    with open(config_file, "r") as f:
        parsed_config = yaml.load(f, Loader=yaml.FullLoader)

    channels = parsed_config.get("channels", default_channels) or default_channels
    dependencies = parsed_config["dependencies"]
    to_stdout = True if files else False
    files = files or parsed_config["files"]
    for file_name, file_config in files.items():
        includes = file_config["includes"]
        file_types_to_generate = get_file_types_to_generate(file_config["generate"])

        for file_type in file_types_to_generate:
            file_deps = []

            # Add common dependencies to file list
            for ecosystem in [file_type, conda_requirements_key]:
                for include in includes:
                    file_deps.extend(
                        dependencies.get(ecosystem, {})
                        .get("common", {})
                        .get(include, [])
                    )

            # Add cuda-arch specific dependencies to file list
            for matrix_combo in grid(file_config["matrix"]):
                cuda_version = matrix_combo["cuda_version"]
                arch = matrix_combo["arch"]
                matrix_combo_deps = []
                for ecosystem in [file_type, conda_requirements_key]:
                    for include in includes:
                        matrix_combo_deps.extend(
                            dependencies.get(ecosystem, {})
                            .get(arch_cuda_key_fmt(arch, cuda_version), {})
                            .get(include, [])
                        )

                # Dedupe deps and print / write to filesystem
                full_file_name = get_filename(file_type, file_name, cuda_version, arch)
                deduped_deps = dedupe(file_deps + matrix_combo_deps)
                make_dependency_file_factory = lambda output_path: make_dependency_file(
                    file_type,
                    full_file_name,
                    config_file,
                    output_path,
                    channels,
                    deduped_deps,
                )

                if to_stdout:
                    output_path = "."
                    contents = make_dependency_file_factory(output_path)
                    print(contents)
                else:
                    output_path = get_output_path(file_type, file_config)
                    contents = make_dependency_file_factory(output_path)
                    with open(join(output_path, full_file_name), "w") as f:
                        f.write(contents)