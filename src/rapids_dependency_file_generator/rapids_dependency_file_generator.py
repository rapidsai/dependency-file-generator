import itertools
import os
import textwrap
from collections import defaultdict

import yaml

from .constants import (
    OutputTypes,
    cli_name,
    default_channels,
    default_conda_dir,
    default_conda_meta_dir,
    default_requirements_dir,
)

OUTPUT_ENUM_VALUES = [str(x) for x in OutputTypes]
NON_NONE_OUTPUT_ENUM_VALUES = [str(x) for x in OutputTypes if not x == OutputTypes.NONE]


def dedupe(dependencies):
    """Generate the unique set of dependencies contained in a dependency list.

    Parameters
    ----------
    dependencies : Sequence
        A sequence containing dependencies (possibly including duplicates).

    Yields
    ------
    list
        The `dependencies` with all duplicates removed.
    """
    deduped = sorted({dep for dep in dependencies if not isinstance(dep, dict)})
    dict_deps = defaultdict(list)
    # This kind of loop is to support nested dependency dicts such as a pip:
    # section. If multiple includes lists contain that, those must be
    # internally deduped as well.
    for dep in filter(lambda dep: isinstance(dep, dict), dependencies):
        for key, values in dep.items():
            dict_deps[key].extend(values)
            dict_deps[key] = sorted(set(dict_deps[key]))
    if dict_deps:
        deduped.append(dict(dict_deps))
    return deduped


def grid(gridspec):
    """Yields the Cartesian product of a `dict` of iterables.

    The input ``gridspec`` is a dictionary whose keys correspond to
    parameter names. Each key is associated with an iterable of the
    values that parameter could take on. The result is a sequence of
    dictionaries where each dictionary has one of the unique combinations
    of the parameter values.

    Parameters
    ----------
    gridspec : dict
        A mapping from parameter names to lists of parameter values.

    Yields
    ------
    Iterable[dict]
        Each yielded value is a dictionary containing one of the unique
        combinations of parameter values from `gridspec`.

    Notes
    -----
    An empty `gridspec` dict will result in an empty dict as the single yielded
    value.
    """
    for values in itertools.product(*gridspec.values()):
        yield dict(zip(gridspec.keys(), values))


def make_dependency_file(
    file_type, name, config_file, output_dir, conda_channels, dependencies
):
    """Generate the contents of the dependency file.

    Parameters
    ----------
    file_type : str
        A string corresponding to the value of a member of constants.OutputTypes.
    name : str
        The name of the file to write.
    config_file : str
        The full path to the dependencies.yaml file.
    output_dir : str
        The path to the directory where the dependency files will be written.
    conda_channels : str
        The channels to include in the file. Only used when `file_type` is
        CONDA.
    dependencies : list
        The dependencies to include in the file.

    Returns
    -------
    str
        The contents of the file.
    """
    relative_path_to_config_file = os.path.relpath(config_file, output_dir)
    file_contents = textwrap.dedent(
        f"""\
        # This file is generated by `{cli_name}`.
        # To make changes, edit {relative_path_to_config_file} and run `{cli_name}`.
        """
    )
    if file_type == str(OutputTypes.CONDA):
        file_contents += yaml.dump(
            {
                "name": os.path.splitext(name)[0],
                "channels": conda_channels,
                "dependencies": dependencies,
            }
        )
    if file_type == str(OutputTypes.CONDA_META):
        file_contents += yaml.dump(dependencies)
    if file_type == str(OutputTypes.REQUIREMENTS):
        file_contents += "\n".join(dependencies) + "\n"
    return file_contents


def _ensure_list(obj):
    return obj if isinstance(obj, list) else [obj]


def get_requested_output_types(output):
    """Get the list of output file types to generate.

    The possible options are enumerated by `constants.OutputTypes`. If the only
    requested output is `NONE`, returns an empty list.

    Parameters
    ----------
    output : str or List[str]
        A string or list of strings indicating the output types.

    Returns
    -------
    List[str]
        The list of output file types to generate.

    Raises
    -------
    ValueError
        If multiple outputs are requested and one of them is NONE, or if an
        unknown output type is requested.
    """
    output = _ensure_list(output)

    if output == [str(OutputTypes.NONE)]:
        return []

    if len(output) > 1 and str(OutputTypes.NONE) in output:
        raise ValueError("'output: [none]' cannot be combined with any other values.")

    if any(v not in NON_NONE_OUTPUT_ENUM_VALUES for v in output):
        raise ValueError(
            "'output' key can only be "
            + ", ".join(f"'{x}'" for x in OUTPUT_ENUM_VALUES)
            + f" or a list of the non-'{OutputTypes.NONE}' values."
        )
    return output


def get_filename(file_type, file_prefix, matrix_combo):
    """Get the name of the file to which to write a generated dependency set.

    The file name will be composed of the following components, each determined
    by the `file_type`:
        - A file-type-based prefix e.g. "requirements" for requirements.txt files.
        - A name determined by the value of $FILENAME in the corresponding
          [files.$FILENAME] section of dependencies.yaml.
        - A matrix description encoding the key-value pairs in `matrix_combo`.
        - A suitable extension for the file (e.g. ".yaml" for conda environment files.)

    Parameters
    ----------
    file_type : str
        A string corresponding to the value of a member of constants.OutputTypes.
    file_prefix : str
        The name of this member in the [files] list in dependencies.yaml.
    matrix_combo : dict
        A mapping of key-value pairs corresponding to the
        [files.$FILENAME.matrix] entry in dependencies.yaml.

    Returns
    -------
    str
        The name of the file to generate.
    """
    file_type_prefix = ""
    file_ext = ""
    if file_type == str(OutputTypes.CONDA) or file_type == str(OutputTypes.CONDA_META):
        file_ext = ".yaml"
    if file_type == str(OutputTypes.REQUIREMENTS):
        file_ext = ".txt"
        file_type_prefix = "requirements"
    suffix = "_".join([f"{k}-{v}" for k, v in matrix_combo.items()])
    filename = "_".join(
        x for x in [file_type_prefix, file_prefix, suffix] if x
    ).replace(".", "")
    return filename + file_ext


def get_output_dir(file_type, config_file_path, file_config, file_name):
    """Get the directory to which to write a generated dependency file.

    The output directory is determined by the `file_type` and the corresponding
    key in the `file_config`. The path provided in `file_config` will be taken
    relative to `output_root`.

    Parameters
    ----------
    file_type : str
        A string corresponding to the value of a member of constants.OutputTypes.
    output_root : str
        The path to the root directory where dependency files are placed.
    file_config : dict
        A dictionary corresponding to one of the [files.$FILENAME] sections of
        the dependencies.yaml file. May contain `conda_dir` or
        `requirements_dir`.
    file_name : str
        The name of this member in the [files] list in dependencies.yaml. This
        argument is only used for conda_meta to generate the appropriate nested
        package directory in `conda/recipes/`
    Returns
    -------
    str
        The directory to write the file to.
    """
    path = [os.path.dirname(config_file_path)]
    if file_type == str(OutputTypes.CONDA_META):
        path.append(file_config.get("conda_meta_dir", default_conda_meta_dir))
    if file_type == str(OutputTypes.CONDA):
        path.append(file_config.get("conda_dir", default_conda_dir))
    if file_type == str(OutputTypes.REQUIREMENTS):
        path.append(file_config.get("requirements_dir", default_requirements_dir))
    return os.path.join(*path)


def should_use_specific_entry(matrix_combo, specific_entry_matrix):
    """Check if an entry should be used.

    Dependencies listed in the [dependencies.$DEPENDENCY_GROUP.specific]
    section are specific to a particular matrix entry provided by the
    [matrices] list. This function validates the [matrices.matrix] value
    against the provided `matrix_combo` to check if they are compatible.

    A `specific_entry_matrix` is compatible with a `matrix_combo` if and only if
    `specific_entry_matrix[key] == matrix_combo[key]` for every key defined in
    `specific_entry_matrix`. A `matrix_combo` may contain additional keys not
    specified by `specific_entry_matrix`.

    Parameters
    ----------
    matrix_combo : dict
        A mapping from matrix keys to values for the current file being
        generated.
    specific_entry_matrix : dict
        A mapping from matrix keys to values for the current specific
        dependency set being checked.

    Returns
    -------
    bool
        True if the `specific_entry_matrix` is compatible with the current
        `matrix_combo` and False otherwise.
    """
    return all(
        matrix_combo.get(specific_key) == specific_value
        for specific_key, specific_value in specific_entry_matrix.items()
    )


def get_deps(dependency_entry, file_type, matrix_combo, include):
    dependencies = []
    for common_entry in dependency_entry.get("common", []):
        if file_type not in _ensure_list(common_entry["output_types"]):
            continue
        dependencies.extend(common_entry["packages"])

    for specific_entry in dependency_entry.get("specific", []):
        if file_type == str(OutputTypes.CONDA_META):
            raise ValueError("Specific dependencies are not supported with conda_meta")
        if file_type not in _ensure_list(specific_entry["output_types"]):
            continue

        found = False
        fallback_entry = None
        for specific_matrices_entry in specific_entry["matrices"]:
            # An empty `specific_matrices_entry["matrix"]` is
            # valid and can be used to specify a fallback_entry for a
            # `matrix_combo` for which no specific entry
            # exists. In that case we save the fallback_entry result
            # and only use it at the end if nothing more
            # specific is found.
            if not specific_matrices_entry["matrix"]:
                fallback_entry = specific_matrices_entry
                continue

            if should_use_specific_entry(
                matrix_combo, specific_matrices_entry["matrix"]
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
                dependencies.extend(specific_matrices_entry["packages"] or [])

        if not found:
            if fallback_entry:
                dependencies.extend(fallback_entry["packages"] or [])
            else:
                raise ValueError(
                    f"No matching matrix found in '{include}' for: {matrix_combo}"
                )
    return dependencies


def make_dependency_files(parsed_config, config_file_path, to_stdout):
    """Generate dependency files.

    This function iterates over data parsed from a YAML file conforming to the
    `dependencies.yaml file spec <https://github.com/rapidsai/dependency-file-generator#dependenciesyaml-format>__`
    and produces the requested files.

    Parameters
    ----------
    parsed_config : dict
       The parsed dependencies.yaml config file.
    config_file_path : str
        The path to the dependencies.yaml file.
    to_stdout : bool
        Whether the output should be written to stdout. If False, it will be
        written to a file computed based on the output file type and
        config_file_path.

    Raises
    -------
    ValueError
        If the file is malformed. There are numerous different error cases
        which are described by the error messages.
    """

    """
    Notes:
        - I don't think you can combine conda_meta with anything else because
        the layout will be different.
        - The matrix entries might have to correspond to conditional
        dependencies. Either that, or it just requires separate includes lists.
        - conda_meta needs to support different types of dependencies (build,
        host, run) unlike all the other formats
        - conda_meta should only operate on files that already exist. It should
        never create new files
        - conda_meta should preserve the order of existing keys. It's OK to
        alphabetize the keys under requirements though.
    """
    channels = parsed_config.get("channels", default_channels) or default_channels

    # First parse the dependencies lists into a more easily consumable format.

    files = parsed_config["files"]
    for file_name, file_config in files.items():
        includes = file_config["includes"]

        file_types_to_generate = get_requested_output_types(file_config["output"])

        for file_type in file_types_to_generate:
            for matrix_combo in grid(file_config.get("matrix", {})):

                # Collect all includes from each dependency list corresponding
                # to this (file_name, file_type, matrix_combo) tuple. The
                # current tuple corresponds to a single file to be written.
                dependencies = []
                for include in includes:
                    dependencies.extend(
                        get_deps(
                            parsed_config["dependencies"][include],
                            file_type,
                            matrix_combo,
                            include,
                        )
                    )
                dependencies = dedupe(dependencies)

                # Dedupe deps and print / write to filesystem
                full_file_name = get_filename(file_type, file_name, matrix_combo)

                output_dir = (
                    "."
                    if to_stdout
                    else get_output_dir(
                        file_type, config_file_path, file_config, file_name
                    )
                )
                contents = make_dependency_file(
                    file_type,
                    full_file_name,
                    config_file_path,
                    output_dir,
                    channels,
                    dependencies,
                )

                if to_stdout:
                    print(contents)
                else:
                    file_path = os.path.join(output_dir, full_file_name)
                    os.makedirs(output_dir, exist_ok=True)
                    with open(file_path, "w") as f:
                        f.write(contents)
