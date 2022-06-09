#!/bin/sh

REP="$(git rev-parse --show-toplevel)"

cd "$REP"
git fetch origin master
git merge
cd -
