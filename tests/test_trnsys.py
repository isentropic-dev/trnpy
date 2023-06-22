import math
from pathlib import Path

import pytest


from trnpy.trnsys.simulation import Simulation
from trnpy.trnsys.lib import TrnsysLib, TrnsysDirectories, track_lib_path
from trnpy.exceptions import (
    DuplicateLibraryError,
    TrnsysStepForwardError,
    TrnsysGetOutputValueError,
    TrnsysSetInputValueError,
)


class MockTrnsysLib(TrnsysLib):
    def __init__(self):
        self.is_at_end = False
        self.units = set()  # tracks units we want to be present in the deck
        self.unit_inputs = {}  # keyed by str f"{unit}:{input_number}"
        self.unit_outputs = {}  # keyed by str f"{unit}:{output_number}"

    def set_directories(self, dirs: TrnsysDirectories) -> int:
        return 0

    def load_input_file(self, input_file: Path) -> int:
        return 0

    def step_forward(self, steps: int) -> (bool, int):
        if self.is_at_end:
            return (False, 1)
        return (True, 0)

    def get_output_value(self, unit: int, output_number: int) -> (float, int):
        if unit not in self.units:
            return (math.nan, 1)
        key = f"{unit}:{output_number}"
        value = self.unit_outputs.get(key)
        if value is None:
            return (math.nan, 2)  # output is not available for this unit
        return (value, 0)

    def set_input_value(self, unit: int, input_number: int, value: float) -> int:
        if unit not in self.units:
            return 1
        key = f"{unit}:{input_number}"
        if key not in self.unit_inputs:
            return 2  # treat this is though unit does not have this input number
        self.unit_inputs[key] = value

    def add_unit_to_deck(self, unit: int):
        """Make a unit be present in the deck."""
        self.units.add(unit)

    def set_unit_output_value(self, unit: int, output_number: int, value: float):
        """Make a unit's output value be available."""
        self.add_unit_to_deck(unit)
        key = f"{unit}:{output_number}"
        self.unit_outputs[key] = value

    def set_unit_input_value(self, unit: int, input_number: int, value: float):
        """Make a unit's input value be available."""
        self.add_unit_to_deck(unit)
        key = f"{unit}:{input_number}"
        self.unit_inputs[key] = value


def new_sim():
    """Create a new simulation with a mocked TrnsysLib."""
    return Simulation(
        MockTrnsysLib(),
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

    sim.lib.is_at_end = False
    sim.step_forward(1)  # not at end of simulation, so ok

    sim.lib.is_at_end = True
    with pytest.raises(TrnsysStepForwardError):
        sim.step_forward(1)


def test_getting_output_values():
    sim = new_sim()

    # Unit not present in simulation
    with pytest.raises(TrnsysGetOutputValueError) as err:
        sim.get_output_value(unit=23, output_number=5)
    assert err.value.error_code == 1

    # Unit now present but output number not available
    sim.lib.set_unit_output_value(23, 1, 42)
    with pytest.raises(TrnsysGetOutputValueError) as err:
        sim.get_output_value(unit=23, output_number=5)
    assert err.value.error_code == 2

    # Unit and output number now available
    sim.lib.set_unit_output_value(23, 5, 10)
    sim.get_output_value(unit=23, output_number=5)


def test_setting_input_values():
    sim = new_sim()

    # Unit not present in simulation
    with pytest.raises(TrnsysSetInputValueError) as err:
        sim.set_input_value(unit=92, input_number=10, value=42)
    assert err.value.error_code == 1

    # Unit now present but input number not available
    sim.lib.set_unit_input_value(92, 1, 42)
    with pytest.raises(TrnsysSetInputValueError) as err:
        sim.set_input_value(unit=92, input_number=10, value=42)
    assert err.value.error_code == 2

    # Unit and input number now available
    sim.lib.set_unit_input_value(92, 10, 0)
    sim.set_input_value(unit=92, input_number=10, value=42)
