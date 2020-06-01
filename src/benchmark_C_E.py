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
        BENCH_TIME_PER_VAR = 60*60*28 # In seconds
        MIN_CR = 1000 # Minimum number of communication rounds
        C50 = [0.5]
        E50 = [1, 5]
        C100 = [1.0]
        E100 = [1, 5, 10]

        combos = list(itertools.product(C50, E50))
        combos = combos + list(itertools.product(C100, E100))

        for (C, E) in combos:
            timestamp = fed_avg.print_assignment(
                            dataset = 'MNIST-non-iid',
                            variant = '1',
                            chosen_client_proportion = C,
                            run_time = BENCH_TIME_PER_VAR,
                            communication_rounds = MIN_CR,
                            epochs = E,
                            batch_size = 20,
                            learning_rate = 0.05,
                            lr_decay = 1e-5,
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