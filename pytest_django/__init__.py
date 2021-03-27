try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    # Broken installation, we don't even try.
    __version__ = "unknown"


__all__ = (
    "__version__",
)
