import pytest
from rapids_dependency_file_generator._rapids_dependency_file_validator import UnusedDependencySetWarning, validate_dependencies


def test_validate_dependencies_warn_on_unused_deps():
    with pytest.warns(UnusedDependencySetWarning) as warnings:
        validate_dependencies({
            "files": {
                "all": {
                    "output": "conda",
                    "includes": ["a", "b"],
                }
            },
            "channels": [],
            "dependencies": {
                "a": {
                    "common": [],
                },
                "b": {
                    "common": [],
                },
                "d": {
                    "common": [],
                },
                "c": {
                    "common": [],
                },
            },
        })

    assert len(warnings) == 2
    assert warnings[0].message.args[0] == 'Dependency set "c" is not referred to anywhere in "files:"'
    assert warnings[1].message.args[0] == 'Dependency set "d" is not referred to anywhere in "files:"'
