#!/usr/bin/python

import sys
import subprocess
import urllib
from limitedstringqueue import LimitedStringQueue

PROGRAM = sys.argv[1]
COMPILER = sys.argv[2]
#ARGS = sys.argv[3]
ARGS = urllib.unquote(sys.argv[3])
IMAGE_ADDR = sys.argv[4]
IMAGE_PASSWD = sys.argv[5]
LOG_FILE = sys.argv[6]
OS_TYPE=sys.argv[7]
EXECID = sys.argv[8]

# this program is for executing outside program on cyber range
class RunProgram():
    # this def allows program to run shell commands in python
    def execute_command(self, command):
        #p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=None)
        q = LimitedStringQueue()
        with open(LOG_FILE, "a") as myfile:
            for line in p.stdout.readlines():
                q.push(line)
                myfile.write(line,)
            myfile.write("\n")     # separate previous outputs
            myfile.write("exec-result: "+EXECID+" "+q.concaturlenc())
            myfile.write("\n")     # separate following outputs
        # Waiting for a return code would not allow background execution, so we don't do it

    # get name of the program from the string PROGRAM provided by users from cyber range definition file
    #def getProgramName(self):
    #    list_elements = PROGRAM.split("/")
    #    return list_elements[-1]

    # execute commands to run the program on cyber range
    def runProgram(self):
        #program_name = self.getProgramName()
        program_compiler = ""
        # get the appropriate compiler
        if COMPILER == "python":
            program_compiler = "python"
        if COMPILER == "ruby":
            program_compiler = "ruby"
        if COMPILER == "powershell":
            program_compiler = "powershell"
        if COMPILER == "bash":
            program_compiler = "bash"
        # process args
        if ARGS == "none":
            program_args = ""
        else:
            program_args = ARGS
        # copy program to /bin/cyberrange of virtual machine
#        command = "sshpass -p {0} scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {1} root@{2}:/bin/cyberrange".format(IMAGE_PASSWD, PROGRAM, IMAGE_ADDR)
#        self.execute_command(command)
#        print command
        # execute program on virtual machine
        defined_aws_version = ["amazon_linux", "amazon_linux2", "red_hat", "ubuntu_16", "ubuntu_18", "ubuntu_20"]
        if OS_TYPE=="windows.7":
            command = "sshpass -p {0} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{1} {2} \"{3}\" {4}".format(IMAGE_PASSWD, IMAGE_ADDR, program_compiler, PROGRAM, program_args)
        elif OS_TYPE in defined_aws_version:
            command = "sshpass -p {0} scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {1} ec2-user@{2}:".format(IMAGE_PASSWD, PROGRAM, IMAGE_ADDR)
            command = "sshpass -p {0} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ec2-user@{1} 'sudo mkdir -p /bin/cyberrange/database/penetration_testing; sudo mv install_sl.sh /bin/cyberrange/database/penetration_testing/'".format(IMAGE_PASSWD, IMAGE_ADDR)
            command = "sshpass -p {0} ssh -i TESTKEY.pem -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ec2-user@{1} {2} {3} {4}".format(IMAGE_PASSWD, IMAGE_ADDR, program_compiler, PROGRAM, program_args)
        else:
            #command = "sshpass -p {0} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{1} {2} {3} {4}".format(IMAGE_PASSWD, IMAGE_ADDR, program_compiler, PROGRAM, program_args)
            command = "sshpass -p {0} ssh -E /dev/null -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{1} {2} '{3} {4}'".format(IMAGE_PASSWD, IMAGE_ADDR, program_compiler, PROGRAM, program_args)
        self.execute_command(command)
        print command

runProgram = RunProgram()
runProgram.runProgram()
