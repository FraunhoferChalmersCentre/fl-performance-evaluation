'''
Benchmark variant C and E
'''
import argparse
import benchmark
import coop
import itertools
import time
import datetime as d # d.datetime(2018,4,24,16,43)
import numpy as np


def bench(start_env):
    def print_generator():
        N_LINEAR_SAMPLES = 8
        NUM_RANDOM_SAMPLES = 20
        N_SAMPLES = 4
        SEED = 7
        Bls = [32-16]*N_SAMPLES
        Bus = [67-16]*N_SAMPLES
        CRs = [5000]*N_SAMPLES

        np.random.seed(SEED)
        rand_decay = [10**x for x in np.random.uniform(-8, -3, NUM_RANDOM_SAMPLES)]
        rand_lr = np.random.uniform(0.02, 0.15, NUM_RANDOM_SAMPLES)

        linear_lr = np.linspace(0.09, 0.02, N_LINEAR_SAMPLES)
        learning_rates = rand_lr #np.concatenate((rand_lr, linear_lr))
        lr_decays = rand_decay #+[0]*N_LINEAR_SAMPLES

        indices = np.array([8,9,14,15])
        mask = np.zeros(20, dtype=bool)
        mask[indices] = True
        lr_decays = np.array(lr_decays)[mask]
        learning_rates = learning_rates[mask]

        #(Bl, Bu, CR, Time, lr)
        bench_collection = zip(Bls, Bus, CRs, learning_rates, lr_decays)
        for tup in bench_collection:
            (Bl, Bu, CR, lr, d) = tup
            timestamp = coop.print_assignment(
                            dataset = 'MNIST-non-iid',
                            run_time = 0,
                            communication_rounds = CR,
                            report_frequency = 10,
                            lower_age_limit = Bl,
                            upper_age_limit = Bu,
                            epochs = 1,
                            batch_size = 20,
                            learning_rate = lr,
                            lr_decay = d,
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
