"""
OODIDA: code for executing assignments

"""
import numpy
import keras
import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2' # Remove Tensorflow warnings
from keras.models import load_model
from keras.models import Sequential
from keras.layers import Dense
import lib.read_data as data
import lib.utils as ut

import gc


def pong():
    return 1


class Model():

    def on_destroy(self):
        keras.backend.clear_session()


def _get_mnist_data_(image_path, label_path):
    x_iter, y_iter = [], []

    for i in range(len(image_path)):
        x, y = data.read_mnist_data(image_path[i], label_path[i])
        x_iter.append(x)
        y_iter.append(y)

    x_train = numpy.concatenate(x_iter)
    y_train = numpy.concatenate(y_iter)

    # Preprocess the data
    input_size = 28*28
    output_size = 10
    x_train = x_train.reshape(x_train.shape[0], input_size)
    x_train = x_train.astype('float32')
    x_train /= 255
    y_train = keras.utils.to_categorical(y_train, output_size)

    return (x_train, y_train)


class Mnist_Model(Model):

    def __init__(self, lr, decay, E, B, image_path, label_path):
        self.model = ut.build_mnist_model(lr, decay)
        self.E = E
        self.B = B
        self.data = _get_mnist_data_(image_path, label_path)


    def train(self, w_list, b_list):
        '''
        Train a "2NN".
        Return: ([weights], [biases])
        '''
        # Update weights
        ut.update_parameters(self.model.layers, w_list, b_list)

        # Fit the model
        x_train, y_train = self.data
        self.model.fit(x_train, y_train, epochs=self.E, batch_size=self.B, verbose=0)

        # return anwser
        return_params = ut.extract_parameters(self.model.layers)

        return return_params


#################### FSVRG local models #######################

class Fsvrg_Mnist_Model(Model):

    def __init__(self, step_size, image_path, label_path):
        self.data = _get_mnist_data_(image_path, label_path)
        self.step_size_k = step_size / len(self.data[1])

        self.local_model, self.static_model= self.get_training_models()

        # Gradient functions
        self.get_local_gradients = ut.compute_gradients(self.local_model)
        self.get_static_gradients = ut.compute_gradients(self.static_model)

        # TODO: Maybe not hardcode this
        self.shapes = [(28*28, 200), (200,200), (200,10)]


    # Create two identical 2NN-models
    def get_training_models(self):
        local_model = ut.build_mnist_model()

        static_model = keras.models.clone_model(local_model)
        static_model.compile(loss=keras.losses.categorical_crossentropy,
                            optimizer=keras.optimizers.SGD(lr=1))

        # Copy weights
        static_model.set_weights(local_model.get_weights())

        return local_model, static_model


    def train(self, w_list, b_list, glob_gradients_w, glob_gradients_b):
        '''
        Train a "2NN".
        Return: ([weights], [biases])
        '''

        print(f'local lr: {self.step_size_k}')

        ut.update_parameters(self.local_model.layers, w_list, b_list)
        ut.update_parameters(self.static_model.layers, w_list, b_list)

        # Create a random permutation to iterate over
        x_train, y_train = self.data
        indices = numpy.random.permutation(len(y_train))

        global_gradients = ut.flat_to_nested_model(glob_gradients_w,
                                glob_gradients_b, self.shapes)

        # Local update loop, implements lines 7-9 of the algorithm
        for i in indices:
            x = x_train[i].reshape(1, 28*28) #TODO: Maybe not hardcode this
            y = y_train[i].reshape(1, 10)

            inputs = [x,
                      numpy.ones(len(x)), # sample weights
                      y,
                      0 # learning phase in TEST mode
            ]

            iter_gradients = self.get_local_gradients(inputs)
            static_gradients = self.get_static_gradients(inputs)

            gradient_diff= ut.parameter_diff(iter_gradients, static_gradients)
            gradient  = ut.parameter_add(gradient_diff, global_gradients)

            self.apply_gradient(gradient, self.step_size_k)

        # final local model
        return_params = ut.extract_parameters(self.local_model.layers)

        gc.collect()

        return return_params


    def apply_gradient(self, gradient, h_k):

        # Scale by local step-size h_k
        scaled_gradient = ut.parameter_scale(gradient, h_k)

        model = self.local_model
        new_params = ut.parameter_diff(model.get_weights(), scaled_gradient)
        model.set_weights(new_params)
