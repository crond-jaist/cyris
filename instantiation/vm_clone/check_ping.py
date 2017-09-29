#!/usr/bin/python

import os
import sys

def check_ping(addr):

    return_value = os.system("ping -c 1 " + addr)
    exit_status = os.WEXITSTATUS(return_value)
    if exit_status == 0:
        pingstatus = 1
    else:
        pingstatus = 0
    return pingstatus


addr_file = sys.argv[1]
addr_list = []
try:
    with open(addr_file) as f:
        addr_list = f.readlines()
except IOError:
    print "Could not read file:", addr_file
for addr in addr_list:
    addr = addr.rstrip("\n")
    print addr
    if not addr:
        print "WARNING: Address to ping is empty."
        continue
    while True:
        status = check_ping(addr)
        if status == 1:
            print addr," connectable"
            break

