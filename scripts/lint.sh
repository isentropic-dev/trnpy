#! /bin/bash
set -euxo pipefail

mypy -p src/trnpy -p tests
black --target-version py311 --check .
isort --profile black --check --diff src/trnpy/ tests/
flake8 src/trnpy/ tests/
