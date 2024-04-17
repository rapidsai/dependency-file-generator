"""Public API for rapids-dependency-file-generator.

This API can be used by Python build tools or other tools that want to
programmatically generate ``pyproject.toml``, ``requirements.txt``, or
a Conda environment from ``dependencies.yaml``.
"""

from . import _config, _rapids_dependency_file_generator
from ._config import *  # noqa: F401,F403
from ._rapids_dependency_file_generator import *  # noqa: F401,F403
from ._version import __version__

__all__ = [
    "__version__",
    *_config.__all__,
    *_rapids_dependency_file_generator.__all__,
]
