from enum import Enum


class OutputTypes(Enum):
    CONDA = "conda"
    CONDA_META = "conda_meta"
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
# TODO: Should we remove a default? This is going to need to be different for
# every package anyway.
default_conda_meta_dir = "conda/recipes/"
default_requirements_dir = "python"
default_dependency_file_path = "dependencies.yaml"
