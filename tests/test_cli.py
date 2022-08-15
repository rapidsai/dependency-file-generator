from unittest import mock
from unittest.mock import mock_open
from rapids_dependency_file_generator.cli import generate_file_obj

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
    file_obj = generate_file_obj("na_file", "test", "conda", "11.5", "x86_64")

    assert file_obj == {
        "test": {
            "generate": "conda",
            "matrix": {"cuda_version": ["11.5"], "arch": ["x86_64"]},
            "includes": ["build", "test"],
        }
    }

    # invalid env: missing config_file
    file_obj = generate_file_obj("", "file_key", "file_type", "cuda_version", "arch")
    assert file_obj == {}

    # invalid env: missing file_key
    file_obj = generate_file_obj("config_file", "", "file_type", "cuda_version", "arch")
    assert file_obj == {}

    # invalid env: missing file_type
    file_obj = generate_file_obj("config_file", "file_key", "", "cuda_version", "arch")
    assert file_obj == {}

    # invalid env: missing cuda_version
    file_obj = generate_file_obj("config_file", "file_key", "file_type", "", "arch")
    assert file_obj == {}

    # invalid env: missing arch
    file_obj = generate_file_obj(
        "config_file", "file_key", "file_type", "cuda_version", ""
    )
    assert file_obj == {}
