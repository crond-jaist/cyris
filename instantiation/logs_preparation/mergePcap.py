#!/usr/bin/env python

import os
import sys
import subprocess
from time import sleep
from scapy.all import PcapReader
#from scapy.error import Scapy_Exception

NOISE = sys.argv[1]
FILE_NAME = sys.argv[2]
ABSPATH = sys.argv[3]
CR_DIR = sys.argv[4]

INSTANTIATION_DIR="instantiation"

class PcapCreation():
    def execute_command(self, command):
       subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def get_pcap_timestamp(self, pcapfile):
        try:
            pcap_content = PcapReader(pcapfile)
            list_timestamp = list(pcap_content)
            start_time = list_timestamp[0].time
            end_time = list_timestamp[-1].time
        except IOError:
            pcap_content = PcapReader(pcapfile)
            list_timestamp = list(pcap_content)
            start_time = list_timestamp[0].time
            end_time = list_timestamp[-1].time
       
        print "{0}: {1} - {2}".format(pcapfile, start_time, end_time)
        return (start_time + end_time)/2
    
    def merge_pcap(self):
        noise_file = ""
        
        # convert pcapng to pcap
        command = "editcap -F libpcap {0}attack.pcapng {0}attack.pcap;\n".format(CR_DIR)
        os.system(command)

        path = "{0}attack.pcap".format(CR_DIR)

        sleep(0.5)
        if os.path.isfile(path):
            print "yes"
        else:
            print "no"

        time1 = self.get_pcap_timestamp(path)
        if NOISE == "low":
            noise_file = "{0}{1}/logs_preparation/noise_low.pcap".format(ABSPATH, INSTANTIATION_DIR)
        elif NOISE == "medium":
            noise_file = "{0}{1}/logs_preparation/noise_medium.pcap".format(ABSPATH, INSTANTIATION_DIR)
        elif NOISE == "high":
            noise_file = "{0}{1}/logs_preparation/noise_high.pcap".format(ABSPATH, INSTANTIATION_DIR)
        print "{0} \n".format(noise_file)
        time2 = self.get_pcap_timestamp(noise_file)

        print "{0}\n".format(FILE_NAME)
        # shift time of noise pcap file
        command = "editcap -t {0} {1} {2}noise.pcap;\n".format(time1-time2, noise_file, CR_DIR)
        # merge pcap files
        command += "mergecap {0}noise.pcap {0}attack.pcap -w {0}{1};\n".format(CR_DIR, FILE_NAME)
        # clean folder 
        command += "rm -f {0}noise.pcap; rm -f {0}attack.*; \n".format(CR_DIR)
        os.system(command)

a = PcapCreation()
a.merge_pcap()
