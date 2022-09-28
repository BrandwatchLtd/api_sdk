"""Top-level package for bwapi."""
from warnings import warn

__version__ = "4.1.0"

warn(
    "The bwapi package is deprecated. Please use 'bcr-api' instead: "
    "https://github.com/BrandwatchLtd/bcr-api",
    DeprecationWarning,
    stacklevel=2,
)
