#! /bin/bash
set -euxo pipefail

coverage run --parallel -m pytest
coverage combine
coverage report
