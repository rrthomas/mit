#!/bin/bash
# Build on Travis
# Written by the Mit authors 2020.
# This file is in the public domain.

set -e

if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then pip3 install pyyaml; fi

./bootstrap
if [[ "$TRAVIS_OS_NAME" != "osx" ]]; then CONFIGURE_ARGS=(PYTHON=/usr/bin/python3.8); fi
if [[ "$ASAN" == "yes" ]]; then
    # FIXME: ASAN doesn't work with thread-local storage
    CONFIGURE_ARGS+=(--enable-package-suffix --disable-tls CFLAGS="-g3 -fsanitize=address -fsanitize=undefined" LDFLAGS="-fsanitize=address -fsanitize=undefined" PY_LOG_ENV="LD_PRELOAD=/usr/lib/gcc/x86_64-linux-gnu/7/libasan.so PYTHONMALLOC=malloc")
fi
./configure --enable-silent-rules "${CONFIGURE_ARGS[@]}" && make

# Can't use libraries in-tree on macOS, so "make install", and don't "make
# distcheck".
if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then sudo make install; fi
( make check || ( cat tests/test-suite.log; false ) ) && if [[ "$TRAVIS_OS_NAME" != "osx" ]]; then make DISTCHECK_CONFIGURE_FLAGS=--enable-package-suffix distcheck; fi
