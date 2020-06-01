'''
Quick simulation test with many clients
'''
import clean_state
import fed_avg
import coop
import os
import signal
import sys
import time


def ctrl_c_handler(signal, frame):
    print('You pressed Ctrl+C!')
    os.system('./exit.escript')
    sys.exit(0)

signal.signal(signal.SIGINT, ctrl_c_handler)


RUN_TIME = 60*60*15 # In seconds
MIN_CR = 100 # Minimum number of communication rounds

nr_clients = '10'
if len(sys.argv) > 1:
    nr_clients = sys.argv[1]

clean_state.clear()

print("Starting server")
os.system('python3 run_server_user.py')
time.sleep(1)

print("Running clients")
os.system('python3 run_many_clients.py ' + nr_clients)
time.sleep(1)


print("Print assignment")
if True:
    fed_avg.print_assignment(
                            variant='1',
                            run_time=RUN_TIME,
                            communication_rounds=MIN_CR,
                            dataset = 'MNIST-non-iid',
                            chosen_client_proportion = 0.30,
                            epochs = 1,
                            batch_size = 50,
                            learning_rate = 0.05,
                            lr_decay = 1e-5,
                            )
else:
    coop.print_assignment(
                        dataset = 'MNIST',
                        communication_rounds = 2,
                        lower_age_limit = 2,
                        upper_age_limit = 7,
                        epochs = 5,
                        batch_size = 20,
                        learning_rate = 0.05,
                        lr_decay = 1e-5,
                        )

time.sleep(RUN_TIME+1e7)


print("Death Blossom activated")
os.system('./exit.escript') # Kills "python3", but not "python"