#! /bin/bash
set -euxo pipefail

mypy -p trnpy -p tests
black --target-version py311 --check .
isort --profile black --check --diff trnpy/ tests/
flake8 trnpy/ tests/
