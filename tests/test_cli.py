from rapids_dependency_file_generator.cli import generate_matrix, validate_args


def test_generate_matrix():
    matrix = generate_matrix("cuda=11.5;arch=x86_64")
    assert matrix == {"cuda": ["11.5"], "arch": ["x86_64"]}

    matrix = generate_matrix(None)
    assert matrix == {}


def test_validate_args():
    # Missing output
    validate_args(["--matrix", "cuda=11.5;arch=x86_64", "--file_key", "all"])

    # Missing matrix
    validate_args(["--output", "conda", "--file_key", "all"])

    # Missing file_key
    validate_args(["--output", "conda", "--matrix", "cuda=11.5;arch=x86_64"])

    # Multiple outputs
    validate_args(["-o", "conda", "--output", "requirements", "pyproject"])

    # Multiple file keys
    validate_args(["-f", "all", "--file-key", "all", "--file_key", "all", "all"])

    # Valid
    validate_args(
        [
            "--output",
            "conda",
            "--matrix",
            "cuda=11.5;arch=x86_64",
            "--file_key",
            "all",
        ]
    )
