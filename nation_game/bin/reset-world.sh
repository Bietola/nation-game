#!/bin/sh

REP="$(git rev-parse --show-toplevel)"

cp "$REP/assets/world.json" "$REP/assets/bu/world.json"
cp "$REP/assets/templates/world-w-natives.json" "$REP/assets/world.json"
echo Done, backup in "$REP/assets/bu/world.json"
