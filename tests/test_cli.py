from unittest import mock
from unittest.mock import mock_open

from rapids_dependency_file_generator.cli import generate_file_obj, generate_matrix

mock_yaml = """
files:
  test:
    generate: none
    includes:
      - build
      - test
"""


@mock.patch(
    "builtins.open",
    mock_open(read_data=mock_yaml),
)
def test_generate_file_obj():
    # valid env
    file_obj = generate_file_obj(
        "na_file", "test", "conda", {"cuda": ["11.5"], "arch": ["x86_64"]}
    )

    assert file_obj == {
        "test": {
            "generate": "conda",
            "matrix": {"cuda": ["11.5"], "arch": ["x86_64"]},
            "includes": ["build", "test"],
        }
    }

    # invalid env: missing config_file
    file_obj = generate_file_obj("", "file_key", "file_type", "matrix")
    assert file_obj == {}

    # invalid env: missing file_key
    file_obj = generate_file_obj("config_file", "", "file_type", "matrix")
    assert file_obj == {}

    # invalid env: missing file_type
    file_obj = generate_file_obj("config_file", "file_key", "", "matrix")
    assert file_obj == {}

    # invalid env: missing matrix
    file_obj = generate_file_obj("config_file", "file_key", "file_type", "")
    assert file_obj == {}


def test_generate_matrix():
    matrix = generate_matrix("cuda=11.5;arch=x86_64")
    assert matrix == {"cuda": ["11.5"], "arch": ["x86_64"]}
