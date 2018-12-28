#!/usr/bin/env python3
# Set up an interactive Python session for use with libsmite
# Usage: [i]python3 -i python-test.py

import sys
from ctypes import *
from ctypes.util import find_library

libsmite = CDLL(find_library("smite"))
