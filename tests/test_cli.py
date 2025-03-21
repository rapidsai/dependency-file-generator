import pytest

from rapids_dependency_file_generator._cli import generate_matrix, validate_args


def test_generate_matrix():
    matrix = generate_matrix("cuda=11.5;arch=x86_64")
    assert matrix == {"cuda": ["11.5"], "arch": ["x86_64"]}

    matrix = generate_matrix(None)
    assert matrix is None


def test_generate_matrix_allows_duplicates_and_chooses_the_final_value():
    # duplicate keys
    matrix = generate_matrix("thing=abc;other_thing=true;thing=def;thing=ghi")
    assert matrix == {"other_thing": ["true"], "thing": ["ghi"]}

    # duplicate keys and values
    matrix = generate_matrix("thing=abc;thing=abc")
    assert matrix == {"thing": ["abc"]}


def test_validate_args():
    # Missing output
    with pytest.raises(Exception):
        validate_args(["--matrix", "cuda=11.5;arch=x86_64", "--file-key", "all"])

    # Missing matrix
    with pytest.raises(Exception):
        validate_args(["--output", "conda", "--file-key", "all"])

    # Missing file_key
    with pytest.raises(Exception):
        validate_args(["--output", "conda", "--matrix", "cuda=11.5;arch=x86_64"])

    # Prepending channels with an output type that is not conda
    with pytest.raises(Exception):
        validate_args(
            [
                "--output",
                "requirements",
                "--matrix",
                "cuda=11.5;arch=x86_64",
                "--file-key",
                "all",
                "--prepend-channel",
                "my_channel",
                "--prepend-channel",
                "my_other_channel",
            ]
        )

    # Valid
    validate_args(
        [
            "--output",
            "conda",
            "--matrix",
            "cuda=11.5;arch=x86_64",
            "--file-key",
            "all",
        ]
    )

    # Valid
    validate_args(
        [
            "--config",
            "dependencies2.yaml",
            "--output",
            "pyproject",
            "--matrix",
            "cuda=11.5;arch=x86_64",
            "--file-key",
            "all",
        ]
    )

    # Valid
    validate_args(
        [
            "-c",
            "dependencies2.yaml",
            "--output",
            "pyproject",
            "--matrix",
            "cuda=11.5;arch=x86_64",
            "--file-key",
            "all",
        ]
    )

    # Valid, with prepended channels
    validate_args(
        [
            "--prepend-channel",
            "my_channel",
            "--prepend-channel",
            "my_other_channel",
        ]
    )

    # Valid, with output/matrix/file_key and prepended channels
    validate_args(
        [
            "--output",
            "conda",
            "--matrix",
            "cuda=11.5;arch=x86_64",
            "--file-key",
            "all",
            "--prepend-channel",
            "my_channel",
            "--prepend-channel",
            "my_other_channel",
        ]
    )

    # Valid, with duplicates in --matrix
    validate_args(
        [
            "-c",
            "dependencies2.yaml",
            "--output",
            "pyproject",
            "--matrix",
            "cuda_suffixed=true;arch=x86_64;cuda_suffixed=false",
            "--file-key",
            "all",
        ]
    )

    # Valid, with 2 files for --output requirements
    validate_args(
        [
            "--output",
            "requirements",
            "--matrix",
            "cuda=12.5",
            "--file-key",
            "all",
            "--file-key",
            "test_python",
        ]
    )

    # Valid, with 2 files for --output conda
    validate_args(
        [
            "--output",
            "conda",
            "--matrix",
            "cuda=12.5",
            "--file-key",
            "all",
            "--file-key",
            "test_python",
        ]
    )

    # Valid, with 3 files
    validate_args(
        [
            "--output",
            "requirements",
            "--matrix",
            "cuda=12.5",
            "--file-key",
            "all",
            "--file-key",
            "test_python",
            "--file-key",
            "build_python",
        ]
    )

    # Verify --version flag
    args = validate_args([])
    assert not args.version

    args = validate_args(["--version"])
    assert args.version
