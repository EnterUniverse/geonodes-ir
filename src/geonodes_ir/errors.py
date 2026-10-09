class GeoNodesIRError(Exception):
    """Base exception for GeoNodes IR."""


class ValidationError(GeoNodesIRError, ValueError):
    """Raised when a graph violates an IR invariant."""


class CompilationError(GeoNodesIRError, RuntimeError):
    """Raised when a valid IR graph cannot be compiled by a backend."""
