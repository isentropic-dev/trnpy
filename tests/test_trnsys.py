import math
from pathlib import Path

import pytest

from trnpy.exceptions import (
    DuplicateLibraryError,
    TrnsysGetOutputValueError,
    TrnsysSetInputValueError,
    TrnsysStepForwardError,
)
from trnpy.trnsys.lib import (
    GetOutputValueReturn,
    StepForwardReturn,
    TrnsysDirectories,
    TrnsysLib,
    track_lib_path,
)
from trnpy.trnsys.simulation import Simulation


class MockTrnsysLib(TrnsysLib):
    def __init__(
        self,
        *,
        start_time: float = 0,
        final_time: float = 10,
        time_step: float = 1,
        current_time: float = 0,
        units: dict = {},
    ):
        """Create a new mocked TRNSYS library.

        Args:
            start_time (float, optional): The simulation start time.  Defaults to 0.
            final_time (float, optional): The simulation final time.  Defaults to 10.
            time_step (float, optional): The simulation time step.  Defaults to 1.
            current_time (float, optional): The current simulation time.  Defaults to 0.
            units (dict, optional): The assumed state of any units in the
                simualation, keyed by unit number.  Each unit is represented as
                a dict with any of the following keys, each of which map to a
                list of floats for that item:
                    - "parameters" (list of floats): Current parameter values.
                    - "inputs" (list of floats): Current input values.
                    - "outputs" (list of floats): Current output values.
                    - "derivatives" (list of floats): Current derivative values.
        """
        self._start_time = start_time
        self._final_time = final_time
        self._time_step = time_step
        self._current_time = current_time
        self._units = units

    def _is_at_final_time(self):
        """Check if simulation is at final time.

        Because of possible accumulating floating point error, we should not
        directly compare `self.current_time` to `self.final_time`.  Instead, we
        check if the current time is within half a time step of the final time.
        """
        return abs(self._final_time - self._current_time) < 0.5 * self._time_step

    def set_directories(self, dirs: TrnsysDirectories) -> int:
        return 0

    def load_input_file(self, input_file: Path) -> int:
        return 0

    def step_forward(self, steps: int) -> StepForwardReturn:
        if self._is_at_final_time():
            return StepForwardReturn(False, 1)
        return StepForwardReturn(True, 0)

    def get_output_value(self, unit: int, output_number: int) -> GetOutputValueReturn:
        if unit not in self._units:
            return GetOutputValueReturn(math.nan, 1)
        unit_outputs = self._units[unit].get("outputs", [])
        index = output_number - 1
        if index >= len(unit_outputs):
            return GetOutputValueReturn(math.nan, 2)
        value = unit_outputs[index]
        return GetOutputValueReturn(value, 0)

    def set_input_value(self, unit: int, input_number: int, value: float) -> int:
        if unit not in self._units:
            return 1
        unit_inputs = self._units[unit].get("inputs", [])
        index = input_number - 1
        if index >= len(unit_inputs):
            return 2
        unit_inputs[index] = value
        return 0


def new_sim(*, lib_state: dict = {}):
    """Create a new simulation with a mocked TrnsysLib.

    Args:
        lib_state (dict, optional): If provided, passed directly to `MockTrnsysLib`.
    """
    return Simulation(
        MockTrnsysLib(**lib_state),
        TrnsysDirectories("", "", ""),
        Path(""),
    )


def test_track_lib_path_raises_duplicate_error_on_same_path():
    track_lib_path(Path("a_lib_file"))
    track_lib_path(Path("another_lib_file"))  # different file path, so ok
    with pytest.raises(DuplicateLibraryError):
        track_lib_path(Path("a_lib_file"))


def test_stepping_after_final_time_raises_step_forward_error():
    sim = new_sim()
    sim.step_forward(1)  # not at end of simulation, so ok

    sim = new_sim(lib_state={"current_time": 168, "final_time": 168})
    with pytest.raises(TrnsysStepForwardError):
        sim.step_forward(1)


def test_getting_output_values():
    # Unit not present in simulation
    sim = new_sim()
    with pytest.raises(TrnsysGetOutputValueError) as err:
        sim.get_output_value(unit=23, output_number=5)
    assert err.value.error_code == 1

    # Unit now present but output number not available
    sim = new_sim(lib_state={"units": {23: {"outputs": [1, 2]}}})
    with pytest.raises(TrnsysGetOutputValueError) as err:
        sim.get_output_value(unit=23, output_number=3)
    assert err.value.error_code == 2

    # Unit and output number now available
    sim = new_sim(lib_state={"units": {23: {"outputs": [1, 2, 3, 4, 5]}}})
    value = sim.get_output_value(unit=23, output_number=5)
    assert value == 5


def test_setting_input_values():
    # Unit not present in simulation
    sim = new_sim()
    with pytest.raises(TrnsysSetInputValueError) as err:
        sim.set_input_value(unit=92, input_number=2, value=42)
    assert err.value.error_code == 1

    # Unit now present but input number not available
    sim = new_sim(lib_state={"units": {23: {"inputs": [1, 2]}}})
    with pytest.raises(TrnsysSetInputValueError) as err:
        sim.set_input_value(unit=23, input_number=3, value=42)
    assert err.value.error_code == 2

    # Unit and input number now available
    sim = new_sim(lib_state={"units": {23: {"inputs": [1, 2, 3]}}})
