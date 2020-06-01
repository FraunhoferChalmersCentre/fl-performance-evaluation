'''
Benchmark using cross validation
'''
import argparse
import benchmark
import fed_avg
import itertools
import time


def bench(start_env):

    def print_generator():

        for fold_num in range(3,5):
            timestamp = fed_avg.print_assignment(
                            dataset = 'MNIST_noniid_cv'+str(fold_num),
                            variant = '1',
                            chosen_client_proportion = 0.1,
                            run_time = 0,
                            communication_rounds = 1000,
                            epochs = 5,
                            batch_size = 20,
                            learning_rate = 0.088,
                            lr_decay = 3.2e-6,
                            )
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
