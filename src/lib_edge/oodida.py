"""
Python library "oodida" for generating an assignment specification as
JSON.

(c) 2017 Fraunhofer-Chalmers Research Centre for Industrial Mathematics

Authors:
Gregor Ulm (gregor.ulm@fcc.chalmers.se)
"""

import json
import time
import os.path


def JSONtoConfig(filename):

    with open(filename, 'r') as f:
        loaded = json.load(f)

    return loaded
