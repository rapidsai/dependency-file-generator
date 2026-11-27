import contextlib
import os.path
from textwrap import dedent

import pytest

from rapids_dependency_file_generator._cli import generate_matrix, main, validate_args
from rapids_dependency_file_generator._rapids_dependency_file_validator import UnusedDependencySetWarning


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


@pytest.mark.parametrize(
    ["extra_args", "context"],
    [
        (
            [],
            contextlib.nullcontext(),
        ),
        (
            ["--strict"],
            contextlib.nullcontext(),
        ),
        (
            ["--warn-unused-dependencies"],
            pytest.warns(UnusedDependencySetWarning),
        ),
        (
            ["--warn-unused-dependencies", "--strict"],
            pytest.raises(UnusedDependencySetWarning),
        ),
        (
            ["--warn-all"],
            pytest.warns(UnusedDependencySetWarning),
        ),
        (
            ["--warn-all", "--strict"],
            pytest.raises(UnusedDependencySetWarning),
        ),
    ],
)
def test_warnings(tmp_path, extra_args, context):
    config_file = os.path.join(tmp_path, "dependencies.yaml")
    with open(config_file, "w") as f:
        f.write(dedent("""
        files:
          all:
            output: conda
            includes: [a]
        channels: []
        dependencies:
          a:
            common: []
          b:
            common: []
        """))

    with context:
        main(["--config", config_file, *extra_args])


GENERATED_COMMENT = (
    "# This list was generated by `rapids-dependency-file-generator`. To make changes, "
    "edit {config} and run `rapids-dependency-file-generator`."
)


def test_stale_pyproject_lists_are_removed(tmp_path):
    comment = GENERATED_COMMENT.format(config="dependencies.yaml")
    config_file = tmp_path / "dependencies.yaml"
    config_file.write_text(dedent("""\
        files:
          py_build:
            output: pyproject
            pyproject_dir: .
            extras:
              table: build-system
            includes: [build]
          py_run:
            output: pyproject
            pyproject_dir: .
            extras:
              table: project
            includes: [run]
        dependencies:
          build:
            common:
              - output_types: [pyproject]
                packages: [setuptools>=77.0.0]
          run:
            common:
              - output_types: [pyproject]
                packages: [numpy]
        """))
    # 'test' and 'tool.custom.requires' were generated by entries that have since
    # been removed from dependencies.yaml. 'docs' was written by hand.
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(dedent(f"""\
        [build-system]
        build-backend = "setuptools.build_meta"
        requires = [
            "setuptools",
        ] {comment}

        [project]
        name = "test"
        version = "0.0.0"
        dependencies = [
            "pandas",
        ] {comment}
        license = "Apache-2.0"

        [project.optional-dependencies]
        test = [
            "pytest",
        ] {comment}
        docs = [
            "sphinx",
        ]

        [tool.custom]
        requires = [
            "stale",
        ] {comment}

        [tool.other]
        setting = true
        """))

    main(["--config", str(config_file)])

    assert pyproject_file.read_text() == dedent(f"""\
        [build-system]
        build-backend = "setuptools.build_meta"
        requires = [
            "setuptools>=77.0.0",
        ] {comment}

        [project]
        name = "test"
        version = "0.0.0"
        dependencies = [
            "numpy",
        ] {comment}
        license = "Apache-2.0"

        [project.optional-dependencies]
        docs = [
            "sphinx",
        ]

        [tool.other]
        setting = true
        """)


def test_stale_pyproject_lists_are_removed_per_file(tmp_path):
    config_file = tmp_path / "dependencies.yaml"
    config_file.write_text(dedent("""\
        files:
          py_run:
            output: pyproject
            pyproject_dir: .
            extras:
              table: project
            includes: [run]
          py_test_nested:
            output: pyproject
            pyproject_dir: nested
            extras:
              table: project.optional-dependencies
              key: test
            includes: [run]
        dependencies:
          run:
            common:
              - output_types: [pyproject]
                packages: [numpy]
        """))
    root_pyproject = tmp_path / "pyproject.toml"
    root_pyproject.write_text(dedent(f"""\
        [project]
        name = "root"
        dependencies = [
            "numpy",
        ] {GENERATED_COMMENT.format(config="dependencies.yaml")}
        """))
    nested_comment = GENERATED_COMMENT.format(config="../dependencies.yaml")
    (tmp_path / "nested").mkdir()
    nested_pyproject = tmp_path / "nested" / "pyproject.toml"
    nested_pyproject.write_text(dedent(f"""\
        [project]
        name = "nested"
        dependencies = [
            "numpy",
        ] {nested_comment}

        [project.optional-dependencies]
        test = [
            "numpy",
        ] {nested_comment}
        """))

    main(["--config", str(config_file)])

    # The root file still generates 'project.dependencies', the nested file doesn't.
    assert "dependencies = [" in root_pyproject.read_text()
    assert nested_pyproject.read_text() == dedent(f"""\
        [project]
        name = "nested"

        [project.optional-dependencies]
        test = [
            "numpy",
        ] {nested_comment}
        """)


def test_stale_pyproject_lists_are_kept_when_writing_to_stdout(tmp_path):
    comment = GENERATED_COMMENT.format(config="dependencies.yaml")
    config_file = tmp_path / "dependencies.yaml"
    config_file.write_text(dedent("""\
        files:
          py_run:
            output: pyproject
            pyproject_dir: .
            extras:
              table: project
            includes: [run]
        dependencies:
          run:
            common:
              - output_types: [pyproject]
                packages: [numpy]
        """))
    pyproject_contents = dedent(f"""\
        [project]
        name = "test"
        dependencies = [
            "numpy",
        ] {comment}

        [project.optional-dependencies]
        test = [
            "pytest",
        ] {comment}
        """)
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject_contents)

    main(["--config", str(config_file), "--file-key", "py_run", "--output", "pyproject", "--matrix", ""])

    assert pyproject_file.read_text() == pyproject_contents
