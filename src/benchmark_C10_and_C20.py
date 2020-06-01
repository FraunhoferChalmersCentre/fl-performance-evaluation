'''
Benchmark variant C and E
'''
import argparse
import benchmark
import fed_avg
import itertools
import time


def bench(start_env):

    def print_generator():
        ESTIMATED_TIME_PER_VAR = 60*60*2.25 # In seconds
        MIN_CR = 1000 # Minimum number of communication rounds
        C = [0.1]
        E = [1, 5, 10]

        combos = list(itertools.product(C, E))
        combos.append((0.2, 1))

        for (C, E) in combos:
            timestamp = fed_avg.print_assignment(
                            dataset = 'MNIST-non-iid',
                            variant = '1',
                            chosen_client_proportion = C,
                            run_time = ESTIMATED_TIME_PER_VAR,
                            communication_rounds = MIN_CR,
                            epochs = E,
                            batch_size = 20,
                            learning_rate = 0.11,
                            lr_decay = 2.2e-7,
                            )
            time.sleep(ESTIMATED_TIME_PER_VAR) # The estimated time will not hold for the last iter
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
