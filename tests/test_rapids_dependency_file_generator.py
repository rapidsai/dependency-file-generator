from unittest import mock
from rapids_dependency_file_generator.rapids_dependency_file_generator import (
    dedupe,
    make_dependency_file,
)
from rapids_dependency_file_generator.constants import cli_name
import yaml


def test_dedupe():
    # simple list
    deduped = dedupe(["dep1", "dep1", "dep2"])
    assert deduped == ["dep1", "dep2"]

    # list w/ pip dependencies
    deduped = dedupe(
        [
            "dep1",
            "dep1",
            {"pip": ["pip_dep1", "pip_dep2"]},
            {"pip": ["pip_dep1", "pip_dep2"]},
        ]
    )
    assert deduped == ["dep1", {"pip": ["pip_dep1", "pip_dep2"]}]


@mock.patch("rapids_dependency_file_generator.rapids_dependency_file_generator.os.path")
def test_make_dependency_file(mock_path):
    relpath = "../../dependencies.yaml"
    mock_path.relpath.return_value = relpath
    header = f"""\
# This file was automatically generated. Changes should not be made directly to this file.
# Instead, edit {relpath} and rerun `{cli_name}`.
"""
    env = make_dependency_file(
        "conda",
        "tmp_env",
        "config_file",
        "output_path",
        ["rapidsai", "nvidia"],
        ["dep1", "dep2"],
    )
    assert env == header + yaml.dump(
        {
            "name": "tmp_env",
            "channels": ["rapidsai", "nvidia"],
            "dependencies": ["dep1", "dep2"],
        }
    )

    env = make_dependency_file(
        "requirements",
        "tmp_env",
        "config_file",
        "output_path",
        ["rapidsai", "nvidia"],
        ["dep1", "dep2"],
    )
    assert env == header + "dep1\ndep2\n"
