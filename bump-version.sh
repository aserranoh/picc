#!/bin/bash

SCRIPTS="picc picc-objdump"
MODULES=lib/picc/*.py

if [ "$#" -ne 1 ]; then
    echo "usage: bump-version.sh VERSION"
else
    sed -i "s/__version__ = '[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*'/__version__ = '"$1"'/" $SCRIPTS $MODULES
    sed -i "s/version='[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*'/version='"$1"'/" setup.py
fi

