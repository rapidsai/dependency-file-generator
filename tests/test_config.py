import tempfile
import textwrap
from pathlib import Path

import pytest

from rapids_dependency_file_generator import config, constants


@pytest.mark.parametrize(
    ["input", "output"],
    [
        *((e.value, {e}) for e in config.Output),
        ("none", set()),
        (["none"], set()),
        (
            ["pyproject", "requirements", "conda"],
            {config.Output.PYPROJECT, config.Output.REQUIREMENTS, config.Output.CONDA},
        ),
        ("invalid", ValueError),
        (["invalid"], ValueError),
        (["none", "pyproject"], ValueError),
    ],
)
def test_parse_outputs(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            config._parse_outputs(input)
    else:
        assert config._parse_outputs(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        ("package", "package"),
        ({"pip": "package"}, config.PipRequirements(pip="package")),
        ({"other": "invalid"}, KeyError),
    ],
)
def test_parse_requirement(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            config._parse_requirement(input)
    else:
        assert config._parse_requirement(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            {"table": "build-system", "key": "requires"},
            config.FileExtras(table="build-system", key="requires"),
        ),
        (
            {"table": "build-system"},
            config.FileExtras(table="build-system", key=None),
        ),
        ({}, KeyError),
    ],
)
def test_parse_extras(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            config._parse_extras(input)
    else:
        assert config._parse_extras(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            {
                "output": "none",
                "includes": [],
            },
            config.File(
                output=set(),
                extras=None,
                includes=[],
                matrix={},
                requirements_dir=Path(constants.default_requirements_dir),
                conda_dir=Path(constants.default_conda_dir),
                pyproject_dir=Path(constants.default_pyproject_dir),
            ),
        ),
        (
            {
                "output": ["conda", "pyproject"],
                "extras": {
                    "table": "build-system",
                    "key": "requires",
                },
                "includes": ["py_build", "py_run"],
                "matrix": {
                    "cuda": ["11", "12"],
                    "arch": ["x86_64", "aarch64"],
                },
                "requirements_dir": "python_requirements",
                "conda_dir": "conda_recipe",
                "pyproject_dir": "python_pyproject",
            },
            config.File(
                output={config.Output.CONDA, config.Output.PYPROJECT},
                extras=config.FileExtras(table="build-system", key="requires"),
                includes=["py_build", "py_run"],
                matrix={
                    "cuda": ["11", "12"],
                    "arch": ["x86_64", "aarch64"],
                },
                requirements_dir=Path("python_requirements"),
                conda_dir=Path("conda_recipe"),
                pyproject_dir=Path("python_pyproject"),
            ),
        ),
    ],
)
def test_parse_file(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            config._parse_file(input)
    else:
        assert config._parse_file(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            {},
            config.Dependencies(common=[], specific=[]),
        ),
        (
            {
                "common": [
                    {
                        "output_types": "none",
                        "packages": [],
                    },
                    {
                        "output_types": ["pyproject", "requirements"],
                        "packages": [
                            "package1",
                            {
                                "pip": ["package2"],
                            },
                        ],
                    },
                ],
                "specific": [
                    {
                        "output_types": "none",
                        "matrices": [
                            {
                                "matrix": None,
                                "packages": None,
                            },
                        ],
                    },
                    {
                        "output_types": ["requirements", "conda"],
                        "matrices": [
                            {
                                "matrix": {
                                    "cuda": "11",
                                    "arch": "x86_64",
                                },
                                "packages": [
                                    "package3",
                                    {
                                        "pip": ["package4"],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            config.Dependencies(
                common=[
                    config.CommonDependencies(
                        output_types=set(),
                        packages=[],
                    ),
                    config.CommonDependencies(
                        output_types={
                            config.Output.PYPROJECT,
                            config.Output.REQUIREMENTS,
                        },
                        packages=[
                            "package1",
                            config.PipRequirements(pip=["package2"]),
                        ],
                    ),
                ],
                specific=[
                    config.SpecificDependencies(
                        output_types=set(),
                        matrices=[
                            config.MatrixMatcher(
                                matrix={},
                                packages=[],
                            ),
                        ],
                    ),
                    config.SpecificDependencies(
                        output_types={config.Output.REQUIREMENTS, config.Output.CONDA},
                        matrices=[
                            config.MatrixMatcher(
                                matrix={"cuda": "11", "arch": "x86_64"},
                                packages=[
                                    "package3",
                                    config.PipRequirements(pip=["package4"]),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ),
    ],
)
def test_parse_dependencies(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            config._parse_dependencies(input)
    else:
        assert config._parse_dependencies(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        ("conda-forge", ["conda-forge"]),
        (["conda-forge", "nvidia"], ["conda-forge", "nvidia"]),
    ],
)
def test_parse_channels(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            config._parse_channels(input)
    else:
        assert config._parse_channels(input) == output


@pytest.mark.parametrize(
    ["input", "path", "output"],
    [
        (
            {
                "files": {
                    "python": {
                        "output": "pyproject",
                        "includes": ["py_build"],
                    },
                },
                "channels": [
                    "conda-forge",
                    "nvidia",
                ],
                "dependencies": {
                    "py_build": {
                        "common": [
                            {
                                "output_types": "pyproject",
                                "packages": [
                                    "package1",
                                ],
                            },
                        ],
                        "specific": [
                            {
                                "output_types": ["conda", "requirements"],
                                "matrices": [
                                    {
                                        "matrix": None,
                                        "packages": None,
                                    },
                                ],
                            },
                        ],
                    },
                },
            },
            "dependencies.yaml",
            config.Config(
                path=Path("dependencies.yaml"),
                files={
                    "python": config.File(
                        output={config.Output.PYPROJECT},
                        includes=["py_build"],
                    ),
                },
                channels=[
                    "conda-forge",
                    "nvidia",
                ],
                dependencies={
                    "py_build": config.Dependencies(
                        common=[
                            config.CommonDependencies(
                                output_types={config.Output.PYPROJECT},
                                packages=[
                                    "package1",
                                ],
                            ),
                        ],
                        specific=[
                            config.SpecificDependencies(
                                output_types={
                                    config.Output.CONDA,
                                    config.Output.REQUIREMENTS,
                                },
                                matrices=[
                                    config.MatrixMatcher(
                                        matrix={},
                                        packages=[],
                                    ),
                                ],
                            ),
                        ],
                    ),
                },
            ),
        ),
    ],
)
def test_parse_config(input, path, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            config.parse_config(input, path)
    else:
        assert config.parse_config(input, path) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            textwrap.dedent(
                """\
                files:
                  python:
                    output: "pyproject"
                    includes: ["py_build"]
                channels:
                  - conda-forge
                  - nvidia
                dependencies:
                  py_build:
                    common:
                      - output_types: "pyproject"
                        packages:
                          - package1
                    specific:
                      - output_types: ["conda", "requirements"]
                        matrices:
                          - matrix:
                            packages:
                """
            ),
            config.Config(
                path=Path("dependencies.yaml"),
                files={
                    "python": config.File(
                        output={config.Output.PYPROJECT},
                        includes=["py_build"],
                    ),
                },
                channels=[
                    "conda-forge",
                    "nvidia",
                ],
                dependencies={
                    "py_build": config.Dependencies(
                        common=[
                            config.CommonDependencies(
                                output_types={config.Output.PYPROJECT},
                                packages=[
                                    "package1",
                                ],
                            ),
                        ],
                        specific=[
                            config.SpecificDependencies(
                                output_types={
                                    config.Output.CONDA,
                                    config.Output.REQUIREMENTS,
                                },
                                matrices=[
                                    config.MatrixMatcher(
                                        matrix={},
                                        packages=[],
                                    ),
                                ],
                            ),
                        ],
                    ),
                },
            ),
        ),
    ],
)
def test_load_config_from_file(input, output):
    with tempfile.NamedTemporaryFile("w") as f:
        f.write(input)
        f.flush()

        if isinstance(output, type) and issubclass(output, Exception):
            with pytest.raises(output):
                config.load_config_from_file(f.name)
        else:
            output.path = Path(f.name)
            assert config.load_config_from_file(f.name) == output
