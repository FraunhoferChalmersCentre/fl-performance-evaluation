'''
Benchmark variant LRs and decays
This scipt should not run with a process called "python3"
'''
import argparse
import benchmark
import fed_avg
import numpy as np
import os
import time


def bench(start_server_locally):

    def print_generator():
        NUM_RANDOM_SAMPLES = 20
        SEED = 7
        np.random.seed(SEED)
        decays = [10**x for x in np.random.uniform(-8, -3, NUM_RANDOM_SAMPLES)]
        learning_rates = np.random.uniform(0.02, 0.15, NUM_RANDOM_SAMPLES)
        random_samples = list(zip(learning_rates, decays))

        idxs = [0,2,3,5,8,9,10,11,17,18]

        BENCH_TIME_PER_VAR = 0
        MIN_CR = 10 # Minimum number of communication rounds

        for lr, decay in [random_samples[i] for i in idxs]:
            timestamp = fed_avg.print_assignment(
                            dataset = 'MNIST-non-iid',
                            variant = '1',
                            chosen_client_proportion = 1.0,
                            run_time = BENCH_TIME_PER_VAR,
                            communication_rounds = MIN_CR,
                            epochs = 1,
                            batch_size = 10,
                            learning_rate = lr,
                            lr_decay = decay,
                            )

            time.sleep(BENCH_TIME_PER_VAR)
            yield timestamp
        print("Death Blossom activated")
        os.system('./exit.escript') # Kills "python3", but not "python"

    # Run benchmark
    benchmark.run(print_generator(), start_server_locally)



if __name__ == '__main__':
    # Check for flag
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start_env',
                        help="start server, user, and clients",
                        action='store_true')
    args = parser.parse_args()

    bench(args.start_env)