'''
A library for the run scripts
'''

import datetime
import os
import socket
import sys


def get_ip_addr():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def string_to_int(s):
    try:
        return int(s)
    except:
        sys.exit("ERROR: The argument should be the number of cars.")


def gnome_term_2(prog1, prog2):
    return 'gnome-terminal --tab -e "{}" --tab -e "{}"'.format(prog1, prog2)


def run_cloud(ip_addr):

    def erl_cloud(name, eval_code):
        return 'erl -name {} -eval \\"{}\\"'.format(name, eval_code)

    def init_cloud():
        return 'bridge:init_cloud()'

    def py_verifier():
        return 'python3 ./verifier.py'

    cloud_name = 'cloud' + '@' + ip_addr
    erl_cloud_str = erl_cloud(cloud_name, init_cloud())
    command = gnome_term_2(erl_cloud_str, py_verifier())

    os.system(command)

    return cloud_name


def run_user(cloud_name, ip_addr):

    def gnome_term_1(prog):
        return 'gnome-terminal -e "{}"'.format(prog)

    def erl_user(name, eval_code):
        return 'erl -name {} -eval \\"{}\\"'.format(name, eval_code)

    def init_user(cloud_name):
        return "bridge:init_user('{}')".format(cloud_name)

    user_name = 'user' + '@' + ip_addr
    erl_user_str = erl_user(user_name, init_user(cloud_name))
    command = gnome_term_1(erl_user_str)

    os.system(command)


def run_cars(n_cars, cloud_name, ip_addr):
    now = datetime.datetime.now()
    log_file = "./logs/{}_{}clients.log".format(now.strftime("%Y-%m-%d_%H-%M-%S"), n_cars)

    for car_i in range(1,n_cars+1):
        run_car(car_i, cloud_name, ip_addr, log_file)


def run_car(car_number, cloud_name, ip_addr, log_file=""):
    car_name = 'car' + str(car_number) + '@' + ip_addr

    init_car_str = init_car(car_number, cloud_name)
    erl_car_str = erl_car(car_name, init_car_str)
    command = gnome_term_2(erl_car_str, py_compute(car_number, log_file))

    os.system(command)


def erl_car(name, eval_code):
    heartbeat = '-heart -env HEART_BEAT_TIMEOUT 300 -env ERL_CRASH_DUMP_SECONDS -1'
    return 'erl {} -name {} -hidden -eval \\"{}\\"'.format(heartbeat, name, eval_code)


def init_car(num, cloud_name):
    return "bridge:init_car({}, '{}').".format(num, cloud_name)


def py_compute(car_number, log_file):
    return 'python3 compute.py {} {}'.format(car_number, log_file)
