import glob
import os
import pathlib
import shutil

import pytest

from rapids_dependency_file_generator.cli import main

CURRENT_DIR = pathlib.Path(__file__).parent


@pytest.fixture(scope="session", autouse=True)
def clean_actual_files():
    for root, _, _ in os.walk("tests"):
        if pathlib.Path(root).name == "actual":
            shutil.rmtree(root)


def make_file_set(file_dir):
    return {
        pathlib.Path(f).relative_to(file_dir)
        for f in glob.glob(str(file_dir) + "/**", recursive=True)
        if pathlib.Path(f).is_file()
    }


@pytest.mark.parametrize(
    "test_name",
    [
        "conda-meta",
        "conda-minimal",
        "integration",
        "matrix",
        "no-matrix",
        "requirements-minimal",
        "specific-fallback-first",
        "specific-fallback",
    ],
)
def test_examples(test_name):
    test_dir = CURRENT_DIR.joinpath("examples", test_name)
    expected_dir = test_dir.joinpath("output", "expected")
    actual_dir = test_dir.joinpath("output", "actual")
    dep_file_path = test_dir.joinpath("dependencies.yaml")

    main(["--config", str(dep_file_path)])

    expected_file_set = make_file_set(expected_dir)
    actual_file_set = make_file_set(actual_dir)

    assert expected_file_set == actual_file_set

    for file in actual_file_set:
        actual_file = open(actual_dir.joinpath(file)).read()
        expected_file = open(expected_dir.joinpath(file)).read()
        assert actual_file == expected_file


@pytest.mark.parametrize("test_name", ["no-specific-match"])
def test_error_examples(test_name):
    test_dir = CURRENT_DIR.joinpath("examples", test_name)
    dep_file_path = test_dir.joinpath("dependencies.yaml")

    with pytest.raises(ValueError):
        main(["--config", str(dep_file_path)])
