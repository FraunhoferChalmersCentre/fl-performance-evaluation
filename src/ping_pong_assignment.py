"""
OODIDA Prototype

This is a prototype of telling the server to request a pong response
from all available clients.

"""

import lib_user.oodida as o


# initialization of config file
ident       = 1
name        = "A simple ping pong test"
description = "The server pings all clients, who then sends a pong response."
mode        = "PingPong" # 'type' is a reserved keyword
config      = o.newConfig(ident, name, description, mode)


assign = dict()
config['assignment_config'] = assign

print(config)


# write JSON
o.writeConfigToJSON(config)
# Note: there is a check that a JSON file does not get written as long
# as there is still an unprocessed JSON file in the destination
# directory


# print content of JSON file to screen
o.printJSON()


# TODO: read results from directory 'state/user_in/'
# filename should be <id>.json


exit()
