"""

Start a simulation
"""
import compile_erl
import clean_state
from lib_run import *


def main():
    compile_erl.compile_all()
    clean_state.clear()

    ip_addr = get_ip_addr()

    args = sys.argv
    n_cars = string_to_int(args[1]) if len(args) == 2 else 1

    # Run our system
    cloud_name = run_cloud(ip_addr)
    run_user(cloud_name, ip_addr)
    run_cars(n_cars,cloud_name, ip_addr)


if __name__ == '__main__':
    main()