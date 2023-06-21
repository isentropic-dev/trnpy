"""Code related to running TRNSYS simulations."""

import os
import ctypes as ct
from pathlib import Path

from .exceptions import (
    DuplicateLibraryError,
    SimulationError,
    UnitNotFoundError,
    InvalidUnitOutputError,
)

# Only one `Simulation` instance can be created for each TRNSYS library file,
# so we need to keep track of which files have been loaded.
_loaded_trnsys_libs = set()


class TrnsysLib:
    """Represents a TRNSYS dynamic library loaded in memory."""


class Simulation:
    """Represents a single TRNSYS simulation."""

    def __init__(self, trnsys_lib: str | os.PathLike, input_file: str | os.PathLike):
        """Initialize a TRNSYS simulation.

        The directory containing the compiled TRNSYS library (`trnsys.dll`
        for Windows, `libtrnsys.so` for Linux) must also contain the required
        TRNSYS resource files (`Units.lab`, `Descrips.dat`, etc.).

        Usage example:
            sim = trnsys.Simulation("path/to/trnsys.dll", "path/to/example.dck")
            done = False
            while not done:
                done = sim.stepForward()
                value = sim.getOutputValue(7, 1)
                print(f"Current value for output 1 of unit 7 is {value}")

        Args:
            trnsys_lib: Path to the compiled TRNSYS library.
            input_file: Path to the simulation's input (deck) file.

        Raises:
            DuplicateLibraryError: The `trnsys_lib` file is already in use.
            OSError: An error occurred loading `trnsys_lib`.
            FileNotFoundError: The provided input file does not exist.
            RuntimeError: An unexpected error occurred.
        """
        self.trnsys_lib = Path(trnsys_lib)
        self.input_file = Path(input_file)

        if self.trnsys_lib in _loaded_trnsys_libs:
            raise DuplicateLibraryError

        if not self.input_file.is_file():
            raise FileNotFoundError

        # Load the TRNSYS library
        self._lib = ct.CDLL(trnsys_lib, ct.RTLD_GLOBAL)
        _loaded_trnsys_libs.add(self.trnsys_lib)

        # Define argument types for library functions
        self._lib.apiSetDirectories.argtypes = [
            ct.c_char_p,  # root dir
            ct.c_char_p,  # exe dir
            ct.c_char_p,  # user lib dir
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self._lib.apiLoadInputFile.argtypes = [
            ct.c_char_p,  # input file
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self._lib.apiStepForward.argtypes = [
            ct.c_int,  # number of steps
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self._lib.apiStepForward.restype = ct.c_bool
        self._lib.apiGetOutputValue.argtypes = [
            ct.c_int,  # unit number
            ct.c_int,  # output number
            ct.POINTER(ct.c_int),  # error code (by reference)
        ]
        self._lib.apiGetOutputValue.restype = ct.c_double

        # Initialize TRNSYS
        root_dir = str(self.trnsys_lib.parent).encode()
        exe_dir = root_dir
        user_lib_dir = root_dir
        error = ct.c_int(0)
        self._lib.apiSetDirectories(root_dir, exe_dir, user_lib_dir, error)
        if error.value != 0:
            raise RuntimeError  # TODO: report a more specific error?

        # Load the input file
        self._lib.apiLoadInputFile(str(self.input_file).encode(), error)
        if error.value != 0:
            raise RuntimeError  # TODO: report a more specific error?

    def stepForward(self, steps: int = 1) -> bool:
        """Step the simulation forward.

        It is not possible to step a simulation beyond its final time.  Fewer
        steps than the requested number will be taken if `steps` is greater
        than the number of steps remaining in the simulation.

        Args:
            steps (int, optional): The number of steps to take.  Defaults to 1.

        Returns:
            `True` if final time has been reached as a result of stepping forward.
            `False` if more steps can be taken.

        Raises:
            ValueError: If `steps` is less than `1`.
            RuntimeError: If called after simulation has reached its final time.
            SimulationError: If TRNSYS reported a fatal error during a step.
        """
        if steps < 1:
            raise ValueError
        error = ct.c_int(0)
        done = self._lib.apiStepForward(steps, error)
        if error.value == 1:
            raise RuntimeError
        if error.value == 99:
            raise SimulationError
        return done

    def getOutputValue(self, unit_number: int, output_number: int) -> float:
        """Return the output value of a unit.

        Args:
            unit_number: The unit of interest.
            output_number: The output of interest.

        Raises:
            UnitNotFoundError: If `unit_number` is not present in the simulation.
            ValueError: If `output_number` is not valid for the unit of interest.
        """
        error = ct.c_int(0)
        value = self._lib.apiGetOutputValue(unit_number, output_number, error)
        if error.value == 1:
            raise UnitNotFoundError
        if error.value == 2:
            raise InvalidUnitOutputError
        return value
