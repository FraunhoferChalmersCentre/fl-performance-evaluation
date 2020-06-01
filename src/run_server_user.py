"""
Start a simulation with a server and a user
"""

import clean_state
import compile_erl
from lib_run import *


compile_erl.compile_all()
clean_state.clear()

ipaddr = get_ip_addr()

cloud_name = run_cloud(ipaddr)
run_user(cloud_name, ipaddr)