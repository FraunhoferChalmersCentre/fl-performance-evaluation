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


def newConfig(ident, name, description, mode):

    config = dict()

    config['id']                = ident
    config['name']              = name
    config['description']       = description
    config['timestamp']         = int(time.time()) * 1000
                                  # time in ms since Unix epoch
    config['type']              = mode
    config['assignment_config'] = None

    return config


def writeConfigToJSON(config):
    filename = 'state/user_out/assignment.json'

    # does file name exist?
    while os.path.exists(filename):
        print("Unprocessed file remaining. Waiting...")
        time.sleep(10)

    # file does not exist:
    with open(filename, 'w') as fp:
        json.dump(config, fp)

    print("File ", filename, " written.")


def printJSON():
    filename = 'state/user_out/assignment.json'
    with open(filename, 'r') as f:
        parsed = json.load(f)
        print(json.dumps(parsed, indent=4, sort_keys=True))


def JSONtoConfig():
    filename = 'state/user_out/assignment.json'
    with open(filename, 'r') as f:
        loaded = json.load(f)

    return loaded
