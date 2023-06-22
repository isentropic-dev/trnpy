from pathlib import Path

import pytest


from trnpy.trnsys.simulation import Simulation
from trnpy.trnsys.lib import TrnsysLib, TrnsysDirectories, track_lib_path
from trnpy.exceptions import DuplicateLibraryError, TrnsysStepForwardError


class MockTrnsysLib(TrnsysLib):
    def __init__(self):
        self.is_at_end = False

    def set_directories(self, dirs: TrnsysDirectories) -> int:
        return 0

    def load_input_file(self, input_file: Path) -> int:
        return 0

    def step_forward(self, steps: int) -> (bool, int):
        if self.is_at_end:
            return (False, 1)
        return (True, 0)


def test_track_lib_path_raises_duplicate_error_on_same_path():
    track_lib_path(Path("a_lib_file"))
    track_lib_path(Path("another_lib_file"))  # different file path, so ok
    with pytest.raises(DuplicateLibraryError):
        track_lib_path(Path("a_lib_file"))


def test_stepping_after_final_time_raises_step_forward_error():
    sim = Simulation(
        MockTrnsysLib(),
        TrnsysDirectories("", "", ""),
        Path(""),
    )

    sim.lib.is_at_end = False
    sim.step_forward(1)  # not at end of simulation, so ok

    sim.lib.is_at_end = True
    with pytest.raises(TrnsysStepForwardError):
        sim.step_forward(1)
