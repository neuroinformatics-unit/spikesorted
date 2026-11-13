from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("spikesorted")
except PackageNotFoundError:
    # package is not installed
    pass

from spikesorted.pipeline.pipeline import Pipeline

__all__ = ["Pipeline"]
