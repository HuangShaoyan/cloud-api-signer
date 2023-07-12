#!/usr/bin/env bash
set -euxo pipefail

poetry run yapf -d -r .
poetry run pytest -vv
