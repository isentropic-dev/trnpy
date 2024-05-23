"""Code related to the TRNSYS dynamic library."""

import ctypes as ct
import functools
import json
import platform
from pathlib import Path
from typing import List, NamedTuple, Optional, Set

from ..exceptions import (
    DuplicateLibraryError,
    TrnsysLoadInputFileError,
    TrnsysSetDirectoriesError,
    UnsupportedOperatingSystem,
)


class StepForwardReturn(NamedTuple):
    """The return value of `TrnsysLib.step_forward`.

    Attributes:
        done (bool): True if the simulation has reached its final time.
        error (int): Error code reported by TRNSYS, with 0 indicating a successful call.
    """

    done: bool
    error: int


class StepForwardWithValuesReturn(NamedTuple):
    """The return value of `TrnsysLib.step_forward_with_values`.

    Attributes:
        values (List[float]): The stored values after stepping forward.
        done (bool): True if the simulation has reached its final time.
        error (int): Error code reported by TRNSYS, with 0 indicating a successful call.
    """

    values: List[float]
    done: bool
    error: int


class GetFloatReturn(NamedTuple):
    """The return value of a `TrnsysLib` function that returns a `float`.

    Attributes:
        value (float): The value returned by TRNSYS.
        error (int): Error code reported by TRNSYS, with 0 indicating a successful call.
    """

    value: float
    error: int


class GetIntReturn(NamedTuple):
    """The return value of a `TrnsysLib` function that returns an `int`.

    Attributes:
        value (int): The value returned by TRNSYS.
        error (int): Error code reported by TRNSYS, with 0 indicating a successful call.
    """

    value: int
    error: int


class StoredValueInfo(NamedTuple):
    """Information about a stored value.

    Attributes:
        id (str): The unique identifier for this stored value.
        label (str): The label associated with this stored value.
    """

    id: str
    label: str


class TrnsysLib:
    """A class representing the TRNSYS library API.

    This abstract class serves as the base for a concrete implementation
    that is responsible for loading and wrapping a TRNSYS library file.
    """

    def get_stored_values_info(self) -> List[StoredValueInfo]:
        """Return information about the stored values in this simulation.

        Returns:
            List[StoredValueInfo]
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

    def step_forward_with_values(self, steps: int) -> StepForwardWithValuesReturn:
        """Step the simulation forward and return stored values.

        Args:
            steps (int): The number of steps to take.

        Returns:
            StepForwardWithValuesReturn
        """
        raise NotImplementedError

    def get_current_time(self) -> GetFloatReturn:
        """Return the current time of the simulation.

        Returns:
            GetFloatReturn
        """
        raise NotImplementedError

    def get_start_time(self) -> GetFloatReturn:
        """Return the start time of the simulation.

        Returns:
            GetFloatReturn
        """
        raise NotImplementedError

    def get_stop_time(self) -> GetFloatReturn:
        """Return the stop time of the simulation.

        Returns:
            GetFloatReturn
        """
        raise NotImplementedError

    def get_time_step(self) -> GetFloatReturn:
        """Return the time step of the simulation.

        Returns:
            GetFloatReturn
        """
        raise NotImplementedError

    def get_output_value(self, unit: int, output_number: int) -> GetFloatReturn:
        """Return the output value of a unit.

        Args:
            unit (int): The unit of interest.
            output_number (int): The output of interest.

        Returns:
            GetFloatReturn
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
    """Represents a loaded TRNSYS library ready to run a simulation."""

    def __init__(
        self,
        trnsys_dir: Path,
        input_file: Path,
        user_type_libs: Optional[List[Path]] = None,
    ):
        """Initialize a LoadedTrnsysLib object.

        Raises:
            UnsupportedOperatingSystem: If the OS is supported by TRNSYS.
            DuplicateLibraryError: If the libs in `trnsys_dir` are already in use.
            OSError: If an error occurs when loading the library.
        """
        lib = _load_api_lib(trnsys_dir)

        error = ct.c_int(0)
        lib.apiSetDirectories(
            str(trnsys_dir).encode(),
            str(trnsys_dir).encode(),
            str(trnsys_dir).encode(),
            error,
        )
        if error.value:
            raise TrnsysSetDirectoriesError(error.value)

        standard_types_lib = trnsys_dir / _lib_filename("types")
        type_libs = [] if user_type_libs is None else user_type_libs
        type_libs.append(standard_types_lib)

        lib.apiLoadInputFile(
            str(input_file).encode(),
            ";".join(str(x) for x in type_libs).encode(),
            error,
        )
        if error.value:
            raise TrnsysLoadInputFileError(error.value)

        stored_values_count = lib.apiGetStoredValuesCount()
        self.stored_values_buffer = (ct.c_double * stored_values_count)()
        self.lib = lib

    def get_stored_values_info(self) -> List[StoredValueInfo]:
        """Return information about the stored values in this simulation.

        Refer to the documentation of `TrnsysLib.get_stored_values_info` for
        more details.
        """
        stored_values_info_ptr = self.lib.apiGetStoredValuesInfo()
        json_string = ct.cast(stored_values_info_ptr, ct.c_char_p).value
        if json_string is None:
            return []

        stored_values_info: List[StoredValueInfo] = json.loads(
            json_string.decode("utf-8")
        )
        return stored_values_info

    def step_forward(self, steps: int) -> StepForwardReturn:
        """Step the simulation forward.

        Refer to the documentation of `TrnsysLib.step_forward` for more details.
        """
        error = ct.c_int(0)
        done = self.lib.apiStepForward(steps, error)
        return StepForwardReturn(done, error.value)

    def step_forward_with_values(self, steps: int) -> StepForwardWithValuesReturn:
        """Step the simulation forward and return stored values.

        Refer to the documentation of `TrnsysLib.step_forward_with_values` for
        more details.
        """
        error = ct.c_int(0)
        done = self.lib.apiStepForwardWithValues(
            steps, self.stored_values_buffer, error
        )
        values = list(self.stored_values_buffer)
        return StepForwardWithValuesReturn(values, done, error.value)

    def get_current_time(self) -> GetFloatReturn:
        """Return the current time of the simulation.

        Refer to the documentation of `TrnsysLib.get_current_time` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetCurrentTime(error)
        return GetFloatReturn(value, error.value)

    def get_start_time(self) -> GetFloatReturn:
        """Return the start time of the simulation.

        Refer to the documentation of `TrnsysLib.get_start_time` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetStartTime(error)
        return GetFloatReturn(value, error.value)

    def get_stop_time(self) -> GetFloatReturn:
        """Return the stop time of the simulation.

        Refer to the documentation of `TrnsysLib.get_stop_time` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetStopTime(error)
        return GetFloatReturn(value, error.value)

    def get_time_step(self) -> GetFloatReturn:
        """Return the time step of the simulation.

        Refer to the documentation of `TrnsysLib.get_time_step` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetTimeStep(error)
        return GetFloatReturn(value, error.value)

    def get_output_value(self, unit: int, output_number: int) -> GetFloatReturn:
        """Return the output value of a unit.

        Refer to the documentation of `TrnsysLib.get_output_value` for more details.
        """
        error = ct.c_int(0)
        value = self.lib.apiGetOutputValue(unit, output_number, error)
        return GetFloatReturn(value, error.value)

    def set_input_value(self, unit: int, input_number: int, value: float) -> int:
        """Set an input value for a unit.

        Refer to the documentation of `TrnsysLib.set_input_value` for more details.
        """
        error = ct.c_int(0)
        self.lib.apiSetInputValue(unit, input_number, value, error)
        return error.value


def _load_api_lib(trnsys_dir: Path) -> ct.CDLL:
    """Load the TRNSYS API library.

    Raises:
        UnsupportedOperatingSystem: If this OS is not supported by TRNSYS.
        DuplicateLibraryError: If the libs in `trnsys_dir` are already in use.
        OSError: If an error occurs when loading the dynamic library.
    """
    api_lib = _lib_filename("api")
    lib_path = trnsys_dir / api_lib
    track_lib_path(lib_path)

    lib = ct.CDLL(str(lib_path), ct.RTLD_GLOBAL)

    # Define the function signatures
    lib.apiSetDirectories.argtypes = [
        ct.c_char_p,  # root dir
        ct.c_char_p,  # exe dir
        ct.c_char_p,  # user lib dir
        ct.POINTER(ct.c_int),  # error code (by reference)
    ]

    lib.apiLoadInputFile.argtypes = [
        ct.c_char_p,  # input file
        ct.c_char_p,  # semicolon-separated list of type lib files
        ct.POINTER(ct.c_int),  # error code (by reference)
    ]

    lib.apiGetStoredValuesCount.restype = ct.c_int
    lib.apiGetStoredValuesInfo.restype = ct.c_char_p

    lib.apiStepForward.restype = ct.c_bool
    lib.apiStepForward.argtypes = [
        ct.c_int,  # number of steps
        ct.POINTER(ct.c_int),  # error code (by reference)
    ]

    lib.apiStepForwardWithValues.restype = ct.c_bool
    lib.apiStepForwardWithValues.argtypes = [
        ct.c_int,  # number of steps
        ct.POINTER(ct.c_double),  # start of stored values array
        ct.POINTER(ct.c_int),  # error code (by reference)
    ]

    lib.apiGetOutputValue.restype = ct.c_double
    lib.apiGetOutputValue.argtypes = [
        ct.c_int,  # unit number
        ct.c_int,  # output number
        ct.POINTER(ct.c_int),  # error code (by reference)
    ]

    lib.apiSetInputValue.argtypes = [
        ct.c_int,  # unit number
        ct.c_int,  # input number
        ct.c_double,  # value to set
        ct.POINTER(ct.c_int),  # error code (by reference)
    ]

    lib.apiGetCurrentTime.restype = ct.c_double
    lib.apiGetCurrentTime.argtypes = [ct.POINTER(ct.c_int)]

    lib.apiGetStartTime.restype = ct.c_double
    lib.apiGetStartTime.argtypes = [ct.POINTER(ct.c_int)]

    lib.apiGetStopTime.restype = ct.c_double
    lib.apiGetStopTime.argtypes = [ct.POINTER(ct.c_int)]

    lib.apiGetTimeStep.restype = ct.c_double
    lib.apiGetTimeStep.argtypes = [ct.POINTER(ct.c_int)]

    return lib


def _lib_filename(name: str) -> str:
    """Return the system-specific filename for a dynamic library.

    Args:
        name(str): The name of the dynamic library.

    Raises:
        UnsupportedOperatingSystem: If this OS is not supported by TRNSYS.
    """
    filename = {
        "Windows": f"{name}.dll",
        "Darwin": f"lib{name}.dylib",
        "Linux": f"lib{name}.so",
    }.get(platform.system())
    if filename is None:
        raise UnsupportedOperatingSystem(platform.system())
    return filename


def _track_lib_path(lib_path: Path, tracked_paths: Set[Path]) -> None:
    """Track TRNSYS lib file paths.

    Raises:
        DuplicateLibraryError: If the file at `lib_path` is already in use.
    """
    if lib_path in tracked_paths:
        raise DuplicateLibraryError(f"The TRNSYS lib '{lib_path}' is already loaded")
    tracked_paths.add(lib_path)


track_lib_path = functools.partial(_track_lib_path, tracked_paths=set())
