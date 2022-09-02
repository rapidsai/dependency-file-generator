from enum import Enum


class GeneratorTypes(Enum):
    CONDA = "conda"
    REQUIREMENTS = "requirements"
    NONE = "none"

    def __str__(self):
        return self.value


conda_and_requirements_key = f"{GeneratorTypes.CONDA}_and_{GeneratorTypes.REQUIREMENTS}"

cli_name = "rapids-dependency-file-generator"

default_channels = [
    "rapidsai",
    "nvidia",
    "rapidsai-nightly",
    "dask/label/dev",
    "conda-forge",
]

default_conda_dir = "conda/environments"
default_requirements_dir = "python"
default_dependency_file_path = "dependencies.yaml"
