from unittest import mock

import yaml
import tomlkit
import pathlib

from rapids_dependency_file_generator import _config
from rapids_dependency_file_generator._constants import cli_name
from rapids_dependency_file_generator._rapids_dependency_file_generator import (
    dedupe,
    make_dependency_file,
    make_dependency_files,
    should_use_specific_entry,
)


def test_dedupe():
    # simple list
    deduped = dedupe(["dep1", "dep1", "dep2"])
    assert deduped == ["dep1", "dep2"]

    # list w/ pip dependencies
    deduped = dedupe(
        [
            "dep1",
            "dep1",
            _config.PipRequirements(pip=["pip_dep1", "pip_dep2"]),
            _config.PipRequirements(pip=["pip_dep1", "pip_dep2"]),
        ]
    )
    assert deduped == ["dep1", {"pip": ["pip_dep1", "pip_dep2"]}]


@mock.patch(
    "rapids_dependency_file_generator._rapids_dependency_file_generator.os.path.relpath"
)
def test_make_dependency_file(mock_relpath):
    relpath = "../../config_file.yaml"
    mock_relpath.return_value = relpath
    header = f"""\
# This file is generated by `{cli_name}`.
# To make changes, edit {relpath} and run `{cli_name}`.
"""
    env = make_dependency_file(
        file_type=_config.Output.CONDA,
        name="tmp_env.yaml",
        config_file="config_file",
        output_dir="output_path",
        conda_channels=["rapidsai", "nvidia"],
        dependencies=["dep1", "dep2"],
        extras=None,
    )
    assert env == header + yaml.dump(
        {
            "name": "tmp_env",
            "channels": ["rapidsai", "nvidia"],
            "dependencies": ["dep1", "dep2"],
        }
    )

    env = make_dependency_file(
        file_type=_config.Output.REQUIREMENTS,
        name="tmp_env.txt",
        config_file="config_file",
        output_dir="output_path",
        conda_channels=["rapidsai", "nvidia"],
        dependencies=["dep1", "dep2"],
        extras=None,
    )
    assert env == header + "dep1\ndep2\n"


def test_make_dependency_files_should_choose_correct_pyproject_toml(capsys):

    current_dir = pathlib.Path(__file__).parent
    make_dependency_files(
        parsed_config=_config.load_config_from_file(current_dir / "examples" / "nested-pyproject" / "dependencies.yaml"),
        file_keys=["sparkly_unicorn"],
        output={_config.Output.PYPROJECT},
        matrix={"cuda": ["100.17"]},
        prepend_channels=[],
        to_stdout=True
    )
    captured_stdout = capsys.readouterr().out

    # should be valid TOML, containing the expected dependencies and the other contents of
    # the nested pyproject.toml file
    doc = tomlkit.loads(captured_stdout)
    assert doc["project"]["name"] == "beep-boop"
    assert doc["project"]["version"] == "1.2.3"
    assert sorted(doc["project"]["dependencies"]) == ["cuda-python>=100.1,<101.0a0", "fsspec>=0.6.0"]

    # and should NOT contain anything from the root-level pyproject.toml
    assert set(dict(doc).keys()) == {"project"}


def test_should_use_specific_entry():
    # no match
    matrix_combo = {"cuda": "11.5", "arch": "x86_64"}
    specific_entry = {"cuda": "11.6"}
    result = should_use_specific_entry(matrix_combo, specific_entry)
    assert result is False

    # one match
    matrix_combo = {"cuda": "11.5", "arch": "x86_64"}
    specific_entry = {"cuda": "11.5"}
    result = should_use_specific_entry(matrix_combo, specific_entry)
    assert result is True

    # many matches
    matrix_combo = {"cuda": "11.5", "arch": "x86_64", "python": "3.6"}
    specific_entry = {"cuda": "11.5", "arch": "x86_64"}
    result = should_use_specific_entry(matrix_combo, specific_entry)
    assert result is True
