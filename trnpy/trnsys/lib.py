"""Code related to running TRNSYS simulations."""

import ctypes as ct
import functools
from dataclasses import dataclass
from pathlib import Path

from ..exceptions import DuplicateLibraryError


@dataclass
class TrnsysDirectories:
    """
    Represents the directory paths required by TRNSYS.
    """

    root: Path
    exe: Path
    user_lib: Path


def _track_lib_path(lib_path: Path, tracked_paths: set):
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
            int: The error code reported by TRNSYS.
                 A value of 0 indicates a successful call.
        """
        raise NotImplementedError

    def load_input_file(self, input_file: Path) -> int:
        """Load an input file.

        Args:
            input_file (Path): The TRNSYS input (deck) file to load.

        Returns:
            int: The error code reported by TRNSYS.
                 A value of 0 indicates a successful call.
        """
        raise NotImplementedError

    def step_forward(self, steps: int) -> (bool, int):
        """Step the simulation forward.

        Args:
            steps (int): The number of steps to take.

        Returns:
            tuple: A tuple containing the following values:
                - bool: Indicates whether the final time has been reached.
                    - True if the simulation is done.
                    - False if more steps can be taken.
                - int: The error code reported by TRNSYS.
                       A value of 0 indicates a successful call.
        """
        raise NotImplementedError

    def get_output_value(self, unit: int, output_number: int) -> (float, int):
        """Return the output value of a unit.

        Args:
            unit (int): The unit of interest.
            output_number (int): The output of interest.

        Returns:
            tuple: A tuple containing the following values:
                - float: The current output value.
                - int: The error code reported by TRNSYS.
                       A value of 0 indicates a successful call.
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

        self.lib = ct.CDLL(lib_path, ct.RTLD_GLOBAL)
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
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self.lib.apiStepForward.restype = ct.c_bool
        self.lib.apiStepForward.argtypes = [
            ct.c_int,  # number of steps
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self.lib.apiGetOutputValue.restype = ct.c_double
        self.lib.apiGetOutputValue.argtypes = [
            ct.c_int,  # unit number
            ct.c_int,  # output number
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

    def load_input_file(self, input_file: Path) -> int:
        """Load an input file.

        Refer to the documentation of `TrnsysLib.load_input_file` for more details.
        """
        error = ct.c_int(0)
        self.lib.apiLoadInputFile(str(input_file).encode(), error)
        return error.value

    def step_forward(self, steps: int) -> (bool, int):
        """Step the simulation forward.

        Refer to the documentation of `TrnsysLib.step_forward` for more details.
        """
        error = ct.c_int(0)
        done = self.lib.apiStepForward(steps, error)
        return (done, error.value)

    def get_output_value(self, unit: int, output_number: int) -> (float, int):
        """Return the output value of a unit.

        Refer to the documentation of `TrnsysLib.get_output_value` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetOutputValue(unit, output_number, error)
        return (value, error.value)