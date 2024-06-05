#!/usr/bin/env bash
set -euxo pipefail

poetry run ruff check .
poetry run ruff format --diff .
poetry run mypy .
poetry run pytest -vv

rm -rf dist
poetry build -vvv
