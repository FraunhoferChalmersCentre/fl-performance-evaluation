"""
Start a simulation with a car
"""
import compile_erl
from lib_run import *


compile_erl.compile_all()

ipaddr = get_ip_addr()

bagarg = 'The cloud node name must be given as the first argument.'
args = sys.argv
cloud_name = args[1] if len(args) > 1 else sys.exit(badarg)
car_num = args[2] if len(args) > 2 else '1'

run_car(car_num, cloud_name, ipaddr)
