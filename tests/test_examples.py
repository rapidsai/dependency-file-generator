import glob
import os
import pathlib
import shutil

import jsonschema
import pytest
import yaml
from jsonschema.exceptions import ValidationError

from rapids_dependency_file_generator._cli import main

CURRENT_DIR = pathlib.Path(__file__).parent

# Erroneous examples raise runtime errors from the generator.
_erroneous_examples = [
    "duplicate-specific-matrix-entries",
    "no-specific-match",
    "pyproject-no-extras",
    "pyproject_bad_key",
    "pyproject_matrix_multi",
    "requirements-pip-dict",
]
EXAMPLE_FILES = [
    pth
    for pth in CURRENT_DIR.glob("examples/*/dependencies.yaml")
    if all(ex not in str(pth.absolute()) for ex in _erroneous_examples)
]
# Invalid examples raise validation errors upon schema validation.
INVALID_EXAMPLE_FILES = list(CURRENT_DIR.glob("examples/invalid/*/dependencies.yaml"))


def make_file_set(file_dir):
    return {
        pathlib.Path(f).relative_to(file_dir)
        for f in glob.glob(str(file_dir) + "/**", recursive=True)
        if pathlib.Path(f).is_file()
    }


@pytest.fixture(
    params=[example_file.parent for example_file in EXAMPLE_FILES],
    ids=[example_file.parent.stem for example_file in EXAMPLE_FILES],
)
def example_dir(request):
    return request.param


@pytest.fixture(
    params=[example_file.parent for example_file in INVALID_EXAMPLE_FILES],
    ids=[example_file.parent.stem for example_file in INVALID_EXAMPLE_FILES],
)
def invalid_example_dir(request):
    return request.param


def test_examples(example_dir):
    expected_dir = example_dir.joinpath("output", "expected")
    actual_dir = example_dir.joinpath("output", "actual")
    dep_file_path = example_dir.joinpath("dependencies.yaml")

    # Copy pyproject.toml files from expected to actual since they are modified in place
    for dirpath, _, filenames in os.walk(expected_dir):
        for filename in filenames:
            if filename == "pyproject.toml":
                full_path = pathlib.Path(dirpath) / filename
                relative_path = full_path.relative_to(expected_dir)
                new_path = actual_dir / relative_path
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(full_path, new_path)

    cli_args = [
        "--config",
        str(dep_file_path),
        "--clean",
        str(example_dir.joinpath("output", "actual")),
    ]

    # Prepend channels for the prepend_channels tests
    if example_dir.name in ("prepend-channels"):
        cli_args = [
            "--prepend-channel",
            "my_channel",
            "--prepend-channel",
            "my_other_channel",
        ] + cli_args

    main(cli_args)

    expected_file_set = make_file_set(expected_dir)
    actual_file_set = make_file_set(actual_dir)

    assert expected_file_set == actual_file_set

    for file in actual_file_set:
        actual_file = open(actual_dir.joinpath(file)).read()
        expected_file = open(expected_dir.joinpath(file)).read()
        assert actual_file == expected_file


@pytest.mark.parametrize("test_name", _erroneous_examples)
def test_error_examples(test_name):
    test_dir = CURRENT_DIR.joinpath("examples", test_name)
    dep_file_path = test_dir.joinpath("dependencies.yaml")

    with pytest.raises(ValueError):
        main(
            [
                "--config",
                str(dep_file_path),
                "--clean",
                str(test_dir.joinpath("output", "actual")),
            ]
        )


def test_examples_are_valid(schema, example_dir):
    dep_file_path = example_dir / "dependencies.yaml"
    instance = yaml.load(dep_file_path.read_text(), Loader=yaml.SafeLoader)
    jsonschema.validate(instance, schema=schema)


def test_invalid_examples_are_invalid(schema, invalid_example_dir):
    dep_file_path = invalid_example_dir / "dependencies.yaml"
    instance = yaml.load(dep_file_path.read_text(), Loader=yaml.SafeLoader)
    with pytest.raises(ValidationError):
        jsonschema.validate(instance, schema=schema)
