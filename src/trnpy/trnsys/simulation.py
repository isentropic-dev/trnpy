"""Code related to running TRNSYS simulations."""

from __future__ import annotations

from pathlib import Path
from typing import List, NamedTuple, Optional, Union

from ..exceptions import (
    TrnsysGetOutputValueError,
    TrnsysSetInputValueError,
    TrnsysStepForwardError,
)
from .lib import LoadedTrnsysLib, StoredValueInfo, TrnsysLib


class Simulation:
    """Represents a single TRNSYS simulation."""

    @classmethod
    def new(
        cls,
        trnsys_dir: Union[str, Path],
        input_file: Union[str, Path],
        user_type_libs: Optional[List[Union[str, Path]]] = None,
    ) -> Simulation:
        """Create a new TRNSYS simulation.

        The `trnsys_dir` must contain the compiled TRNSYS library (`trnsys.dll`
        for Windows, `libtrnsys.so` for Linux) as well as the other required
        libraries and resource files (`Units.lab`, `Descrips.dat`, etc.).

        Usage example:
            trnsys_dir = "path/to/trnsys/directory"
            input_file = "path/to/example.dck"
            sim = Simulation.new(trnsys_dir, input_file)
            done = False
            while not done:
                done = sim.step_forward()
                value = sim.get_output_value(unit=7, output_number=1)
                print(f"Current value for output 1 of unit 7 is {value}")

        Args:
            trnsys_dir: Path to the TRNSYS directory. Must exist.
            input_file: Path to the simulation's input (deck) file. Must exist.
            user_type_libs: Optional list of paths to user Type libs. All must exist.

        Raises:
            FileNotFoundError: If any provided path does not exist.
            DuplicateLibraryError: The lib in `trnsys_dir` is already in use.
            OSError: An error occurred loading the lib from `trnsys_dir`.
            TrnsysSetDirectoriesError
            TrnsysLoadInputFileError
        """
        trnsys_dir = Path(trnsys_dir).resolve(strict=True)
        input_file = Path(input_file).resolve(strict=True)
        type_libs = (
            []
            if user_type_libs is None
            else [Path(lib_file).resolve(strict=True) for lib_file in user_type_libs]
        )
        lib = LoadedTrnsysLib(trnsys_dir, input_file, type_libs)
        return cls(lib)

    def __init__(self, lib: TrnsysLib):
        """Initialize a Simulation object."""
        self.lib = lib

    def step_forward(self, steps: int = 1) -> bool:
        """Step the simulation forward.

        It is not possible to step a simulation beyond its final time.  Fewer
        steps than the requested number will be taken if `steps` is greater
        than the number of steps remaining in the simulation.

        Args:
            steps (int, optional): The number of steps to take.  Defaults to 1.

        Returns:
            - True if final time has been reached as a result of stepping forward.
            - False if more steps can be taken.

        Raises:
            ValueError: If `steps` is less than 1.
            TrnsysStepForwardError: If a simulation error occurs while stepping forward.
        """
        if steps < 1:
            raise ValueError("Number of steps cannot be less than 1.")

        (done, error_code) = self.lib.step_forward(steps)
        if error_code:
            raise TrnsysStepForwardError(error_code)

        return done

    def step_forward_with_values(self, steps: int = 1) -> StepForwardWithValuesReturn:
        """Step the simulation forward and return stored values.

        It is not possible to step a simulation beyond its final time.  Fewer
        steps than the requested number will be taken if `steps` is greater
        than the number of steps remaining in the simulation.

        Args:
            steps (int, optional): The number of steps to take.  Defaults to 1.

        Returns:
            StepForwardWithValuesReturn: A named tuple with the following fields:
                - values (List[float]): The stored values after stepping forward.
                - done (bool): True if the simulation has reached its final time.
        Raises:
            ValueError: If `steps` is less than 1.
            TrnsysStepForwardError: If a simulation error occurs while stepping forward.
        """
        if steps < 1:
            raise ValueError("Number of steps cannot be less than 1.")

        (values, done, error_code) = self.lib.step_forward_with_values(steps)
        if error_code:
            raise TrnsysStepForwardError(error_code)

        return StepForwardWithValuesReturn(values, done)

    def get_output_value(self, *, unit: int, output_number: int) -> float:
        """Return the current output value of a unit.

        Args:
            unit (int): The unit of interest.
            output_number (int): The output of interest.

        Returns:
            float: The current output value.

        Raises:
            TrnsysGetOutputValueError
        """
        (value, error_code) = self.lib.get_output_value(unit, output_number)
        if error_code:
            raise TrnsysGetOutputValueError(error_code)

        return value

    def set_input_value(self, *, unit: int, input_number: int, value: float) -> None:
        """Set an input value for a unit.

        Args:
            unit (int): The unit of interest.
            input_number (int): The input of interest.
            value (float): The input is set to this value.

        Raises:
            TrnsysSetInputValueError
        """
        error_code = self.lib.set_input_value(unit, input_number, value)
        if error_code:
            raise TrnsysSetInputValueError(error_code)

    @property
    def stored_values_info(self) -> List[StoredValueInfo]:
        """Information about the stored values in this simulation.

        The order of the returned list of `StoredValueInfo` named tuples
        corresponds to the order of stored values returned when calling
        `Simulation.step_forward_with_values`.
        """
        return self.lib.get_stored_values_info()

    @property
    def current_time(self) -> float:
        """The current time of the simulation."""
        return self.lib.get_current_time()

    @property
    def current_step(self) -> int:
        """The current step of the simulation."""
        return self.lib.get_current_step()

    @property
    def start_time(self) -> float:
        """The start time of the simulation."""
        return self.lib.get_start_time()

    @property
    def stop_time(self) -> float:
        """The stop time of the simulation."""
        return self.lib.get_stop_time()

    @property
    def time_step(self) -> float:
        """The time step of the simulation."""
        return self.lib.get_time_step()

    @property
    def total_steps(self) -> int:
        """The total number of time steps in the simulation."""
        return self.lib.get_total_steps()


class StepForwardWithValuesReturn(NamedTuple):
    """The return value of `Simulation.step_forward_with_values`.

    Attributes:
        values (List[float]): The stored values after stepping forward.
        done (bool): True if the simulation has reached its final time.
    """

    values: List[float]
    done: bool
