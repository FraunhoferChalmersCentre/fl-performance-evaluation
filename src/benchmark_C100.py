'''
Benchmark variant C and E
'''
import argparse
import benchmark
import fed_avg
import itertools
import time
from numpy import linspace


def bench(start_env):

    def print_generator():
        BENCH_TIME_PER_VAR = 60*60*9 # In seconds
        MIN_CR = 1000 # Minimum number of communication rounds
        CS = [1.0]
        ES = [10, 5, 1]

        combos = list(itertools.product(CS, ES))

        for (C, E) in combos:
            timestamp = fed_avg.print_assignment(
                            dataset = 'MNIST-non-iid',
                            variant = '1',
                            chosen_client_proportion = C,
                            run_time = BENCH_TIME_PER_VAR,
                            communication_rounds = MIN_CR,
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