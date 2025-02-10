try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    # Broken installation, we don't even try.
    __version__ = "unknown"


from .fixtures import DjangoAssertNumQueries, DjangoAssertNumAllConnectionsQueries, DjangoCaptureOnCommitCallbacks
from .plugin import DjangoDbBlocker


__all__ = [
    "DjangoAssertNumQueries",
    "DjangoAssertNumAllConnectionsQueries",
    "DjangoCaptureOnCommitCallbacks",
    "DjangoDbBlocker",
    "__version__",
]
