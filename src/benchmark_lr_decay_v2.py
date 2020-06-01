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
        NUM_RANDOM_SAMPLES = 10
        SEED = 2018-3-28
        np.random.seed(SEED)
        decays = [10**x for x in np.random.uniform(-4, -3, NUM_RANDOM_SAMPLES)]
        learning_rates = np.random.uniform(0.05, 0.08, NUM_RANDOM_SAMPLES)
        random_samples = list(zip(learning_rates, decays))

        BENCH_TIME_PER_VAR = 0
        MIN_CR = 20 # Minimum number of communication rounds

        E = [1, 5, 10]
        B = [10, 20, 600]

        for epochs, batch_size in zip(E, B):
            for _ in range(3):
                for lr, decay in random_samples:
                    timestamp = fed_avg.print_assignment(
                                    dataset = 'MNIST-non-iid',
                                    variant = '1',
                                    chosen_client_proportion = 1.0,
                                    run_time = BENCH_TIME_PER_VAR,
                                    communication_rounds = MIN_CR,
                                    epochs = epochs,
                                    batch_size = batch_size,
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
