#!/bin/sh

REP="$(git rev-parse --show-toplevel)"

cd "$REP/nation_game"
# poetry install
poetry run python main.py
cd -
