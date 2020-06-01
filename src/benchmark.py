
import clean_state
import glob
import os
import signal
import sys
import time


def run(print_generator, start_environment=False):

    def ctrl_c_handler(signal, frame):
        print('You pressed Ctrl+C!')
        os.system('./exit.escript')
        sys.exit(0)
    signal.signal(signal.SIGINT, ctrl_c_handler)

    COOLDOWN_TIME = 5 # In seconds

    clean_state.clear()

    if start_environment:
        print("Starting server")
        os.system('python run_server_user.py')
        time.sleep(1)

        print("Running clients")
        os.system('python run_many_clients.py 100')
        time.sleep(1)

    for timestamp in print_generator:
        # Wait for result before continuing
        result_file_path = './state/user_in/final_result.json'
        wait_count = 0
        while not os.path.isfile(result_file_path):
            wait_count += 1
            print("Waiting for result...", wait_count, "times\r",end="")
            time.sleep(10)
        print("")
        os.remove(result_file_path) # Consume the result

        # Print last score
        log_path_reg = 'logs/score_log_id{}*.csv'.format(timestamp)
        log_path = glob.glob(log_path_reg)[0]
        with open(log_path, 'r') as f:
            print(f.readlines()[-1])

        time.sleep(COOLDOWN_TIME)