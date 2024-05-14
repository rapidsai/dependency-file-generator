import typing
from dataclasses import dataclass, field
from enum import Enum
from os import PathLike
from pathlib import Path

import yaml

from . import _constants
from ._rapids_dependency_file_validator import validate_dependencies

__all__ = [
    "Output",
    "FileExtras",
    "File",
    "PipRequirements",
    "CommonDependencies",
    "MatrixMatcher",
    "SpecificDependencies",
    "Dependencies",
    "Config",
    "parse_config",
    "load_config_from_file",
]


class Output(Enum):
    """An output file type to generate."""

    PYPROJECT = "pyproject"
    """Generate a ``pyproject.toml``."""

    REQUIREMENTS = "requirements"
    """Generate a ``requirements.txt``."""

    CONDA = "conda"
    """Generate a Conda environment file."""


@dataclass
class FileExtras:
    """The ``extras`` field of a file key in ``dependencies.yaml``."""

    table: str
    """The ``table`` field."""

    key: typing.Union[str, None] = None
    """The ``key`` field."""


@dataclass
class File:
    """A file key in ``dependencies.yaml``."""

    output: set[Output]
    """The set of output file types to generate."""

    includes: list[str]
    """The list of dependency sets to include."""

    extras: typing.Union[FileExtras, None] = None
    """Optional extra information for the file generator."""

    matrix: dict[str, list[str]] = field(default_factory=dict)
    """The matrix of specific parameters to use when generating."""

    requirements_dir: Path = Path(_constants.default_requirements_dir)
    """The directory in which to write ``requirements.txt``."""

    conda_dir: Path = Path(_constants.default_conda_dir)
    """The directory in which to write the Conda environment file."""

    pyproject_dir: Path = Path(_constants.default_pyproject_dir)
    """The directory in which to write ``pyproject.toml``."""


@dataclass
class PipRequirements:
    """A list of Pip requirements to include as dependencies."""

    pip: list[str]
    """The list of Pip requirements."""


@dataclass
class CommonDependencies:
    """A dependency entry in the ``common`` field of a dependency set."""

    output_types: set[Output]
    """The set of output types for this entry."""

    packages: list[typing.Union[str, PipRequirements]]
    """The list of packages for this entry."""


@dataclass
class MatrixMatcher:
    """A matrix matcher for a ``specific`` dependency entry."""

    matrix: dict[str, str]
    """The set of matrix values to match."""

    packages: list[typing.Union[str, PipRequirements]]
    """The list of packages for this entry."""


@dataclass
class SpecificDependencies:
    """A dependency entry in the ``specific`` field of a dependency set."""

    output_types: set[Output]
    """The set of output types for this entry."""

    matrices: list[MatrixMatcher]
    """The list of matrix matchers for this entry."""


@dataclass
class Dependencies:
    """A dependency set."""

    common: list[CommonDependencies] = field(default_factory=list)
    """The list of common dependency entries."""

    specific: list[SpecificDependencies] = field(default_factory=list)
    """The list of specific dependency entries."""


@dataclass
class Config:
    """A fully parsed ``dependencies.yaml`` file."""

    path: Path
    """The path to the parsed file."""

    files: dict[str, File] = field(default_factory=dict)
    """The file entries, keyed by name."""

    channels: list[str] = field(default_factory=lambda: list(_constants.default_channels))
    """A list of channels to include in Conda files."""

    dependencies: dict[str, Dependencies] = field(default_factory=dict)
    """The dependency sets, keyed by name."""


def _parse_outputs(outputs: typing.Union[str, list[str]]) -> set[Output]:
    if isinstance(outputs, str):
        outputs = [outputs]
    if outputs == ["none"]:
        outputs = []
    return {Output(o) for o in outputs}


def _parse_extras(extras: dict[str, str]) -> FileExtras:
    return FileExtras(
        table=extras["table"],
        key=extras.get("key", None),
    )


def _parse_file(file_config: dict[str, typing.Any]) -> File:
    def get_extras() -> typing.Union[FileExtras, None]:
        try:
            extras = file_config["extras"]
        except KeyError:
            return None

        return _parse_extras(extras)

    return File(
        output=_parse_outputs(file_config["output"]),
        extras=get_extras(),
        includes=list(file_config["includes"]),
        matrix={key: list(value) for key, value in file_config.get("matrix", {}).items()},
        requirements_dir=Path(file_config.get("requirements_dir", _constants.default_requirements_dir)),
        conda_dir=Path(file_config.get("conda_dir", _constants.default_conda_dir)),
        pyproject_dir=Path(file_config.get("pyproject_dir", _constants.default_pyproject_dir)),
    )


def _parse_requirement(requirement: typing.Union[str, dict[str, list[str]]]) -> typing.Union[str, PipRequirements]:
    if isinstance(requirement, str):
        return requirement

    return PipRequirements(pip=requirement["pip"])


def _parse_dependencies(dependencies: dict[str, typing.Any]) -> Dependencies:
    return Dependencies(
        common=[
            CommonDependencies(
                output_types=_parse_outputs(d["output_types"]),
                packages=[_parse_requirement(p) for p in d["packages"]],
            )
            for d in dependencies.get("common", [])
        ],
        specific=[
            SpecificDependencies(
                output_types=_parse_outputs(d["output_types"]),
                matrices=[
                    MatrixMatcher(
                        matrix=dict(m.get("matrix", {}) or {}),
                        packages=[_parse_requirement(p) for p in m.get("packages", []) or []],
                    )
                    for m in d["matrices"]
                ],
            )
            for d in dependencies.get("specific", [])
        ],
    )


def _parse_channels(channels) -> list[str]:
    if isinstance(channels, str):
        return [channels]

    return list(channels)


def parse_config(config: dict[str, typing.Any], path: PathLike) -> Config:
    """Parse a configuration file from a dictionary.

    Parameters
    ----------
    config : dict[str, Any]
        The dictionary to parse.
    path : PathLike
        The path to the parsed configuration file. This will be stored as the ``path``
        attribute.

    Returns
    -------
    Config
        The fully parsed configuration file.

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If the dependencies do not conform to the schema
    """
    validate_dependencies(config)
    return Config(
        path=Path(path),
        files={key: _parse_file(value) for key, value in config["files"].items()},
        channels=_parse_channels(config.get("channels", [])),
        dependencies={key: _parse_dependencies(value) for key, value in config["dependencies"].items()},
    )


def load_config_from_file(path: PathLike) -> Config:
    """Open a ``dependencies.yaml`` file and parse it.

    Parameters
    ----------
    path : PathLike
        The path to the configuration file to parse.

    Returns
    -------
    Config
        The fully parsed configuration file.
    """
    with open(path) as f:
        return parse_config(yaml.safe_load(f), path)
