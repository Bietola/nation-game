#!/bin/sh

cat "$(realpath "$0" | xargs dirname | xargs dirname)"/assets/world.json | jq