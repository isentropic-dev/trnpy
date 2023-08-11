"""Code related to the TRNSYS dynamic library."""

import ctypes as ct
import functools
from dataclasses import dataclass
from pathlib import Path
from typing import List, NamedTuple, Set

from ..exceptions import DuplicateLibraryError


@dataclass
class TrnsysDirectories:
    """Represents the directory paths required by TRNSYS."""

    root: Path
    exe: Path
    user_lib: Path

    @classmethod
    def from_single_path(cls, path: Path) -> "TrnsysDirectories":
        """Create a TrnsysDirectories instance from a single path.

        Args:
            path (Path): The path to use for all TRNSYS directories.
        """
        return cls(path, path, path)


class StepForwardReturn(NamedTuple):
    """The return value of `TrnsysLib.step_forward`.

    Attributes:
        done (bool): True if the simulation has reached its final time.
        error (int): Error code reported by TRNSYS, with 0 indicating a successful call.
    """

    done: bool
    error: int


class GetCurrentTimeReturn(NamedTuple):
    """The return value of `TrnsysLib.get_current_time`.

    Attributes:
        value (float): The current simulation time reported by TRNSYS.
        error (int): Error code reported by TRNSYS, with 0 indicating a successful call.
    """

    value: float
    error: int


class GetOutputValueReturn(NamedTuple):
    """The return value of `TrnsysLib.get_output_value`.

    Attributes:
        value (float): The output value reported by TRNSYS.
        error (int): Error code reported by TRNSYS, with 0 indicating a successful call.
    """

    value: float
    error: int


def _track_lib_path(lib_path: Path, tracked_paths: Set[Path]) -> None:
    """Track TRNSYS lib file paths.

    Raises:
        DuplicateLibraryError: If the file at `lib_path` is already in use.
    """
    if lib_path in tracked_paths:
        raise DuplicateLibraryError(f"The TRNSYS lib '{lib_path}' is already loaded")
    tracked_paths.add(lib_path)


track_lib_path = functools.partial(_track_lib_path, tracked_paths=set())


class TrnsysLib:
    """A class representing the TRNSYS library API.

    This abstract class serves as the base for a concrete implementation
    that is responsible for loading and wrapping a TRNSYS library file.
    """

    def set_directories(self, dirs: TrnsysDirectories) -> int:
        """Set the TRNSYS directories.

        Args:
            dirs (TrnsysDirectories): The TRNSYS paths to set.

        Returns:
            int: The error code reported by TRNSYS, with 0 indicating a successful call.
        """
        raise NotImplementedError

    def load_input_file(self, input_file: Path, type_lib_files: List[Path]) -> int:
        """Load an input file.

        Args:
            input_file (Path): The TRNSYS input (deck) file to load.
            type_lib_files (List[Path]): Type library files to load.

        Returns:
            int: The error code reported by TRNSYS, with 0 indicating a successful call.
        """
        raise NotImplementedError

    def step_forward(self, steps: int) -> StepForwardReturn:
        """Step the simulation forward.

        Args:
            steps (int): The number of steps to take.

        Returns:
            StepForwardReturn
        """
        raise NotImplementedError

    def get_current_time(self) -> GetCurrentTimeReturn:
        """Return the current time of the simulation.

        Returns:
            SimulationNotInitializedError
        """
        raise NotImplementedError

    def get_output_value(self, unit: int, output_number: int) -> GetOutputValueReturn:
        """Return the output value of a unit.

        Args:
            unit (int): The unit of interest.
            output_number (int): The output of interest.

        Returns:
            GetOutputValueReturn
        """
        raise NotImplementedError

    def set_input_value(self, unit: int, input_number: int, value: float) -> int:
        """Set an input value for a unit.

        Args:
            unit (int): The unit of interest.
            input_number (int): The input of interest.
            value (float): The input is set to this value.

        Returns:
            int: The error code reported by TRNSYS, with 0 indicating a successful call.
        """
        raise NotImplementedError


class LoadedTrnsysLib(TrnsysLib):
    """Represents a TRNSYS library loaded in memory."""

    def __init__(self, lib_path: Path):
        """Initialize a LoadedTrnsysLib object.

        Raises:
            DuplicateLibraryError: If the file at `lib_path` is already in use.
            OSError: If an error occurs when loading the library.
        """
        track_lib_path(lib_path)

        self.lib = ct.CDLL(str(lib_path), ct.RTLD_GLOBAL)
        self.lib_path = lib_path

        # Define the function signatures
        self.lib.apiSetDirectories.argtypes = [
            ct.c_char_p,  # root dir
            ct.c_char_p,  # exe dir
            ct.c_char_p,  # user lib dir
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self.lib.apiLoadInputFile.argtypes = [
            ct.c_char_p,  # input file
            ct.c_char_p,  # semicolon-separated list of type lib files
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self.lib.apiStepForward.restype = ct.c_bool
        self.lib.apiStepForward.argtypes = [
            ct.c_int,  # number of steps
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self.lib.apiGetCurrentTime.restype = ct.c_double
        self.lib.apiGetCurrentTime.argtypes = [
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self.lib.apiGetOutputValue.restype = ct.c_double
        self.lib.apiGetOutputValue.argtypes = [
            ct.c_int,  # unit number
            ct.c_int,  # output number
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self.lib.apiSetInputValue.argtypes = [
            ct.c_int,  # unit number
            ct.c_int,  # input number
            ct.c_double,  # value to set
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]

    def set_directories(self, dirs: TrnsysDirectories) -> int:
        """Set the TRNSYS directories in the library.

        Refer to the documentation of `TrnsysLib.set_directories` for more details.
        """
        error = ct.c_int(0)
        self.lib.apiSetDirectories(
            str(dirs.root).encode(),
            str(dirs.exe).encode(),
            str(dirs.user_lib).encode(),
            error,
        )
        return error.value

    def load_input_file(self, input_file: Path, type_lib_files: List[Path]) -> int:
        """Load an input file.

        Refer to the documentation of `TrnsysLib.load_input_file` for more details.
        """
        error = ct.c_int(0)
        self.lib.apiLoadInputFile(
            str(input_file).encode(),
            ";".join(str(x) for x in type_lib_files).encode(),
            error,
        )
        return error.value

    def step_forward(self, steps: int) -> StepForwardReturn:
        """Step the simulation forward.

        Refer to the documentation of `TrnsysLib.step_forward` for more details.
        """
        error = ct.c_int(0)
        done = self.lib.apiStepForward(steps, error)
        return StepForwardReturn(done, error.value)

    def get_current_time(self) -> GetCurrentTimeReturn:
        """Return the current time of the simulation.

        Refer to the documentation of `TrnsysLib.get_current_time` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetCurrentTime(error)
        return GetCurrentTimeReturn(value, error.value)

    def get_output_value(self, unit: int, output_number: int) -> GetOutputValueReturn:
        """Return the output value of a unit.

        Refer to the documentation of `TrnsysLib.get_output_value` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetOutputValue(unit, output_number, error)
        return GetOutputValueReturn(value, error.value)

    def set_input_value(self, unit: int, input_number: int, value: float) -> int:
        """Set an input value for a unit.

        Refer to the documentation of `TrnsysLib.set_input_value` for more details.
        """
        error = ct.c_int(0)
        self.lib.apiSetInputValue(unit, input_number, value, error)
        return error.value
