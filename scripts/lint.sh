#! /bin/bash
set -euxo pipefail

black --target-version py37 --check .
isort --profile black --check --diff trnpy/ tests/
