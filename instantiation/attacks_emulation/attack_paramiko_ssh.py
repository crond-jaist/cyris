#!/usr/bin/python
import paramiko, sys, os, socket
import threading
import subprocess

attacked_addr = sys.argv[1]
username = sys.argv[2]
number = sys.argv[3]
time = sys.argv[4]
basevm_type = sys.argv[5]

class myThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.assign_number = 0

    def run(self):
        print "Starting " + self.name
        if(self.threadID != 5):
            self.assign_number = int(number)/5
        else:
            self.assign_number = int(number) - (int(number)/5)*4

        for i in range(0, self.assign_number):
            try:
                response = ssh_connect()
                if response == 1:
                    print "{}: {}".format(self.name, i)
                elif response == 2:
                    print "socket error"
            except Exception, e:
                print e
                pass
        print "Exiting " + self.name

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(attacked_addr, port=22, username=username, password="abcd")
    except paramiko.AuthenticationException:
        response = 1
    except socket.error:
        response = 2

    ssh.close()
    return response

# Set system date as the same as input
if time != "none":
    if basevm_type == 'kvm':
        os.system("ssh root@{0} date +%Y%m%d -s {1}".format(attacked_addr, time))
    elif basevm_type == 'aws':
        os.system("ssh -i TESTKEY.pem ec2-user@{0} date +%Y%m%d -s {1}".format(attacked_addr, time))

# Create new threads
thread1 = myThread(1, "Thread-1")
thread2 = myThread(2, "Thread-2")
thread3 = myThread(3, "Thread-3")
thread4 = myThread(4, "Thread-4")
thread5 = myThread(5, "Thread-5")

# Start new Threads
thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()

# Wait until threads are finished
thread1.join()
thread2.join()
thread3.join()
thread4.join()
thread5.join()

# Set system date to the correct value.
if time != "none":
    if basevm_type == 'kvm':
        correct_date = subprocess.check_output("date +%Y%m%d", shell=True)
        correct_time = subprocess.check_output("date +%T", shell=True)
        os.system("ssh root@{0} date +%Y%m%d -s {1}".format(attacked_addr, correct_date))
        os.system("ssh root@{0} date +%T -s {1}".format(attacked_addr, correct_time))
        os.system("ssh root@{0} sort --stable --reverse --key=1,2 /var/log/secure -o /var/log/secure".format(attacked_addr))
    elif basevm_type == 'aws':
        correct_date = subprocess.check_output("date +%Y%m%d", shell=True)
        correct_time = subprocess.check_output("date +%T", shell=True)
        os.system("ssh -i TESTKEY.pem ec2-user@{0} sudo date +%Y%m%d -s {1}".format(attacked_addr, correct_date))
        os.system("ssh -i TESTKEY.pem ec2-user@{0} sudo date +%T -s {1}".format(attacked_addr, correct_time))
        os.system("ssh -i TESTKEY.pem ec2-user@{0} sudo sort --stable --reverse --key=1,2 /var/log/secure -o /var/log/secure".format(attacked_addr))
