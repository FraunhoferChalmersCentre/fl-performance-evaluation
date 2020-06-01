import csv
import glob
import numpy
import struct


def read_mnist_data(fname_img, fname_lbl):
    '''
    Read MNIST data from a byte file.

    Return: tuple of inputs and labels (numpy)
    '''
    with open(fname_lbl, 'rb') as flbl:
        magic, num = struct.unpack(">II", flbl.read(8))
        lbl = numpy.fromfile(flbl, dtype=numpy.int8)
        if len(lbl) != num:
            print('Header mismatch. #labels != header number')

    with open(fname_img, 'rb') as fimg:
        magic, num, rows, cols = struct.unpack(">IIII", fimg.read(16))
        img = numpy.fromfile(fimg, dtype=numpy.uint8).reshape(num, rows, cols)

    return (img, lbl)

def read_cars_data(input_path):
    reg_exp_file = input_path + 'car*-labels.byte'
    input_files = glob.glob(reg_exp_file)
    num_cars = len(input_files)

    car_labels_str = input_path + 'car{}-labels.byte'
    car_images_str = input_path + 'car{}-images.byte'

    x_return = []
    y_return = []

    for idx in range(1, num_cars+1):
        # Read file
        image_file = car_images_str.format(idx)
        label_file = car_labels_str.format(idx)
        x, y = read_mnist_data(image_file, label_file)

        # accumulate/store chosen
        x_return.append(x)
        y_return.append(y)

    # return
    return (numpy.concatenate(x_return), numpy.concatenate(y_return))

def read_mnist_car_data():
    path = '../src/data/mnist/'

    return read_cars_data(path)
