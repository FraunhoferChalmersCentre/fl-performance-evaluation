'''
Benchmark variant C and E
'''
import argparse
import benchmark
import coop
import itertools
import time
import datetime as d


def bench(start_env):

    def print_generator():
        Bls = [32]
        Bus = [67]
        CRs = [1000]
        Times = [None]

        for (Bl, Bu, CR, Time) in zip(Bls, Bus, CRs, Times):
            if Time == None:
                stop_time = d.datetime(2018,4,23,7,57)
                Time = (stop_time-d.datetime.now()).total_seconds()
            timestamp = coop.print_assignment(
                            dataset = 'MNIST-non-iid',
                            run_time = Time,
                            communication_rounds = CR,
                            report_frequency = 10,
                            lower_age_limit = Bl,
                            upper_age_limit = Bu,
                            epochs = 1,
                            batch_size = 20,
                            learning_rate = 0.05,
                            lr_decay = 1e-5,
                            )
            time.sleep(Time)
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
