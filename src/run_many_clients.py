#!/usr/bin/env python3
"""
run_many_clients.py

Start client nodes only, and run them as background proccesses.
The edge computation script is also run in the background, one per client.
You probably want to execute run_server_user.py prior to this script.
"""
import clean_state
import datetime
import os
import argparse
import subprocess
import compile_erl
import lib_run
from lib_run import get_ip_addr, init_car


def run(car_ids, cloud_name=None, attached=False):

    compile_erl.compile_all()
    clean_state.clear()

    ip_addr = get_ip_addr()

    if cloud_name == None:
        cloud_name = 'cloud' + '@' + ip_addr

    now = datetime.datetime.now()
    log_file = "./logs/{}_{}clients.log".format(now.strftime("%Y-%m-%d_%H-%M-%S"), len(car_ids))

    start_car = lib_run.run_car if attached else run_erl_detached_car
    for car_id in car_ids:
        start_car(car_id, cloud_name, ip_addr, log_file)

    print("Done")


def run_erl_detached_car(car_number, cloud_name, ip_addr, log_file):
    car_number = str(car_number)
    car_name = 'car' + car_number + '@' + ip_addr

    init_car_code = init_car(car_number, cloud_name)
    heartbeat = '-heart -env HEART_BEAT_TIMEOUT 300 -env ERL_CRASH_DUMP_SECONDS -1'
    erl_cmd = 'erl {} -hidden -detached -name {} -eval \"{}\"'.format(heartbeat, car_name, init_car_code)

    os.system(erl_cmd)
    subprocess.Popen(['python3', 'compute.py', car_number, log_file], stdout=subprocess.DEVNULL)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Run clients without terminals.")
    parser.add_argument('last_car_num',
                        help="last car number",
                        type=int,
                        default=100,
                        nargs='?')
    parser.add_argument('first_car_num',
                        help="first car number",
                        type=int,
                        default=1,
                        nargs='?')
    parser.add_argument('-n', '--sname', help="set server name")
    parser.add_argument('-a', '--attached',
                        help="erl starts without the detached flag",
                        action='store_true')
    args = parser.parse_args()

    # arguments
    order = -1 if args.first_car_num > args.last_car_num else 1
    car_ids = range(args.first_car_num, args.last_car_num + order, order)
    cloud_name = args.sname
    # run
    run(car_ids, cloud_name, args.attached)
