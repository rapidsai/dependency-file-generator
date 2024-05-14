import tempfile
import textwrap
from pathlib import Path

import pytest

from rapids_dependency_file_generator import _config, _constants


@pytest.mark.parametrize(
    ["input", "output"],
    [
        *((e.value, {e}) for e in _config.Output),
        ("none", set()),
        (["none"], set()),
        (
            ["pyproject", "requirements", "conda"],
            {
                _config.Output.PYPROJECT,
                _config.Output.REQUIREMENTS,
                _config.Output.CONDA,
            },
        ),
        ("invalid", ValueError),
        (["invalid"], ValueError),
        (["none", "pyproject"], ValueError),
    ],
)
def test_parse_outputs(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            _config._parse_outputs(input)
    else:
        assert _config._parse_outputs(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        ("package", "package"),
        ({"pip": ["package", "other-package"]}, _config.PipRequirements(pip=["package", "other-package"])),
        ({"other": "invalid"}, KeyError),
    ],
)
def test_parse_requirement(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            _config._parse_requirement(input)
    else:
        assert _config._parse_requirement(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            {"table": "build-system", "key": "requires"},
            _config.FileExtras(table="build-system", key="requires"),
        ),
        (
            {"table": "build-system"},
            _config.FileExtras(table="build-system", key=None),
        ),
        ({}, KeyError),
    ],
)
def test_parse_extras(input, output):
    if isinstance(output, type) and issubclass(output, Exception):
        with pytest.raises(output):
            _config._parse_extras(input)
    else:
        assert _config._parse_extras(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            {
                "output": "none",
                "includes": [],
            },
            _config.File(
                output=set(),
                extras=None,
                includes=[],
                matrix={},
                requirements_dir=Path(_constants.default_requirements_dir),
                conda_dir=Path(_constants.default_conda_dir),
                pyproject_dir=Path(_constants.default_pyproject_dir),
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
            _config.File(
                output={_config.Output.CONDA, _config.Output.PYPROJECT},
                extras=_config.FileExtras(table="build-system", key="requires"),
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
            _config._parse_file(input)
    else:
        assert _config._parse_file(input) == output


@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            {},
            _config.Dependencies(common=[], specific=[]),
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
            _config.Dependencies(
                common=[
                    _config.CommonDependencies(
                        output_types=set(),
                        packages=[],
                    ),
                    _config.CommonDependencies(
                        output_types={
                            _config.Output.PYPROJECT,
                            _config.Output.REQUIREMENTS,
                        },
                        packages=[
                            "package1",
                            _config.PipRequirements(pip=["package2"]),
                        ],
                    ),
                ],
                specific=[
                    _config.SpecificDependencies(
                        output_types=set(),
                        matrices=[
                            _config.MatrixMatcher(
                                matrix={},
                                packages=[],
                            ),
                        ],
                    ),
                    _config.SpecificDependencies(
                        output_types={
                            _config.Output.REQUIREMENTS,
                            _config.Output.CONDA,
                        },
                        matrices=[
                            _config.MatrixMatcher(
                                matrix={"cuda": "11", "arch": "x86_64"},
                                packages=[
                                    "package3",
                                    _config.PipRequirements(pip=["package4"]),
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
            _config._parse_dependencies(input)
    else:
        assert _config._parse_dependencies(input) == output


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
            _config._parse_channels(input)
    else:
        assert _config._parse_channels(input) == output


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
            _config.Config(
                path=Path("dependencies.yaml"),
                files={
                    "python": _config.File(
                        output={_config.Output.PYPROJECT},
                        includes=["py_build"],
                    ),
                },
                channels=[
                    "conda-forge",
                    "nvidia",
                ],
                dependencies={
                    "py_build": _config.Dependencies(
                        common=[
                            _config.CommonDependencies(
                                output_types={_config.Output.PYPROJECT},
                                packages=[
                                    "package1",
                                ],
                            ),
                        ],
                        specific=[
                            _config.SpecificDependencies(
                                output_types={
                                    _config.Output.CONDA,
                                    _config.Output.REQUIREMENTS,
                                },
                                matrices=[
                                    _config.MatrixMatcher(
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
            _config.parse_config(input, path)
    else:
        assert _config.parse_config(input, path) == output


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
            _config.Config(
                path=Path("dependencies.yaml"),
                files={
                    "python": _config.File(
                        output={_config.Output.PYPROJECT},
                        includes=["py_build"],
                    ),
                },
                channels=[
                    "conda-forge",
                    "nvidia",
                ],
                dependencies={
                    "py_build": _config.Dependencies(
                        common=[
                            _config.CommonDependencies(
                                output_types={_config.Output.PYPROJECT},
                                packages=[
                                    "package1",
                                ],
                            ),
                        ],
                        specific=[
                            _config.SpecificDependencies(
                                output_types={
                                    _config.Output.CONDA,
                                    _config.Output.REQUIREMENTS,
                                },
                                matrices=[
                                    _config.MatrixMatcher(
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
                _config.load_config_from_file(f.name)
        else:
            output.path = Path(f.name)
            assert _config.load_config_from_file(f.name) == output
