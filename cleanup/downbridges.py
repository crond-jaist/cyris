#!/usr/bin/python

# this script is to bring down cyber range 's bridges. It gets the job done by open and see how many bridges are there in the create_bridges.sh file

import sys
import fcntl

filename = sys.argv[1]
clone_id = sys.argv[2]

def down_bridges():
    number = 0
    count = 0
    # Open the /etc/network/interfaces with atomic mode.
    with open(filename, "r+") as my_file:
        fcntl.flock(my_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Read content of the file.
        file_lines = my_file.readlines()
        for line in file_lines:
            if "auto eth{0}".format(clone_id) in line:
                if count == 0:
                    number = file_lines.index(line)
                count = count + 1

        if number != 0:
            gap = 0
            if count != 1:
                gap = 11 * count
            else:
                gap = 10
            print "starting line: ", number - 1
            print "ending line: ", number + gap + 1
            first_part = file_lines[:(number-1)]
            second_part = file_lines[(number+gap):]
        my_file.seek(0)
        if first_part[-1] != "\n" and second_part and second_part[0] != "\n":
            my_file.writelines(first_part)
            my_file.writelines("\n")
            my_file.writelines(second_part)
        else:
            my_file.writelines(first_part+second_part)
        my_file.truncate()
        fcntl.flock(my_file, fcntl.LOCK_UN)

down_bridges()
