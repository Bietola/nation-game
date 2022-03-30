#!/bin/sh

REP="$(git rev-parse --show-toplevel)"

pkill poetry
git add ./assets/game-data/**
git commit -m "Game update"
git push
