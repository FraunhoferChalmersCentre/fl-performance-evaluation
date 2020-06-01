'''
Generates partions from two MNIST files (images and labels).
The paths for the files are static.
'''
import struct
import numpy
import random
import os


def run_partition_mnist():
    SEED_NR = 20180316
    n_partitions = 100
    total_nr_data = 60000
    input_dir = '../src/data/mnist/'
    images_file = input_dir + 'train-images.idx3-ubyte'
    labels_file = input_dir + 'train-labels.idx1-ubyte'

    pairs = get_byte_list(labels_file, images_file)
    random.seed(SEED_NR)
    random.shuffle(pairs)
    nr_data_per_car = [total_nr_data//n_partitions]*n_partitions
    output_dir = './data/mnist/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    partition_mnist_list(pairs, nr_data_per_car, output_dir)


def run_write_non_iid():
    SEED_NR = 20180316
    input_dir = './data/mnist/'
    labels_file = input_dir + 'train-labels.idx1-ubyte'
    images_file = input_dir + 'train-images.idx3-ubyte'

    r = get_byte_record(labels_file, images_file)
    random.seed(SEED_NR)
    shards = divid_into_shards(r)

    output_dir = './data/mnist-non-iid/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    write_non_iid(shards, output_dir)


def get_byte_record(lbl_file_name, img_file_name):
    '''
    Returns a dictionary,
    where the key is a label and the value is images in a list.
    Labels and images are stored as bytes.
    '''
    record = dict()
    for i in range(10):
        i_in_byte = (i).to_bytes(1, byteorder='big')
        record[i_in_byte] = []

    with open(lbl_file_name, 'rb') as lbl_file, open(img_file_name, 'rb') as img_file:

        magic_number, num = struct.unpack('>II', lbl_file.read(8))
        _magic, _num, rows, cols = struct.unpack('>IIII', img_file.read(16))

        assert(num == _num)

        for i in range(num):
            label = lbl_file.read(1)
            img = img_file.read(rows*cols)

            record[label].append(img)

    return record


def get_byte_list(lbl_file_name, img_file_name):
    '''
    Returns a list of tuples,
    each tuple contains a label and an image, both in bytes.
    '''

    tuples = []
    with open(lbl_file_name, 'rb') as lbl_file, open(img_file_name, 'rb') as img_file:

        magic_number, num = struct.unpack('>II', lbl_file.read(8))
        _magic, _num, rows, cols = struct.unpack('>IIII', img_file.read(16))

        assert(num == _num)

        for i in range(num):
            label = lbl_file.read(1)
            img = img_file.read(rows*cols)

            tuples.append((label, img))

    return tuples


def divid_into_shards(record):
    '''
    record: a bucket (dict) of digits,
        where each bucket contains corresponding images.

    Sorts the images by label, divids them into 200 shards of size 300.
    Idea taken from the FedAvg papper.

    return: a shuffle list of shards.
    '''
    mnist = record.items() # a list of tuples, where each tuple have a label and a list of images
    pairs = [(tups[0], item) for tups in mnist for item in tups[1]]
    pairs = sorted(pairs, key=lambda x: x[0])
    rest = pairs
    shards = []

    for _ in range(200):
        shard = rest[:300]
        rest = rest[300:]
        shards.append(shard)

    random.shuffle(shards)
    return shards


def write_non_iid(shards, output_dir):
    '''
    shards: a list of fragments of the sorted list of input/label pairs
    output_dir: where to put the resulting files

    This function writes two shards per car.
    Same thing as the FedAvg papper does.
    '''
    n_shards = len(shards)
    for i2 in range(0, n_shards, 2):
        car_i = i2 // 2 + 1

        lbls_file_name = "{}car{}-labels.byte".format(output_dir, car_i)
        imgs_file_name = "{}car{}-images.byte".format(output_dir, car_i)
        with open(lbls_file_name, 'wb') as lbl_file, \
                open(imgs_file_name, 'wb') as img_file:

            lbl_magic_nr = b'\x00\x00\x08\x01' # ubyte, 1-dim
            n_lbl = (600).to_bytes(4, byteorder='big')
            lbl_header = lbl_magic_nr + n_lbl
            lbl_file.write(lbl_header)

            img_magic_nr = b'\x00\x00\x08\x03' # ubyte, 3-dim
            n_imgs = (600).to_bytes(4, byteorder='big')
            n_rows = (28).to_bytes(4, byteorder='big')
            n_cols = (28).to_bytes(4, byteorder='big')
            img_header = img_magic_nr + n_imgs + n_rows + n_cols
            img_file.write(img_header)

            for shard in (shards[i2], shards[i2+1]):
                for (lbl, img) in shard:
                    lbl_file.write(lbl)
                    img_file.write(img)


def partition_mnist_list(pairs, nr_data_per_car, output_dir):

    for i, nr_data in enumerate(nr_data_per_car):
        number_list = pairs[:nr_data]
        pairs = pairs[nr_data:]
        car_i = i+1

        lbls_file_name = "{}car{}-labels.byte".format(output_dir, car_i)
        imgs_file_name = "{}car{}-images.byte".format(output_dir, car_i)
        with open(lbls_file_name, 'wb') as lbl_file, \
                open(imgs_file_name, 'wb') as img_file:

            lbl_magic_nr = b'\x00\x00\x08\x01' # ubyte, 1-dim
            n_lbl = (nr_data).to_bytes(4, byteorder='big')
            lbl_header = lbl_magic_nr + n_lbl
            lbl_file.write(lbl_header)

            img_magic_nr = b'\x00\x00\x08\x03' # ubyte, 3-dim
            n_imgs = (nr_data).to_bytes(4, byteorder='big')
            n_rows = (28).to_bytes(4, byteorder='big')
            n_cols = (28).to_bytes(4, byteorder='big')
            img_header = img_magic_nr + n_imgs + n_rows + n_cols
            img_file.write(img_header)

            for (lbl, img) in number_list:
                lbl_file.write(lbl)
                img_file.write(img)



if __name__ == '__main__':
    run_write_non_iid()
    run_partition_mnist()