from dataclasses import dataclass, field
from enum import Enum
from os import PathLike
from pathlib import Path

import yaml

from . import constants
from .rapids_dependency_file_validator import validate_dependencies


class Output(Enum):
    PYPROJECT = "pyproject"
    REQUIREMENTS = "requirements"
    CONDA = "conda"


@dataclass
class FileExtras:
    table: str
    key: str | None = None


@dataclass
class File:
    output: set[Output]
    includes: list[str]
    extras: FileExtras | None = None
    matrix: dict[str, list[str]] = field(default_factory=dict)
    requirements_dir: Path = Path(constants.default_requirements_dir)
    conda_dir: Path = Path(constants.default_conda_dir)
    pyproject_dir: Path = Path(constants.default_pyproject_dir)


@dataclass
class PipRequirements:
    pip: list[str]


@dataclass
class CommonDependencies:
    output_types: set[Output]
    packages: list[str | PipRequirements]


@dataclass
class MatrixMatcher:
    matrix: dict[str, str]
    packages: list[str | PipRequirements]


@dataclass
class SpecificDependencies:
    output_types: set[Output]
    matrices: list[MatrixMatcher]


@dataclass
class Dependencies:
    common: list[CommonDependencies] = field(default_factory=list)
    specific: list[SpecificDependencies] = field(default_factory=list)


@dataclass
class Config:
    path: Path
    files: dict[str, File] = field(default_factory=dict)
    channels: list[str] = field(
        default_factory=lambda: list(constants.default_channels)
    )
    dependencies: dict[str, Dependencies] = field(default_factory=dict)


def _parse_outputs(outputs: str | list[str]) -> set[Output]:
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


def _parse_file(file_config: dict[str, object]) -> File:
    def get_extras():
        try:
            extras = file_config["extras"]
        except KeyError:
            return None

        return _parse_extras(extras)

    return File(
        output=_parse_outputs(file_config["output"]),
        extras=get_extras(),
        includes=list(file_config["includes"]),
        matrix={
            key: list(value) for key, value in file_config.get("matrix", {}).items()
        },
        requirements_dir=Path(
            file_config.get("requirements_dir", constants.default_requirements_dir)
        ),
        conda_dir=Path(file_config.get("conda_dir", constants.default_conda_dir)),
        pyproject_dir=Path(
            file_config.get("pyproject_dir", constants.default_pyproject_dir)
        ),
    )


def _parse_requirement(requirement: str | dict[str, str]) -> str | PipRequirements:
    if isinstance(requirement, str):
        return requirement

    return PipRequirements(pip=requirement["pip"])


def _parse_dependencies(dependencies: dict[str, object]) -> Dependencies:
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
                        packages=[
                            _parse_requirement(p) for p in m.get("packages", []) or []
                        ],
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


def parse_config(config: dict[str, object], path: PathLike) -> Config:
    validate_dependencies(config)
    return Config(
        path=Path(path),
        files={key: _parse_file(value) for key, value in config["files"].items()},
        channels=_parse_channels(config.get("channels", [])),
        dependencies={
            key: _parse_dependencies(value)
            for key, value in config["dependencies"].items()
        },
    )


def load_config_from_file(path: PathLike) -> Config:
    with open(path) as f:
        return parse_config(yaml.safe_load(f), path)
