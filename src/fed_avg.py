"""
OODIDA Prototype

This is a prototype of telling the server to send weights to
the clients and back.

"""

import lib_user.oodida as o


def print_assignment(dataset = 'MNIST-non-iid',
                    chosen_client_proportion = 0.1,
                    variant = '1',
                    run_time = 0,
                    communication_rounds = 1000,
                    learning_rate = 0.088,
                    lr_decay = 3.2e-6,
                    epochs = 5,
                    batch_size = 20):
    # initialization of config file
    ident       = 2
    name        = "FedAvg training"
    description = "Federated Learning with the algorithm FedAvg on MNIST non-IID data."
    type_        = "FedAvg"
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
    assignment['dataset'] = dataset
    assignment['C'] = chosen_client_proportion
    assignment['variant'] = variant
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
