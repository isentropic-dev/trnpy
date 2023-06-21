class DuplicateLibraryError(Exception):
    """Raised when a library file has already been loaded."""


class SimulationError(Exception):
    """Raised when a simulation reports a fatal error."""


class UnitNotFoundError(Exception):
    """Raised when a unit is not present in a simulation."""


class InvalidUnitOutputError(Exception):
    """Raised when an output does not exist for a unit."""
