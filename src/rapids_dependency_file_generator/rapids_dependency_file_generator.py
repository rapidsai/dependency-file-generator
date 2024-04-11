import fnmatch
import itertools
import os
import textwrap
from collections import defaultdict
from collections.abc import Generator

import tomlkit
import yaml

from . import config
from .constants import cli_name

__all__ = [
    "make_dependency_files",
]

HEADER = f"# This file is generated by `{cli_name}`."


def delete_existing_files(root: os.PathLike) -> None:
    """Delete any files generated by this generator.

    This function can be used to clean up a directory tree before generating a new set
    of files from scratch.

    Parameters
    ----------
    root : PathLike
        The path (relative or absolute) to the root of the directory tree to search for files to delete.
    """
    for dirpath, _, filenames in os.walk(root):
        for fn in filter(
            lambda fn: fn.endswith(".txt") or fn.endswith(".yaml"), filenames
        ):
            with open(file_path := os.path.join(dirpath, fn)) as f:
                try:
                    if HEADER in f.read():
                        os.remove(file_path)
                except UnicodeDecodeError:
                    pass


def dedupe(
    dependencies: list[str | config.PipRequirements],
) -> list[str | dict[str, str]]:
    """Generate the unique set of dependencies contained in a dependency list.

    Parameters
    ----------
    dependencies : list[str | PipRequirements]
        A sequence containing dependencies (possibly including duplicates).

    Returns
    ------
    list[str | dict[str, str]]
        The `dependencies` with all duplicates removed.
    """
    deduped = sorted({dep for dep in dependencies if isinstance(dep, str)})
    dict_deps = defaultdict(list)
    for dep in filter(lambda dep: not isinstance(dep, str), dependencies):
        if isinstance(dep, config.PipRequirements):
            dict_deps["pip"].extend(dep.pip)
            dict_deps["pip"] = sorted(set(dict_deps["pip"]))
    if dict_deps:
        deduped.append(dict(dict_deps))
    return deduped


def grid(gridspec: dict[str, list[str]]) -> Generator[dict[str, str]]:
    """Yields the Cartesian product of a `dict` of iterables.

    The input ``gridspec`` is a dictionary whose keys correspond to
    parameter names. Each key is associated with an iterable of the
    values that parameter could take on. The result is a sequence of
    dictionaries where each dictionary has one of the unique combinations
    of the parameter values.

    Parameters
    ----------
    gridspec : dict[str, list[str]]
        A mapping from parameter names to lists of parameter values.

    Yields
    ------
    dict[str, str]
        Each yielded value is a dictionary containing one of the unique
        combinations of parameter values from `gridspec`.
    """
    for values in itertools.product(*gridspec.values()):
        yield dict(zip(gridspec.keys(), values))


def make_dependency_file(
    *,
    file_type: config.Output,
    name: os.PathLike,
    config_file: os.PathLike,
    output_dir: os.PathLike,
    conda_channels: list[str],
    dependencies: list[str | dict[str, list[str]]],
    extras: config.FileExtras,
):
    """Generate the contents of the dependency file.

    Parameters
    ----------
    file_type : Output
        An Output value used to determine the file type.
    name : PathLike
        The name of the file to write.
    config_file : PathLike
        The full path to the dependencies.yaml file.
    output_dir : PathLike
        The path to the directory where the dependency files will be written.
    conda_channels : list[str]
        The channels to include in the file. Only used when `file_type` is
        CONDA.
    dependencies : list[str | dict[str, list[str]]]
        The dependencies to include in the file.
    extras : FileExtras
        Any extra information provided for generating this dependency file.

    Returns
    -------
    str
        The contents of the file.
    """
    relative_path_to_config_file = os.path.relpath(config_file, output_dir)
    file_contents = textwrap.dedent(
        f"""\
        {HEADER}
        # To make changes, edit {relative_path_to_config_file} and run `{cli_name}`.
        """
    )
    if file_type == config.Output.CONDA:
        file_contents += yaml.dump(
            {
                "name": os.path.splitext(name)[0],
                "channels": conda_channels,
                "dependencies": dependencies,
            }
        )
    elif file_type == config.Output.REQUIREMENTS:
        file_contents += "\n".join(dependencies) + "\n"
    elif file_type == config.Output.PYPROJECT:
        if extras.table == "build-system":
            key = "requires"
            if extras.key is not None:
                raise ValueError(
                    "The 'key' field is not allowed for the 'pyproject' file type when "
                    "'table' is 'build-system'."
                )
        elif extras.table == "project":
            key = "dependencies"
            if extras.key is not None:
                raise ValueError(
                    "The 'key' field is not allowed for the 'pyproject' file type when "
                    "'table' is 'project'."
                )
        else:
            if extras.key is None:
                raise ValueError(
                    "The 'key' field is required for the 'pyproject' file type when "
                    "'table' is not one of 'build-system' or 'project'."
                )
            key = extras.key

        # This file type needs to be modified in place instead of built from scratch.
        with open(os.path.join(output_dir, name)) as f:
            file_contents_toml = tomlkit.load(f)

        toml_deps = tomlkit.array()
        for dep in dependencies:
            toml_deps.add_line(dep)
        toml_deps.add_line(indent="")
        toml_deps.comment(
            f"This list was generated by `{cli_name}`. To make changes, edit "
            f"{relative_path_to_config_file} and run `{cli_name}`."
        )

        # Recursively descend into subtables like "[x.y.z]", creating tables as needed.
        table = file_contents_toml
        for section in extras.table.split("."):
            try:
                table = table[section]
            except tomlkit.exceptions.NonExistentKey:
                # If table is not a super-table (i.e. if it has its own contents and is
                # not simply parted of a nested table name 'x.y.z') add a new line
                # before adding a new sub-table.
                if not table.is_super_table():
                    table.add(tomlkit.nl())
                table[section] = tomlkit.table()
                table = table[section]

        table[key] = toml_deps

        file_contents = tomlkit.dumps(file_contents_toml)

    return file_contents


def get_filename(file_type: config.Output, file_key: str, matrix_combo: dict[str, str]):
    """Get the name of the file to which to write a generated dependency set.

    The file name will be composed of the following components, each determined
    by the `file_type`:
        - A file-type-based prefix e.g. "requirements" for requirements.txt files.
        - A name determined by the value of $FILENAME in the corresponding
          [files.$FILENAME] section of dependencies.yaml. This name is used for some
          output types (conda, requirements) and not others (pyproject).
        - A matrix description encoding the key-value pairs in `matrix_combo`.
        - A suitable extension for the file (e.g. ".yaml" for conda environment files.)

    Parameters
    ----------
    file_type : Output
        An Output value used to determine the file type.
    file_key : str
        The name of this member in the [files] list in dependencies.yaml.
    matrix_combo : dict[str, str]
        A mapping of key-value pairs corresponding to the
        [files.$FILENAME.matrix] entry in dependencies.yaml.

    Returns
    -------
    str
        The name of the file to generate.
    """
    file_type_prefix = ""
    file_ext = ""
    file_name_prefix = file_key
    suffix = "_".join([f"{k}-{v}" for k, v in matrix_combo.items()])
    if file_type == config.Output.CONDA:
        file_ext = ".yaml"
    elif file_type == config.Output.REQUIREMENTS:
        file_ext = ".txt"
        file_type_prefix = "requirements"
    elif file_type == config.Output.PYPROJECT:
        file_ext = ".toml"
        # Unlike for files like requirements.txt or conda environment YAML files, which
        # may be named with additional prefixes (e.g. all_cuda_*) pyproject.toml files
        # need to have that exact name and are never prefixed.
        file_name_prefix = "pyproject"
        suffix = ""
    filename = "_".join(
        filter(None, (file_type_prefix, file_name_prefix, suffix))
    ).replace(".", "")
    return filename + file_ext


def get_output_dir(
    file_type: config.Output, config_file_path: os.PathLike, file_config: config.File
):
    """Get the directory to which to write a generated dependency file.

    The output directory is determined by the `file_type` and the corresponding
    key in the `file_config`. The path provided in `file_config` will be taken
    relative to `output_root`.

    Parameters
    ----------
    file_type : Output
        An Output value used to determine the file type.
    output_root : PathLike
        The path to the root directory where dependency files are placed.
    file_config : File
        A dictionary corresponding to one of the [files.$FILENAME] sections of
        the dependencies.yaml file. May contain `conda_dir` or
        `requirements_dir`.

    Returns
    -------
    str
        The directory to write the file to.
    """
    path = [os.path.dirname(config_file_path)]
    if file_type == config.Output.CONDA:
        path.append(file_config.conda_dir)
    elif file_type == config.Output.REQUIREMENTS:
        path.append(file_config.requirements_dir)
    elif file_type == config.Output.PYPROJECT:
        path.append(file_config.pyproject_dir)
    return os.path.join(*path)


def should_use_specific_entry(
    matrix_combo: dict[str, str], specific_entry_matrix: dict[str, str]
):
    """Check if an entry should be used.

    Dependencies listed in the [dependencies.$DEPENDENCY_GROUP.specific]
    section are specific to a particular matrix entry provided by the
    [matrices] list. This function validates the [matrices.matrix] value
    against the provided `matrix_combo` to check if they are compatible.

    A `specific_entry_matrix` is compatible with a `matrix_combo` if and only
    if `specific_entry_matrix[key]` matches the glob pattern
    `matrix_combo[key]` for every key defined in `specific_entry_matrix`. A
    `matrix_combo` may contain additional keys not specified by
    `specific_entry_matrix`.

    Parameters
    ----------
    matrix_combo : dict[str, str]
        A mapping from matrix keys to values for the current file being
        generated.
    specific_entry_matrix : dict[str, str]
        A mapping from matrix keys to values for the current specific
        dependency set being checked.

    Returns
    -------
    bool
        True if the `specific_entry_matrix` is compatible with the current
        `matrix_combo` and False otherwise.
    """
    return all(
        specific_key in matrix_combo
        and fnmatch.fnmatch(matrix_combo[specific_key], specific_value)
        for specific_key, specific_value in specific_entry_matrix.items()
    )


def make_dependency_files(
    parsed_config: config.Config,
    file_keys: list[str],
    output: set[config.Output],
    matrix: dict[str, list[str]] | None,
    prepend_channels: list[str],
    to_stdout: bool,
):
    """Generate dependency files.

    This function iterates over data parsed from a YAML file conforming to the
    `dependencies.yaml file spec <https://github.com/rapidsai/dependency-file-generator#dependenciesyaml-format>`_
    and produces the requested files.

    :param parsed_config: The parsed dependencies.yaml config file.
    :type parsed_config: Config

    :param file_keys: The list of file keys to use.
    :type file_keys: list[str]

    :param output: The set of file types to write.
    :type output: set[Output]

    :param matrix: The matrix to use, or None if the default matrix from each
        file key should be used.
    :type matrix: dict[str, list[str]] | None

    :param prepend_channels: List of channels to prepend to the ones from
        parsed_config.
    :type prepend_channels: list[str]

    :param to_stdout: Whether the output should be written to stdout. If
        False, it will be written to a file computed based on the output
        file type and ``parsed_config``'s path.
    :type to_stdout: bool

    :raises ValueError: If the file is malformed. There are numerous
        different error cases which are described by the error messages.
    """

    for file_key in file_keys:
        file_config = parsed_config.files[file_key]
        file_types_to_generate = file_config.output & output
        if matrix is not None:
            file_matrix = matrix
        else:
            file_matrix = file_config.matrix
        calculated_grid = list(grid(file_matrix))
        if (
            config.Output.PYPROJECT in file_types_to_generate
            and len(calculated_grid) > 1
        ):
            raise ValueError("Pyproject outputs can't have more than one matrix output")
        for file_type in file_types_to_generate:
            for matrix_combo in calculated_grid:
                dependencies = []

                # Collect all includes from each dependency list corresponding
                # to this (file_name, file_type, matrix_combo) tuple. The
                # current tuple corresponds to a single file to be written.
                for include in file_config.includes:
                    dependency_entry = parsed_config.dependencies[include]

                    for common_entry in dependency_entry.common:
                        if file_type not in common_entry.output_types:
                            continue
                        dependencies.extend(common_entry.packages)

                    for specific_entry in dependency_entry.specific:
                        if file_type not in specific_entry.output_types:
                            continue

                        found = False
                        fallback_entry = None
                        for specific_matrices_entry in specific_entry.matrices:
                            # An empty `specific_matrices_entry["matrix"]` is
                            # valid and can be used to specify a fallback_entry for a
                            # `matrix_combo` for which no specific entry
                            # exists. In that case we save the fallback_entry result
                            # and only use it at the end if nothing more
                            # specific is found.
                            if not specific_matrices_entry.matrix:
                                fallback_entry = specific_matrices_entry
                                continue

                            if should_use_specific_entry(
                                matrix_combo, specific_matrices_entry.matrix
                            ):
                                # Raise an error if multiple specific entries
                                # (not including the fallback_entry) match a
                                # requested matrix combination.
                                if found:
                                    raise ValueError(
                                        f"Found multiple matches for matrix {matrix_combo}"
                                    )
                                found = True
                                # A package list may be empty as a way to
                                # indicate that for some matrix elements no
                                # packages should be installed.
                                dependencies.extend(
                                    specific_matrices_entry.packages or []
                                )

                        if not found:
                            if fallback_entry:
                                dependencies.extend(fallback_entry.packages)
                            else:
                                raise ValueError(
                                    f"No matching matrix found in '{include}' for: {matrix_combo}"
                                )

                # Dedupe deps and print / write to filesystem
                full_file_name = get_filename(file_type, file_key, matrix_combo)
                deduped_deps = dedupe(dependencies)

                output_dir = (
                    "."
                    if to_stdout
                    else get_output_dir(file_type, parsed_config.path, file_config)
                )
                contents = make_dependency_file(
                    file_type=file_type,
                    name=full_file_name,
                    config_file=parsed_config.path,
                    output_dir=output_dir,
                    conda_channels=prepend_channels + parsed_config.channels,
                    dependencies=deduped_deps,
                    extras=file_config.extras,
                )

                if to_stdout:
                    print(contents)
                else:
                    os.makedirs(output_dir, exist_ok=True)
                    file_path = os.path.join(output_dir, full_file_name)
                    with open(file_path, "w") as f:
                        f.write(contents)
