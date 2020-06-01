'''
Benchmark variant 0, 1 and 2
This scipt can not run with a process called "python3"
'''
import clean_state
import fed_avg
import os
import signal
import sys
import time


def ctrl_c_handler(signal, frame):
    print('You pressed Ctrl+C!')
    os.system('./exit.escript')
    sys.exit(0)

signal.signal(signal.SIGINT, ctrl_c_handler)


BENCH_TIME_PER_VAR = 60*60*15 # In seconds
MIN_CR = 5000 # Minimum number of communication rounds
COOLDOWN_TIME = 60*15 # In seconds

variants = ['0', '1', '2']


clean_state.clear()

print("Starting server")
os.system('python run_server_user.py')
time.sleep(1)

print("Running clients")
os.system('python run_many_clients.py 100')
time.sleep(1)

for variant in variants:
    print("Print assignment")
    fed_avg.print_assignment(variant=variant,
                            run_time=BENCH_TIME_PER_VAR,
                            communication_rounds=MIN_CR)

    time.sleep(BENCH_TIME_PER_VAR)
    result_file_path = './state/user_in/final_result.json'
    while not os.path.isfile(result_file_path):
        print("Waiting for result...")
        time.sleep(10)
    os.remove(result_file_path) # Consume the result

    time.sleep(COOLDOWN_TIME)

print("Death Blossom activated")
os.system('./exit.escript') # Kills "python3", but not "python"