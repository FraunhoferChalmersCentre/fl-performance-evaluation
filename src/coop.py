"""
OODIDA Prototype

This is a prototype of telling the server to send weights to
the clients and back.

"""

import lib_user.oodida as o


def print_assignment(dataset = 'MNIST',
                    run_time = 60,
                    communication_rounds = 2,
                    report_frequency = 10,
                    lower_age_limit = 0,
                    upper_age_limit = 5,
                    learning_rate = 0.05,
                    lr_decay = 1e-5,
                    epochs = 5,
                    batch_size = 20):
    # initialization of config file
    ident       = 4
    name        = "CO-OP training"
    description = "Federated Learning with the CO-OP algorithm"
    type_        = "COOP"
    config      = o.newConfig(ident, name, description, type_)

    # client values
    init_clients = dict()
    init_clients['lr'] = learning_rate
    init_clients['decay'] = lr_decay
    init_clients['E'] = epochs
    init_clients['B'] = batch_size

    # set assignment
    assignment = dict()
    assignment['init_clients'] = init_clients
    assignment['train_time'] = run_time
    assignment['communication_rounds'] = communication_rounds
    assignment['report_frequency'] = report_frequency
    assignment['lower_age_limit'] = lower_age_limit
    assignment['upper_age_limit'] = upper_age_limit
    assignment['dataset'] = dataset

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