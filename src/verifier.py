import os
import json
import time
from keras.models import Sequential
from keras.layers import Dense
import keras
import lib.utils as ut
import lib.read_data as data
from numpy import ones
import glob
import re


def main():
    overwatch_file_names = 'state/cloud/verification_model_id*.json'
    mnist_model = ut.build_mnist_model()
    get_gradients = ut.compute_gradients(mnist_model) #Function to compute gradients
    MNIST_TEST_DATA = ut.LazyData(lambda: data.read_mnist_data('data/mnist/t10k-images.idx3-ubyte', 'data/mnist/t10k-labels.idx1-ubyte'))
    MNIST_TEST_DATA_CV = ut.LazyData(None)
    MNIST_TRAIN_DATA = ut.LazyData(data.read_mnist_car_data)

    print("Let's a go!")
    while True:
        for input_file in glob.glob(overwatch_file_names):
            try:
                with open(input_file, 'r') as f:
                    json_data = json.load(f)

                w_list = json_data['model']['w']
                b_list = json_data['model']['b']

                dataset = json_data['dataset']
                if dataset.startswith('MNIST_noniid_cv'):
                    match = re.search(r'(?<=_cv)\d+', dataset)
                    val_fold = int(match.group(0))

                    path = f'data/mnist_noniid_cv/fold{val_fold}/'
                    MNIST_TEST_DATA_CV = ut.LazyData(lambda: data.read_cars_data(path))
                    x_raw, y_raw = MNIST_TEST_DATA_CV.load()
                    x_test, y_test = ut.reshape_mnist(x_raw, y_raw)
                    model = mnist_model

                elif dataset.startswith('MNIST_iid_cv'):
                    match = re.search(r'(?<=_cv)\d+', dataset)
                    val_fold = int(match.group(0))

                    path = f'data/mnist_iid_cv/fold{val_fold}/'
                    MNIST_TEST_DATA_CV = ut.LazyData(lambda: data.read_cars_data(path))
                    x_raw, y_raw = MNIST_TEST_DATA_CV.load()
                    x_test, y_test = ut.reshape_mnist(x_raw, y_raw)
                    model = mnist_model

                elif dataset.startswith('MNIST'):
                    # Same test set independetly of the distibution
                    x_raw, y_raw = MNIST_TEST_DATA.load()
                    x_test, y_test = ut.reshape_mnist(x_raw, y_raw)
                    model = mnist_model

                # Update weights
                ut.update_parameters(model.layers, w_list, b_list)

                loss, metric = evaluation(model, x_test, y_test)

                score_json = dict()
                score_json['loss'] = loss
                score_json['metric'] = metric

                typ = json_data['type']
                if typ == 'fsvrg':
                    x_raw, y_raw = MNIST_TRAIN_DATA.load()
                    x_train, y_train = ut.reshape_mnist(x_raw, y_raw)
                    inputs = [x_train, # X
                              ones(len(x_train)), # sample weights
                              y_train, # y
                              0 # learning phase in TEST mode
                    ]

                    gradients = get_gradients(inputs)
                    gradients_w, gradients_b = ut.flatten_model(gradients)

                    score_json['gradients_w'] = gradients_w
                    score_json['gradients_b'] = gradients_b

                id_number = get_id_from_file_name(input_file)
                output_path = 'state/cloud/verification_score_id{}.json'.format(id_number)
                output_tmp_path = output_path + '_tmp_'
                with open(output_tmp_path, 'w') as fp:
                    json.dump(score_json, fp)
                    os.rename(output_tmp_path, output_path)

                os.remove(input_file)

                # log performance for an assignment
                log_path_name = json_data['path_name']
                with open(log_path_name, 'a+') as log:
                    log.write('{},{}\n'.format(loss, metric))
            except Exception as e:
                print("Could not read JSON file, I'll try again.")
                print("Error:", e)

        time.sleep(0.5)


def evaluation(model, x_train, y_train):
    '''
    Returns ([weights], [biases])
    '''

    # evaluate the model
    scores = model.evaluate(x_train, y_train)
    print("%s: %.3f" % (model.metrics_names[0], scores[0]))
    print("%s: %.3f" % (model.metrics_names[1], scores[1]))
    # return anwser
    return (scores[0], scores[1])


def get_id_from_file_name(name):
    '''
    Matches and returns the integer preceded by "_id"
    '''
    match = re.search(r'(?<=_id)\d+', name)
    id_number = int(match.group(0))
    return id_number


if __name__ == '__main__':
    main()
