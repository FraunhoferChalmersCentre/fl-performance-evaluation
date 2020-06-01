'''
Benchmark variant learning rates linearly
'''
import argparse
import benchmark
import fed_avg
import time
from numpy import linspace


def bench(start_env):

    def print_generator():
        BENCH_TIME_PER_VAR = 60*60*2.4 # In seconds
        MIN_CR = 1200 # Minimum number of communication rounds
        learning_rates = linspace(0.09, 0.02, 8)

        for lr in learning_rates:
            timestamp = fed_avg.print_assignment(
                            dataset = 'MNIST-non-iid',
                            variant = '1',
                            chosen_client_proportion = 0.1,
                            run_time = BENCH_TIME_PER_VAR,
                            communication_rounds = MIN_CR,
                            epochs = 5,
                            batch_size = 20,
                            learning_rate = lr,
                            lr_decay = 0,
                            )
            time.sleep(BENCH_TIME_PER_VAR)
            yield timestamp
        print("Done!")

    # Run benchmark with learning_rates
    benchmark.run(print_generator(), start_env)



if __name__ == '__main__':
    # Check for flag
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start_env',
                        help="start server, user, and clients",
                        action='store_true')
    args = parser.parse_args()

    bench(args.start_env)