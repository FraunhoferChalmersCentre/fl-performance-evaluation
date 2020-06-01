"""
OODIDA Prototype

This is a prototype of telling the server to send weights to
the clients and back.

"""

import lib_user.oodida as o


def print_assignment(dataset = 'MNIST',
                    run_time = 0,
                    communication_rounds = 200,
                    step_size = 30):
    # initialization of config file
    ident       = 5
    name        = "FSVRG training"
    description = "FSVRG description here"
    type_        = "FSVRG"
    config      = o.newConfig(ident, name, description, type_)

    # set assignment
    assignment = dict()
    assignment['dataset'] = dataset
    assignment['step_size'] = step_size
    assignment['train_time'] = run_time
    assignment['communication_rounds'] = communication_rounds

    config['assignment_config'] = assignment

    # write JSON
    o.writeConfigToJSON(config)
    # Note: there is a check that a JSON file does not get written as long
    # as there is still an unprocessed JSON file in the destination
    # directory

    # print content of JSON file to screen
    o.printJSON()

    return config['timestamp']


if __name__ == '__main__':

    print_assignment()
