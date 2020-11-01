#!/bin/sh
set -eux

# first arg starts with "/" and refers to an executable, then run it.
if [ "${1#/}" != "$1" -a -x "$1" ]; then
    exec "$@"
else
    exec /runci $@
fi

