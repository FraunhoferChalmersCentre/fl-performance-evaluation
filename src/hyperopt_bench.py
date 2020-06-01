from __future__ import print_function

from hyperopt import Trials, STATUS_OK, tpe
from keras.datasets import mnist
from keras.layers.core import Dense, Dropout, Activation
from keras.models import Sequential
from keras.utils import np_utils
from keras.callbacks import ModelCheckpoint
import keras

from hyperas import optim
from hyperas.utils import eval_hyperopt_space
from hyperas.distributions import choice, uniform, conditional, randint

import datetime as dt


def data():
    """
    Data providing function:

    This function is separated from create_model() so that hyperopt
    won't reload data for each evaluation run.
    """
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train = x_train.reshape(60000, 784)
    x_test = x_test.reshape(10000, 784)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255
    nb_classes = 10
    y_train = np_utils.to_categorical(y_train, nb_classes)
    y_test = np_utils.to_categorical(y_test, nb_classes)
    return x_train, y_train, x_test, y_test


def create_model(x_train, y_train, x_test, y_test):
    """
    Model providing function:

    Create Keras model with double curly brackets dropped-in as needed.
    Return value has to be a valid python dictionary with two customary keys:
        - loss: Specify a numeric evaluation metric to be minimized
        - status: Just use STATUS_OK and see hyperopt documentation if not feasible
    The last one is optional, though recommended, namely:
        - model: specify the model just created so that we can later use it again.
    I was here
    """
    model = Sequential()
    model.add(Dense(200, input_dim=784, activation='relu'))
    model.add(Dense(200, activation='relu'))
    model.add(Dense(10, activation='softmax'))

    # WARNING! These constants are douplicated
    NR_EPOCHS = 50
    LR_FUN = lambda x: 10**x
    DECAY_FUN = lambda x: 10**x

    batch_size = {{choice([10, 20, 50, 600])}}

    lr_exp = {{uniform(-0, -2)}}
    learning_rate = LR_FUN(lr_exp)

    decay_exp = {{uniform(-3, -6)}}
    decay = DECAY_FUN(decay_exp)

    format_str = "\nNew parameters:\nLR = {}\nDecay = {}\nBatch size: {}"
    print(format_str.format(learning_rate, decay, batch_size))

    model.compile(loss='categorical_crossentropy', metrics=['accuracy'],
                  optimizer=keras.optimizers.SGD(lr=learning_rate, decay=decay))

    model_chk_path = './best_model.tmp'
    mcp = ModelCheckpoint(model_chk_path, monitor="val_acc",
                          save_best_only=True, save_weights_only=False)

    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=NR_EPOCHS,
              verbose=2,
              validation_data=(x_test, y_test),
              callbacks=[mcp])
    model.load_weights(model_chk_path)

    score, acc = model.evaluate(x_test, y_test, verbose=0)
    print('Test accuracy:', acc)
    return {'loss': -acc, 'status': STATUS_OK, 'model': model}


if __name__ == '__main__':

    # WARNING! These constants are douplicated
    NR_EPOCHS = 50
    LR_FUN = lambda x: 10**x
    DECAY_FUN = lambda x: 10**x

    current_data = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = '../benchmark_results/centralised/centralised_hyperopt_{}.csv'.format(current_data)
    with open(output_file, 'a+') as log:
        log.write('A Hyperas run with {} epochs\n'.format(NR_EPOCHS))
        log.write('Format: trial, acc, lr, decay, batch size\n')
    # Make a seed from the file name (its numbers) between 0 and 2^32-1
    random_seed = eval(current_data.replace('-', '').replace('_','')) % (2**32)

    trials=Trials()
    best_run, best_model, space = optim.minimize(
            model=create_model,
            data=data,
            rseed=random_seed,
            algo=tpe.suggest,
            max_evals=10,
            trials=trials,
            eval_space=True,
            return_space=True
        )
    print("------------------ Done ------------------")

    # params for the different trials
    best_trial = ("NONE", 0) # : (String, acc)
    for t, trial in enumerate(trials):
        vals = trial.get('misc').get('vals')
        acc = trial.get('result').get('loss')*-1
        values = eval_hyperopt_space(space, vals)
        lr = LR_FUN(values['lr_exp'])
        d = DECAY_FUN(values['decay_exp'])
        batch = values['batch_size']
        summary = "Trial {}:\nAcc={}, Learning rate: {:.2e}, decay: {:.2e}, batch size: {}".format(t,acc,lr,d,batch)
        print(summary)
        with open(output_file, 'a+') as log:
            log.write('{},{},{},{},{}\n'.format(t,acc,lr,d,batch))
        if best_trial[1] < acc:
            best_trial = (summary, acc)

    # Print summary for best trial
    with open(output_file, 'a+') as log:
        log.write('Best run:\n'.format(NR_EPOCHS))
        log.write(best_trial[0])

    print("\n----Best:----")
    X_train, Y_train, X_test, Y_test = data()
    print("Evalutation of best performing model:")
    print(best_model.evaluate(X_test, Y_test))
    print("Best performing model hyper-parameters:")
    lr = LR_FUN(best_run['lr_exp'])
    d = DECAY_FUN(best_run['decay_exp'])
    batch = best_run['batch_size']
    print("Learning rate: {:.2e}, decay: {:.2e}, batch size: {}".format(lr,d,batch))
    print("\nRandom variables:", best_run)
