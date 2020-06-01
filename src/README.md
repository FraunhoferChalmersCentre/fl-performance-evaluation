# Algorithms

We've implemented three algorithms for federated learning:
* [Federated Averaging (FedAvg)](https://arxiv.org/abs/1602.05629)
* [Federated Stochastic Variance Reduced Gradient (FSVRG)](https://arxiv.org/abs/1610.02527)
* [COOP](https://doi.org/10.7939/R32805C45)

Since the algorithms are distributed in nature, the implementations exists both on the clients and in the server.

### On-device training

The program responsible for training models on clients is `compute.py`.

### Centralized aggregation

Model aggregation is performed in the server.
Specifically, the implementations for the algorithms' different aggregations are in `./erlang_framework/server.erl`

The training loops (including model aggregation) for the different algorithms are:
* FedAvg uses `server:update_weights_iter/5`
* FSVRG uses `server:fsvrg_loop/9`
* COOP uses `server:coop_loop/9`

Updated models are verified in the server using `verifier.py`.

### Models

We use Keras to build the neural network models.
The models used in training are defined in `lib_edge/assignment.py` with help of `lib/utils.py`.
The architecture is a "2NN" multi-layer perceptron, as described in [Section 3 of the paper on FedAvg](https://arxiv.org/abs/1602.05629).

# Data

Our benchmarks use [the MNIST database of handwritten digits](http://yann.lecun.com/exdb/mnist/).
This data is further partitioned to 100 clients using different distributions.

The final layout of the directory `./data` consists of four datasets:
```bash
~/D/f/src > ls -1 data/
mnist/
mnist_iid_cv/
mnist-non-iid/
mnist_noniid_cv/
```
Each subdirectory has a different partitioning of data to clients.

**Note**: Unfortunately, we cannot re-create the `mnist-non-iid` as it were in the paper.
However, if you follow the instructions to download and create the data, the other datasets (`mnist`, `mnist_iid_cv` and `mnist_noniid_cv`) will be exactly the ones used in our paper.
`mnist-non-iid` will be generated in the same way as in our experiments, but using a different random seed.
If you're interested in the exact partitioning of `mnist-non-iid` used in the paper, we can provide it upon request.


## Fetch dataset

For convenience, we provide a simple script to download and unpack the data in the right place:
```bash
~/D/f/src> ./download_mnist.sh
```

## Create partitioned datasets

In the following steps, we assume that the uncompressed MNIST data files already exist in `./data/mnist/`.

### `mnist` and `mnist-non-iid`

Both `mnist` and `mnist-non-iid` will assign a unique subset of MNIST each of our 100 clients.
For example, abbreviated contents of `./data/mnist`:

```bash
~/D/f/src> ls -1 data/mnist
car100-images.byte
car100-labels.byte
car10-images.byte
car10-labels.byte
car11-images.byte
car11-labels.byte
# --- snip ---
```
The `car` prefix simply means 'client' and the number is the client ID.

These datasets are primarily used for hyperparameter searches (Appendix A.3 in the paper), but they were also used to create Figure 1 (see the `plot_distribution_of_iid_and_non.ipynb` notebook).
To create the datasets, run `partion_mnist.py` as a script (don't forget to activate the `fl-env` environment!):
```bash
~/D/f/src> python3 partion_mnist.py
```

### `mnist_iid_cv` and `mnist_noniid_cv`

Besides partitioning MNIST to our clients, `mnist_iid_cv` and `mnist_noniid_cv` are designed for 5-fold cross validation.
Therefore, the contents of these directories will be five additional directories, one per fold:
```bash
~/D/f/src> ls -1 data/mnist_iid_cv/
fold1/
fold2/
fold3/
fold4/
fold5/
```
Each fold directory has files for all clients.
These are the datasets used in the training procedure that led to our main results (Section 5 in the paper).

To create this data, you need to run these notebooks:
* `partition_iid_into_folds.ipynb`
* `partition_into_folds.ipynb`



# Results

All results, and eventual crash reports, will be written to file in the `./logs/` directory.


# Example usage

Activate the environment:
```
> conda activate fl-eval
```

Start a local simulation with three clients
```
~/D/fl-performance-evaluation> cd src
~/D/f/src> python3 run_locally.py 3
```
The argument to `run_locally.py` is the number of clients to start.


Write an assignment:
```python
''' example_fedavg.py
'''
import argparse
import benchmark
import fed_avg
import time

# Benchmark different C and E
def bench(start_env):
    def print_generator():
        BENCH_TIME_PER_VAR = 15 # In seconds
        MIN_CR = 3

        CS = [1.0] # List of C parameters to test
        ES = [5]   # List of E parameters to test

        # Tuples of FedAvg parameters
        parameter_pairs = zip(CS, ES)

        for (C, E) in parameter_pairs:
            timestamp = fed_avg.print_assignment(
                            dataset = 'MNIST_iid_cv1',      # Train with mnist_iid_cv, leaving out the first fold
                            chosen_client_proportion = C,
                            run_time = BENCH_TIME_PER_VAR,  # Minimum run-time
                            communication_rounds = MIN_CR,  # Minimum number of communication rounds
                            epochs = E,
                            batch_size = 20,
                            learning_rate = 0.11,
                            lr_decay = 2.2e-7,
                            )
            time.sleep(BENCH_TIME_PER_VAR)
            yield timestamp
        print("Done!")

    # Run benchmark
    benchmark.run(print_generator(), start_env)

if __name__ == '__main__':
    # Check for flag
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start_env',
                        help="start server, user, and clients",
                        action='store_true')
    args = parser.parse_args()

    bench(args.start_env)
```

Valid values for the `dataset` argument to `print_assignment` are:
* MNIST
* MNIST-non-iid
* MNIST_iid_cv[1-5]
* MNIST_noniid_cv1[1-5]

where [1-5] is a number between 1 and 5.
See the other `benchmark_*.py` scripts as well as `fedag.py`, `coop.py` and `fsvrg.py` for additional reference on how to write assignment files.

Send the assignment to the server:
```
~/D/f/src> python3 example_fedavg.py
```
This will block until results are available.


Inspect the result log:
```
~/D/f/src> cat logs/score_log_id1590566040000_MNIST_iid_cv1_C1.0_E5_B20_LR0.11_Decay2.2e-7.csv
```

To quickly kill everything, run this on the machine that hosts the server:
```
./exit.escript
```
This requires that the server is reachable.

**Warning**: `exit.escript` will execute `pkill python3` on both the server and all connected clients.
This will also happen if you press `Ctrl+c` during a benchmark.


## Distributed execution

To run the server + user and a client on separate computers run
```
~/D/f/src> python3 run_server_user.py
```
on the server/user machine and run
```
~/D/f/src> python3 run_client.py 'cloud@IP'
```
on the client computer, where _IP_ is the IP address of the server.


## Large scale simulation

For large scale simulations we want client nodes to be launched as
background processes. This is the behaviour of `run_many_clients.py`.
For instance, to run a simulation with 100 client nodes:
```
~/D/f/src> python3 run_server_user.py
~/D/f/src> python3 run_many_clients.py 100
```
You'll need a fair amount of RAM available to run this, though.

# Copyright

(c) 2018 - 2020 Fraunhofer-Chalmers Research Centre for Industrial Mathematics