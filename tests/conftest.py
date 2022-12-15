import pytest

from rapids_dependency_file_generator.rapids_dependency_file_validator import SCHEMA


@pytest.fixture(scope="session")
def schema():
    return SCHEMA
