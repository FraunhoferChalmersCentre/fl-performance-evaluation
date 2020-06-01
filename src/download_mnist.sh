#!/bin/bash

DATA_DIR=./data/mnist/
DOWNLOAD_DIR=./tmp

BASE_URL=http://yann.lecun.com/exdb/mnist/
DATAFILES=(train-images-idx3-ubyte.gz train-labels-idx1-ubyte.gz t10k-images-idx3-ubyte.gz t10k-labels-idx1-ubyte.gz)

for file in "${DATAFILES[@]}"
do 
    wget $BASE_URL$file -P $DATA_DIR -nc
    printf "Decompressing '$file'... "
    gunzip --name --force --keep $DATA_DIR$file
    printf "Done\n\n"  
done
