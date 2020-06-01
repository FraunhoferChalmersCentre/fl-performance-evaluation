import numpy
import keras
from keras import backend as K
from keras.layers import Dense
from keras.models import Sequential
import operator as op

import logging
import gc

######################## Keras utilities  ########################

######### Create ANN models #########

def build_mnist_model(lr=0.01, decay=0.0):
    '''
    The 2NN from the FedAvg paper.

    Return: a Keras model
    '''

    input_size = 28*28
    output_size = 10

    # create model
    model = Sequential()
    model.add(Dense(200, input_dim=input_size, activation='relu'))
    model.add(Dense(200, activation='relu'))
    model.add(Dense(output_size, activation='softmax'))

    # Compile model
    model.compile(loss=keras.losses.categorical_crossentropy,
                  optimizer=keras.optimizers.sgd(lr=lr, decay=decay),
                  metrics=['accuracy'])
    return model


def reshape_mnist(x_raw, y_raw):
    '''
    Return normalised and reshaped mnist data, ready to be inputted to
    a Keras model
    '''
    x_train = x_raw.reshape(x_raw.shape[0], 28*28)
    x_train = x_train.astype('float32')
    x_train /= 255
    y_train = keras.utils.to_categorical(y_raw, 10)
    return (x_train, y_train)


######### Change parameters #########

def update_parameters(layers, w_list, b_list):
    '''
    Modifies the parameters in each layer of 'layers'.
    '''
    for layer, w, b  in zip(layers, w_list, b_list):
        w_shape = layer.get_weights()[0].shape
        b_shape = layer.get_weights()[1].shape
        w = numpy.array(w)
        w = w.reshape(w_shape)
        b = numpy.array(b)
        b = b.reshape(b_shape)
        layer.set_weights([w,b])


def extract_params_from(layer):
    '''
    Returns the weights and the biases in two flatten lists.
    '''
    [ws, bs] = layer.get_weights()
    weights = ws.flatten().tolist()
    biases = bs.tolist()
    return (weights, biases)


def extract_parameters(layers):
    '''
    Returns the weights and the biases in two lists of lists.
    '''
    w_list = []
    b_list = []
    for layer in layers:
        w, b = extract_params_from(layer)
        w_list.append(w)
        b_list.append(b)
    return (w_list, b_list)


def flatten_model(full_model):
    '''
    Reshape a model extracted from Keras to a shape we can encode in JSON
    '''
    ws = [full_model[i].flatten().tolist() for i in range(0, len(full_model), 2)]
    bs = [full_model[i].tolist() for i in range(1, len(full_model), 2)]

    return (ws, bs)


def flat_to_nested_model(ws, bs, shapes):
    '''
    Reshape a model extracted from JSON to the format used by Keras
    shapes: list of shape-tuples of weights between layers.
    '''
    assert(len(ws) == len(bs))

    res = []
    for i in range(len(bs)):
        res.append(numpy.array(ws[i]).reshape(shapes[i]).tolist())
        res.append(numpy.array(bs[i]).tolist())

    return res


######### Parameter arithmetics #########

def parameter_diff(p1, p2):
    return parameter_op(p1, p2, op.sub)


def parameter_add(p1, p2):
    return parameter_op(p1, p2, op.add)


def parameter_scale(params, scalar : float):
    for i in range(0, len(params), 2):
        params[i+1] *= scalar
        for j in range(len(params[i])):
            params[i][j] *= scalar
    return params


def parameter_op(param1, param2, operator):
    '''
    Returns the difference between two parameter tuples
    All arguments are lists with equal length in the outermost dimension.
    '''
    assert(len(param1) == len(param2))

    for i in range(0, len(param1), 2):
        param1[i+1] = operator(param1[i+1], param2[i+1])
        for j in range(len(param1[i])):
            param1[i][j] = operator(param1[i][j], param2[i][j])
    return param1


######### Custom training #########

def compute_gradients(model):
    # https://github.com/keras-team/keras/issues/2226

    weights = model.trainable_weights
    grads = model.optimizer.get_gradients(model.total_loss, weights)

    input_tensors = [model.inputs[0], # input data
                     model.sample_weights[0], # how much to weight each sample by
                     model.targets[0], # labels
                     K.learning_phase(), # train or test mode
    ]

    get_gradients = K.function(inputs=input_tensors, outputs=grads)

    return get_gradients


######################## Misc. ########################

class LazyData:
    'A class for lazy loading of data'

    def __init__(self, load_function):
        '''
        load_function: nullary function that returns a inputs/labels pair
        '''
        self.load_function = load_function
        self.data = None

    def load(self):
        if self.data != None:
            return self.data
        else:
            self.data = self.load_function()
            return self.data
