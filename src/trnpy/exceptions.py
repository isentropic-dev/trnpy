from typing import Optional


class UnsupportedOperatingSystem(Exception):
    """Raised if this operating system is not supported."""

    def __init__(self, system: str):
        super().__init__(f"The {system} operating system is not supported by TRNSYS.")


class DuplicateLibraryError(Exception):
    """Raised when a library file has already been loaded."""


class SimulationError(Exception):
    """Raised when a simulation reports a fatal error."""


class TrnsysError(Exception):
    """Represents an error raised by TRNSYS."""

    def __init__(self, error_code: int, message: Optional[str] = None):
        super().__init__(
            message if message else f"An unknown TRNSYS error ({error_code}) occurred."
        )
        self.error_code = error_code


class TrnsysInitializeSimulationError(TrnsysError):
    def __init__(self, error_code: int):
        messages = {
            1: "provided config is not valid",
            2: "a specified file or directory does not exist",
            3: "standard Types library was not found",
            4: "simulation has already been initialized",
            5: "list file cannot be opened for writing",
            6: "input file cannot be opened for reading",
            7: "a required Type was not found",
            8: "an invalid stored value was specified in the input file",
            100: "license is expired",
        }
        super().__init__(error_code, messages.get(error_code))


class TrnsysStepForwardError(TrnsysError):
    def __init__(self, error_code: int):
        messages = {
            1: "simulation has reached its final time",
        }
        super().__init__(error_code, messages.get(error_code))


class TrnsysGetOutputValueError(TrnsysError):
    def __init__(self, error_code: int):
        messages = {
            1: "unit is not present in the deck",
            2: "output number is not valid for this unit",
        }
        super().__init__(error_code, messages.get(error_code))


class TrnsysSetInputValueError(TrnsysError):
    def __init__(self, error_code: int):
        messages = {
            1: "unit is not present in the deck",
            2: "input number is not valid for this unit",
        }
        super().__init__(error_code, messages.get(error_code))
