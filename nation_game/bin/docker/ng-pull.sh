#!/bin/sh

REP="$(git rev-parse --show-toplevel)"

cd "$REP"
git fetch origin main
git merge
cd -
