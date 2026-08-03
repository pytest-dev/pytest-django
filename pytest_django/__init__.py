try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    # Broken installation, we don't even try.
    __version__ = "unknown"


from .fixtures import DjangoAssertNumQueries, DjangoCaptureOnCommitCallbacks, Settings
from .plugin import DjangoDbBlocker


__all__ = [
    "DjangoAssertNumQueries",
    "DjangoCaptureOnCommitCallbacks",
    "DjangoDbBlocker",
    "Settings",
    "__version__",
]
