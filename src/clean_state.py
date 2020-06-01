'''
  Cleans the previous state.
  Supplying a argument 'l' will also remove the
  verification logs.
  Very simple script for doing rm.
'''

import argparse
import os


def clear(rm_logs=False):

    if rm_logs:
        os.system("rm -v logs/score_log_*")
        os.system("rm -v logs/*.log")
        os.system("rm -v logs/*.dump")

    os.system("rm -v state/cloud/verification*")
    os.system("rm -v state/edge_in/edge_result*")
    os.system("rm -v state/edge_out/assignment*")
    os.system("rm -v state/user_in/final_result.json")
    os.system("rm -v state/user_out/assignment*")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clear old state.")
    parser.add_argument('-l', '--logs',
                        help="Clear logs/ as well",
                        action='store_true')
    args = parser.parse_args()

    clear(args.logs)
