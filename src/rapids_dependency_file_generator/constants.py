from enum import Enum


class OutputTypes(Enum):
    CONDA = "conda"
    REQUIREMENTS = "requirements"
    NONE = "none"

    def __str__(self):
        return self.value


cli_name = "rapids-dependency-file-generator"

default_channels = [
    "rapidsai",
    "rapidsai-nightly",
    "dask/label/dev",
    "conda-forge",
    "nvidia",
]

default_conda_dir = "conda/environments"
default_requirements_dir = "python"
default_dependency_file_path = "dependencies.yaml"
