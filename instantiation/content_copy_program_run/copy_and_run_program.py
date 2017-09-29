#!/usr/bin/python

#import os
import sys
import subprocess

PROGRAM = sys.argv[1]
COMPILER = sys.argv[2]
ARGS = sys.argv[3]
IMAGE_ADDR = sys.argv[4]
IMAGE_PASSWD = sys.argv[5]
LOG_FILE = sys.argv[6]

# this program is for executing outside program on cyber range
class RunProgram():
    # this def allows program to run shell commands in python
    def execute_command(self, command):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with open(LOG_FILE, "a") as myfile:
            for line in p.stdout.readlines():
                myfile.write(line,)

    # get name of the program from the string PROGRAM provided by users from cyber range definition file
    def getProgramName(self):
        list_elements = PROGRAM.split("/")
        return list_elements[-1]

    # execute commands to run the program on cyber range
    def runProgram(self):
        program_name = self.getProgramName()
        program_compiler = ""
        # get the appropriate compiler
        if COMPILER == "python":
            program_compiler = "python"
        if COMPILER == "ruby":
            program_compiler = "ruby"
        # process args
        if ARGS == "none":
            program_args = ""
        else:
            program_args = ARGS
        # copy program to /bin/cyberrange of virtual machine
        command = "sshpass -p {0} scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {1} root@{2}:/bin/cyberrange".format(IMAGE_PASSWD, PROGRAM, IMAGE_ADDR)
        self.execute_command(command)
        print command
        # execute program on virtual machine
        command = "sshpass -p {0} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{1} {2} /bin/cyberrange/{3} {4}".format(IMAGE_PASSWD, IMAGE_ADDR, program_compiler, program_name, program_args)
        self.execute_command(command)
        print command
        # delete program to /bin/cyberrange
        command = "sshpass -p {0} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{1} \"rm -f /bin/cyberrange/{2}\"".format(IMAGE_PASSWD, IMAGE_ADDR, program_name)
        self.execute_command(command)

runProgram = RunProgram()
runProgram.runProgram()
