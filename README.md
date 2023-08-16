# trnpy

[![Build Status][test-badge]][main-test-workflow]

## Development

When developing **trnpy**, it is recommended to set up a virtual environment.
This ensures a clean and isolated environment for your development work.
Here are the steps to initialize a virtual environment and install the requirements using `pip`:

### Prerequisites
- Python 3.7 or above
- `pip` package manager

### Setting up a Virtual Environment
1. Open a terminal or command prompt and navigate to the project directory.
2. Create a new virtual environment by running the following command:

```
python3 -m venv env --prompt trnpy
```

This will create a new directory named `env` that contains the necessary files for the virtual environment.

3. Activate the virtual environment:

- On macOS and Linux:
  ```
  source env/bin/activate
  ```
- On Windows:
  ```
  env\Scripts\Activate.ps1
  ```

You should see `(trnpy)` at the beginning of your command prompt, indicating that the virtual environment is active.

### Installing Requirements

4. With the virtual environment activated, you can now install the project requirements:

```
pip install -e ".[lint,test,typing]"
```

This will install all the required packages specified in the `requirements.txt` file into your virtual environment.

[test-badge]: https://github.com/isentropic-dev/trnpy/actions/workflows/test.yml/badge.svg
[main-test-workflow]: https://github.com/isentropic-dev/trnpy/actions/workflows/test.yml?query=branch%3Amain+
