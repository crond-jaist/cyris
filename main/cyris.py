#!/usr/bin/python

#############################################################################
# Classes related to the CyRIS main functions
#############################################################################

# External imports
import time
import os
import subprocess
import yaml
import sys
from collections import defaultdict
import socket
import random
from datetime import datetime, timedelta
import fcntl            # for atomic file writing
import getopt
import logging
import re
import urllib
from cyvar import CyVarBase, CyVarForm, CyVarBox

# Internal imports.
from modules import SSHKeygenHostname, EmulateAttacks, ManageUsers, InstallTools, BaseImageLaunch, EmulateMalware, GenerateTrafficCaptureFiles, ModifyRuleset, CopyContent, ExecuteProgram
from entities import Host, Guest, CloneGuest, CloneSubnetwork, CloneInstance, CloneHost, CloneSetting
from clone_environment import VMClone
import parse_config
from check_description import check_description
from storyboard import Storyboard

# AWS support
import boto3
import json
from aws_sg import create_security_group, edit_ingress, describe_security_groups
from aws_instances import create_instances, describe_instance_status, stop_instances,publicIp_get,clone_instances
from aws_image import create_img, describe_image
from aws_info import edit_tags, get_info

# Set global logging level
#logging.basicConfig(level=logging.DEBUG, format='* %(levelname)s: %(filename)s: %(message)s')
logging.basicConfig(format='* %(levelname)s: %(filename)s: %(message)s')


#############################################################################
# Constants.
#############################################################################

DEBUG = False
DEBUG2 = False

# Whether to try to destroy a cyber range when an error occurs
DESTROY_ON_ERROR = False

# Settings for parallel ssh and scp
PSSH_TIMEOUT = 300     # Seconds until the connections will be timed out
PSSH_CONCURRENCY = 50  # Maximum number of concurrent connections
PSCP_CONCURRENCY = 50  # Maximum number of concurrent connections

# Settings for check ssh function: total timeout and for one try
CHECK_SSH_TIMEOUT_TOTAL = 120 # Longer for AWS: 300?
CHECK_SSH_TIMEOUT_ONCE = 5    # Longer for AWS: 60?
CHECK_SSH_CONNECTIVITY_INDICATOR = "Permission denied"

# Master node's account.
MSTNODE_ACCOUNT = ""
MSTNODE_MGMT_ADDR = ""
BASEIMG_ROOT_PASSWD = "theroot"

# The list contains response output of system calls.
RESPONSE_LIST = []

# Testing variables.
TIME_MEASURE = True

# Output file name templates
RANGE_NOTIFICATION_FILE = "range_notification-cr"
RANGE_DETAILS_FILE = "range_details-cr"

# The values below are used for sending email notifications regarding cyber range creation
# (if USER_EMAIL is defined in the CyRIS configuration file)
# Note: This feature is not yet fully supported, use at your own risk 
EMAIL_SERVER = "server_hostname"
EMAIL_SENDER = "Sender Name <sender@domain>"
EMAIL_ACCOUNT = "sender@domain"
EMAIL_PASSWD = "email_password"

# Default values for some fields
# TODO: Should be selected based on the guest OS
DEFAULT_PACKAGE_MANAGER = "yum"

INSTANTIATION_DIR = "instantiation"
creation_datetime = -1

#############################################################################
class CyberRangeCreation():

    range_details_filename = None
    range_notification_filename = None

    #########################################################################
    # Init function contains global variables
    def __init__(self, argv):

        global DESTROY_ON_ERROR

        # Get global parameters from CONFIG file.
        global ABS_PATH
        global CR_DIR
        global GW_MODE
        global GW_ACCOUNT
        global GW_MGMT_ADDR
        global GW_INSIDE_ADDR
        global USER_EMAIL

        global DEBUG
        global creation_datetime
        creation_datetime = datetime.now()

        # Parse options and command-line arguments
        try:
            opts, args = getopt.getopt(argv, "hdv", ["help", "destroy-on-error", "verbose"])
        except getopt.GetoptError as err:
            print "* ERROR: cyris: Command-line argument error: %s" % (str(err))
            self.usage()
            quit(-1)

        # First we deal with options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                self.usage()
                quit(-1)
            elif opt in ("-d", "--destroy-on-error"):
                print "* INFO: cyris: In case of error, will try to destroy cyber range."
                DESTROY_ON_ERROR = True;
            elif opt in ("-v", "--verbose"):
                DEBUG = True
                print "* DEBUG: cyris: Debug mode enabled."

        # Then with command-line arguments
        if len(args)<2:
            print "* ERROR: cyris: Not enough command-line arguments."
            self.usage()
            quit(-1)

        # Get name of description file
        self.training_description = args[0]

        print "#########################################################################"
        print "%s: Cyber Range Instantiation System" % (self.get_version_string())
        print "#########################################################################"

        # Get global parameters from CONFIG file.
        print "* INFO: cyris: Parse the configuration file."
        ABS_PATH, CR_DIR, GW_MODE, GW_ACCOUNT, GW_MGMT_ADDR, GW_INSIDE_ADDR, USER_EMAIL = parse_config.parse_config(args[1])
        # Check that parse was successful
        if ABS_PATH == False:
            self.creation_log_file = "" # Needed for handle_error() to work correctly
            self.handle_error()
            quit(-1)

        #self.training_description = sys.argv[1]
        self.hosts = []
        self.guests = []
        self.clone_setting = None
        # directory containing coressponding config files
        self.directory = ""
        # Absolute path of logs of the execution.
        self.global_log_file = "{0}logs/cr_creation.log".format(ABS_PATH)
        self.time_measure_file = "{0}logs/cr_creation_time.txt".format(ABS_PATH)

        # Absolute path of file which records ip addresses of current running base images
        self.cur_running_ipaddr_file = "{0}settings/running_ipaddr.txt".format(ABS_PATH)

        self.global_log_message = ""
        self.global_time_message = ""
        i = creation_datetime
        self.global_log_message += "\n##########################################################################"
        self.global_log_message += "\n##########################################################################"
        self.global_log_message += "\nCyber range creation {0}\n".format(i.strftime('%Y/%m/%d %H:%M:%S'))
        self.global_time_message += "\n##########################################################################"
        self.global_time_message += "\n##########################################################################"
        self.global_time_message += "\nCyber range creation {0}\n".format(i.strftime('%Y/%m/%d %H:%M:%S'))

        # a list of config files created in individual hosts during cloning part
        self.setup_fwrule_file = ""                     # for setting up fwrule on each vms
        self.setup_dfgw_file = ""                       # for setting up default gateways on each vms
        self.create_bridges_file = ""                   # for creating bridges of each cyber range instance
        self.entry_points_file = ""                     # for individual hosts to check ping their entry points after vms are created
        self.clone_file = ""                            # for cloning process
        self.create_vms_file = ""                       # for creating vms from base images
        self.create_tunnels_file = ""                   # for creating ssh tunnels for entry points
        self.create_entry_accounts_file = ""            # for creating random accounts and passwds on entry points
        self.install_wordpress_file = ""                # for installing wordpress on webservers (only needed in level 2)
        self.destruction_file = ""                      # for destructing cyber range on individual hosts
        self.pssh_file = ""                             # for containing a list of hosts for parallel-ssh
        self.pscp_file = ""                             # for containing a list of hosts for parallel-scp
        self.prepare_prg_afcln_file = ""                # for copying post-cloned programs on other hosts
        self.install_prg_afcln_file = ""                # for executing programs on individual guest after being cloned
        self.creation_status_file = ""                  # for returning the creation process result: success or failure
        self.creation_log_file = ""                     # for recording log of the creation process

        if GW_MODE:
            if GW_ACCOUNT is None or GW_MGMT_ADDR is None or GW_INSIDE_ADDR is None:
                print "* ERROR: cyris: If GW_MODE is enabled in the config file, then GW_ACCOUNT, GW_MGMT_ADDR and"
                print "         GW_INSIDE_ADDR must also be assigned valid values."

                self.handle_error()
                quit(-1)


    #########################################################################
    # Determine software version by reading it from the CHANGES file
    def get_version_string(self):

        # Set program name and version file
        PROGRAM_NAME = "CyRIS"
        CHANGES_FILENAME = "../CHANGES"

        # Get program directory
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # Read version string from a version file
        version_filename = str(dir_path) + "/" + CHANGES_FILENAME
        version_string = ""
        try:
            version_file = open(version_filename)
            version_expr = "{0} v".format(PROGRAM_NAME)
            for line in version_file:
                if re.match(version_expr, line):
                    version_string = line.rstrip("\n")
                    break
        except IOError, e:
            print e

        if not version_string:
            print "* WARNING: cyris: Unable to determine version number."
            version_string = PROGRAM_NAME

        return version_string

    #########################################################################
    # Check if prerequisites are met
    # FIXME: Should call error handling function so that execution is terminated
    def check_prerequsites(self):

        # TODO: Check that OS is Ubuntu?!

        # Check for sudo permission
        command = "timeout --foreground 2 sudo id"
        return_value = os.system("{0} > /dev/null 2>&1".format(command))
        exit_status = os.WEXITSTATUS(return_value)
        if exit_status != 0:
            print "* ERROR: cyris: Passwordless sudo execution is not enabled."
            self.handle_error()
            quit(-1)

        # TODO: Check that SSH keys are defined?!

        # TODO: Check if Internet access is available?!

    #########################################################################
    # Given a file with full path, separate the file name and the absolute path
    def separateNamePath(self, string):
        list_elements = string.split("/")
        name = list_elements[-1]
        path = ""
        list_elements.pop()
        for i in list_elements:
            path += "{0}/".format(i)
        return name, path
    #########################################################################
    # Decide the last bit of the base image's IP address to make sure that no running
    # base images have the same IP address.
    def add_basevm_ipaddr(self, last_bit):
        try:
            # If the logs/running_ipaddr.txt doesn't exist before, it means no base images is running.
            # Therefore, it needs only to create the file, and write the last_bit down.
            if not os.path.isfile(self.cur_running_ipaddr_file):
                with open(self.cur_running_ipaddr_file, "w") as f:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    f.write("{0}\n".format(str(last_bit)))
                    fcntl.flock(f, fcntl.LOCK_UN)
                return last_bit
            # Else if the file exists.
            else:
                with open(self.cur_running_ipaddr_file, "r+") as f:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)

                    # Original code; should work now as every written number is followed by EOL
                    cur_lb_list = f.readlines()

                    # Replacement code for old case when empty lines appeared in the file
                    # Make list of lines in file 'f' after stripping whitespaces from end of string
                    #cur_lb_list = (line.rstrip() for line in f)
                    # Make list of lines that are _not_ empty strings
                    #cur_lb_list = list(line for line in cur_lb_list if line)

                    # Check if the file is empty.
                    if len(cur_lb_list) == 0:
                        f.write("{0}\n".format(str(last_bit)))
                        fcntl.flock(f, fcntl.LOCK_UN)
                        return last_bit
                    # If the file isn't empty.
                    else:
                        # Read current last bits in the file.
                        # Current checking position in the file.
                        i = 0
                        # Iterate the current addr list to check if the last bit has been existed.
                        while (i < len(cur_lb_list)):
                            #if DEBUG:
                            #    print "* DEBUG: cyris: Current element in ipaddr list:", int(cur_lb_list[i])
                            if int(cur_lb_list[i]) == last_bit:
                                i = 0
                                last_bit += 1
                            else:
                                i += 1
                        f.write("{0}\n".format(str(last_bit)))
                        fcntl.flock(f, fcntl.LOCK_UN)
                        return last_bit
        except IOError, e:
            print "* ERROR: cyris: IOError:", e
            self.handle_error()
            quit(-1)
    #########################################################################
    # Parse information from the cyber range definition description to three
    # variables: self.hosts list, self.guests list, and self.cloneInfos list
    def parse_description(self, filename):
        try:
            with open(filename, "r") as f:
                doc = yaml.load(f)
        except yaml.YAMLError, exc:
            print "* ERROR: cyris: Issue with the cyber range description file: ", exc
            return

        # for each playbook in the training description
        for element in doc:
            if "host_settings" in element.keys():
                for i,h in enumerate(element["host_settings"]):
                    if DEBUG:
                        print "account: " + h["account"]
                    if i == 0:
                        global MSTNODE_ACCOUNT
                        global MSTNODE_MGMT_ADDR
                        MSTNODE_ACCOUNT = h["account"]
                        MSTNODE_MGMT_ADDR = h["mgmt_addr"]
                    host = Host(h["id"], h.get("virbr_addr"), h["mgmt_addr"], h["account"])
                    self.hosts.append(host)

            if "guest_settings" in element.keys():
                for i,g in enumerate(element["guest_settings"]):
                    # If user specifies ip_addr for the guest.
                    if "ip_addr" in g.keys():
                        ip_addr = g["ip_addr"]
                    # Else, CyRIS generates ip_addr for the guest using its own rules as below.
                    else:
                        # Assign last bit of IP addr for the guest, which is the sum of 100 and the guest's i.
                        last_bit = self.add_basevm_ipaddr(100 + i)
                        # Generate IP addr for the guest, which is 192.168.122.{last_bit}.
                        ip_addr = "192.168.122.{0}".format(last_bit)
                    # If user specifies tasks for the guest.
                    if "tasks" in g.keys():
                        tasks = g["tasks"]
                    else:
                        tasks = []
                    # If basevm_os_type defined
                    if "basevm_os_type" in g.keys():
                        basevm_os_type = g["basevm_os_type"]
                    else:
                        basevm_os_type = "centos.7"

                    guest = Guest(g["id"], ip_addr, BASEIMG_ROOT_PASSWD, g["basevm_host"], g.get("basevm_config_file"), basevm_os_type, g["basevm_type"], "", tasks)
                    self.guests.append(guest)

        if "clone_settings" in element.keys():
            range_id = element["clone_settings"][0]["range_id"]
            self.range_id = range_id # Save for future reference
            clone_host_list = []

            for host in element["clone_settings"][0]["hosts"]:
                # The 'host_id' of 'host' may contain a list of ids,
                # so we split the list if needed
                host_id_str = host["host_id"]
                host_id_list = []
                if "," in host_id_str:
                    host_id_list = host_id_str.replace(" ","").split(",")
                else:
                    host_id_list.append(host_id_str)
                for host_id in host_id_list:
                    instance_num = host["instance_number"]
                    # set network topology type
                    nw_type = host["topology"][0]["type"]
                    instance_list = []
                    for i in range(1, instance_num+1):
                        # Since each instance reuse the information of the guest, it's important to 
                        # recreate a clone_guest_list and clone_subnw_list  when creating a new instance.
                        clone_subnw_list = []
                        for subnetwork in host["topology"][0]["networks"]:
                            name = subnetwork["name"]
                            members = subnetwork["members"]
                            if "gateway" in subnetwork.keys():
                                gateway = subnetwork["gateway"]
                            else:
                                gateway = ""
                            clone_subnetwork = CloneSubnetwork(name, members, gateway)
                            clone_subnw_list.append(clone_subnetwork)
                        clone_guest_list = []
                        for guest in host["guests"]:
                            guest_id = guest["guest_id"]
                            number = guest["number"]
                            fw_rules = []
                            if Storyboard.FORWARDING_RULES in guest.keys():
                                has_fw_setup = True
                                for rule in guest[Storyboard.FORWARDING_RULES]:
                                    fw_rules.append(rule[Storyboard.RULE])
                            else:
                                has_fw_setup = False
                            if "entry_point" in guest.keys():
                                is_entry_point = True
                            else:
                                is_entry_point = False
                            # Create a list of clone_guest with size=number
                            for k in range(1, number+1):
                                for vm_guest in self.guests:
                                    if guest_id==vm_guest.getGuestId():
                                        os_type=vm_guest.getBasevmOSType()
                                #clone_guest = CloneGuest(guest_id, k, has_fw_setup, fw_rules, is_entry_point,os_type)
                                clone_guest = CloneGuest(guest_id, k, i, range_id,has_fw_setup, fw_rules, is_entry_point,os_type)
                                clone_guest_list.append(clone_guest)
                        instance = CloneInstance(i, clone_guest_list, clone_subnw_list)
                        instance_list.append(instance)

                    # Find host with same id in the hosts list and use it to initialize the CloneHost object
                    # We use a new object 'actual_host' because the object 'host' above may contain a list of host ids
                    actual_host = self.get_host_object(host_id)
                    clone_host = CloneHost(actual_host, instance_list)
                    clone_host_list.append(clone_host)
            self.clone_setting = CloneSetting(range_id, nw_type, clone_host_list)

        # Set basevm_name for guests
        for guest in self.guests:
            basevm_name = "{0}_cr{1}_base".format(guest.getGuestId(), self.clone_setting.getRangeId())
            guest.setBasevmName(basevm_name)

    #########################################################################
    # Return the host object associated to a host_id value
    def get_host_object(self, host_id):
        for host in self.hosts:
            if host_id == host.getHostId():
                return host
        return None

    #########################################################################
    # Return essential information of the host from host_id value
    def get_host(self, host_id):
        for host in self.hosts:
            if host_id == host.getHostId():
                host_mgmt_addr = host.getMgmtAddr()
                host_virbr_addr = host.getVirbrAddr()
                host_account = host.getAccount()
        return host_mgmt_addr, host_virbr_addr, host_account

    #########################################################################
    # Return essential information of the guest from guest_id value
    def get_guest(self, guest_id):
        for guest in self.guests:
            if guest.getGuestId() == guest_id:
                basevm_name = guest.getBasevmName()
                basevm_addr = guest.getBasevmAddr()
        return basevm_name, basevm_addr

    #########################################################################
    # Set names for directory and config files related to the being created cyber range
    def set_config_file_name(self):
        # Assign name for the directory.
        #self.directory = "{0}cyber_range/{1}/".format(ABS_PATH, self.clone_setting.getRangeId())
        self.directory = "{0}{1}/".format(CR_DIR, self.clone_setting.getRangeId())
        # Assign names for config files.
        self.setup_fwrule_file = "{0}setup_fwrule.sh".format(self.directory)
        self.setup_dfgw_file = "{0}setup_dfgw.sh".format(self.directory)
        self.create_bridges_file = "{0}create_bridges.sh".format(self.directory)
        self.entry_points_file = "{0}entry_points.txt".format(self.directory)
        self.clone_file = "{0}clone.sh".format(self.directory)
        self.create_vms_file = "{0}create_vm.sh".format(self.directory)
        self.create_tunnels_file = "{0}create_tunnels.sh".format(self.directory)
        self.create_entry_accounts_file = "{0}create_entry_accounts.sh".format(self.directory)
        self.install_wordpress_file = "{0}install_wordpress.sh".format(self.directory)
        self.destruction_file = "{0}destruct_cyberrange.sh".format(self.directory)
        self.pssh_file = "{0}pssh_hosts.txt".format(self.directory)
        self.pscp_file = "{0}pscp_hosts.txt".format(self.directory)
        self.prepare_prg_afcln_file = "{0}prepare_prg_afcln.sh".format(self.directory)
        self.install_prg_afcln_file = "{0}install_prg_afcln.sh".format(self.directory)
        self.creation_status_file = "{0}cr_creation_status".format(self.directory)
        self.creation_log_file = "{0}creation.log".format(self.directory)

    #########################################################################
    # Get commands for each base image from the cyber description file.
    def get_instantiation_commands(self, guest, basevm_type):
        # Command_list is for storing a list of commands that need to perform on the base image during the preparation phase.
        # Post_execute_program_list is a list programs that need to perform on the cloned guests after the cloning phase.
        command_list = []
        post_execute_program_list = []
        guest_addr = guest.getBasevmAddr()
        guest_passwd = guest.getRootPasswd()
        guest_os_type = guest.getBasevmOSType()
        host_mgmt_addr, host_virbr_addr, host_account = self.get_host(guest.getBasevmHost())
        command = ""
        sepchar = ","
        varbox = CyVarBox()
        # from mail_template
        varbox.entry1("range_id", self.clone_setting.getRangeId())
        varbox.entry1("instance_count",self.clone_setting.getTotalInstanceNum())
        varbox.entry1("guest_id", guest.getGuestId())
        varbox.entry1("creation_datetime",creation_datetime.strftime('%Y%m%dT%H%M%S'))
        varbox.entry1("creation_date",creation_datetime.strftime('%Y%m%d'))
        varbox.entry1("creation_time",creation_datetime.strftime('%H%M%S'))

        # Parse commands from tasks if it is not empty.
        if len(guest.getTasks()) != 0:
            for task in guest.getTasks():
                if "add_account" in task.keys():
                    for account in task["add_account"]:
                        new_account = account["account"]
                        new_passwd = account["passwd"]
                        if Storyboard.FULL_NAME in account.keys():
                            full_name = account[Storyboard.FULL_NAME]
                        else:
                            full_name = ""

                        command = ManageUsers(guest_addr, ABS_PATH).add_account(new_account, new_passwd, full_name, guest_os_type, basevm_type)
                        command_list.append(command)

                if "modify_account" in task.keys():
                    for account in task["modify_account"]:
                        old_account = account["account"]
                        if "new_account" in account:
                            new_account = account["new_account"]
                        else:
                            new_account = "null"
                        if "new_passwd" in account:
                            new_passwd = account["new_passwd"]
                        else:
                            new_passwd = "null"
                        command = ManageUsers(guest_addr, ABS_PATH).modify_account(old_account, new_account, new_passwd, guest_os_type, basevm_type)
                        command_list.append(command)
                        #command = SSHKeygen(guest.getBasevmAddr(), new_passwd, ABS_PATH).command()
                        #command_list.append(command)
                        # Update guest's root password.
                        if old_account == "root" and new_passwd != "null":
                            #print new_passwd
                            guest_passwd = new_passwd
                            guest.setRootPasswd(new_passwd)

                if "install_package" in task.keys():
                    installTools = InstallTools(guest_addr, "root", ABS_PATH)
                    for package in task["install_package"]:
                        if "package_manager" in package.keys():
                            package_manager = package["package_manager"]
                        else:
                            package_manager = DEFAULT_PACKAGE_MANAGER;
                        package_name = package["name"]
                        version = ""
                        if "version" in package.keys():
                            version = package["version"]
                        command = installTools.package_install_command(package_manager, package_name, version, guest_os_type, basevm_type)
                        command_list.append(command)

                if "install_source" in task.keys():
                    installTools = InstallTools(guest_addr, "root", ABS_PATH)
                    for source in task["source_install"]:
                        chdir = source["chdir"]
                        compiler = source["compiler"]
                        command = installTools.source_install_command(chdir, compiler)
                        command_list.append(command)

                if "emulate_attack" in task.keys():
                    for attack in task["emulate_attack"]:
                        attack_type = attack["attack_type"]
                        target_account = attack["target_account"]
                        attempt_number = attack["attempt_number"]
                        attack_time = "none"
                        if "attack_time" in attack.keys():
                            attack_time = attack["attack_time"]
                        command = EmulateAttacks(attack_type, guest_addr, target_account, attempt_number, attack_time, ABS_PATH, basevm_type).command()
                        command_list.append(command)

                if "emulate_traffic_capture_file" in task.keys():
                    for fi in task["emulate_traffic_capture_file"]:
                        path_name = fi["file_name"]
                        file_name, file_path = self.separateNamePath(path_name)
                        attack_type = fi["attack_type"]
                        noise_level = fi["noise_level"]
                        generateTraffic = GenerateTrafficCaptureFiles(host_virbr_addr, guest_addr, guest_passwd, attack_type, noise_level, file_path, file_name, ABS_PATH, self.directory, basevm_type)
                        if attack_type == "ssh_attack":
                            attack_source = fi["attack_source"]
                            command = generateTraffic.ssh_attack(host_account, attack_source, 50)
                            command_list.append(command)
                        if attack_type == "dos_attack":
                            attack_source = fi["attack_source"]
                            if "attack_port" in fi.keys():
                                attack_port = fi["attack_port"]
                            else:
                                attack_port = "80"
                            command = generateTraffic.dos_attack(attack_source, attack_port)
                            command_list.append(command)
                        if attack_type == "ddos_attack":
                            command = generateTraffic.ddos_attack()
                            command_list.append(command)

                if "emulate_malware" in task.keys():
                    for malware in task["emulate_malware"]:
                        name = malware["name"]
                        if malware["mode"] == "dummy_calculation":
                            mode = "calculation"
                            crspd_option = malware["cpu_utilization"]
                        if malware["mode"] == "port_listening":
                            mode = "port_listening"
                            crspd_option = malware["port"]
                        command = EmulateMalware(guest_addr, name, mode, crspd_option, ABS_PATH, basevm_type, guest_os_type).command()
                        command_list.append(command)

                if "copy_content" in task.keys():
                    for content in task["copy_content"]:
                        src = content["src"]
                        dst = content["dst"]
                        command = CopyContent(src, dst, guest_addr, guest_passwd, ABS_PATH, guest_os_type, basevm_type).command()
                        command_list.append(command)

                # Since this task requires guest's password, it's mandatory to specify this task after any task related 
                # to changing account root's password.
                if "execute_program" in task.keys():
                    for program in task["execute_program"]:
                        program_name = program["program"]
                        interpreter = program["interpreter"]
                        args = "none"
                        if "args" in program.keys():
#                            args = program["args"]
                            args = urllib.quote(program["args"])
                        # If "execute_time" tag isn't included or is specified as "before_clone", then the command will be added
                        # to the command_list. Otherwise, the program will be added to the post_execute_program_list
                        execidtail = "noname"
                        if "id" in program:
                            execidtail = program["id"]
                        if 1:
                            actargs = varbox.safe_project_URLchunks(args)
                        else:
                            actargs = args

                        if "execute_time" not in program.keys() or program["execute_time"] == "before_clone":
                            command = ExecuteProgram(program_name, interpreter, actargs, guest_addr, guest_passwd, self.creation_log_file, ABS_PATH, guest_os_type, guest.getGuestId()+sepchar+execidtail).command()
                            #command = ExecuteProgram(program_name, interpreter, args, guest_addr, guest_passwd, self.creation_log_file, ABS_PATH, guest_os_type).command()
                            command_list.append(command)
                        else:
                            # change ExecuteProgram param4 to guest_addr from "" ,
                            # because run_program.py's sys.argv are ignore "".
                            program = ExecuteProgram(program_name, interpreter, actargs, "$TARGET", guest_passwd, self.creation_log_file, ABS_PATH, guest_os_type, "$COMTAGPREFIX"+sepchar+execidtail)
                            #program = ExecuteProgram(program_name, interpreter, args, guest_addr, guest_passwd, self.creation_log_file, ABS_PATH, guest_os_type)
                            post_execute_program_list.append(program)

                if "firewall_rules" in task.keys():
                    for ruleset in task["firewall_rules"]:
                        ruleset_file = ruleset["rule"]
                        command = ModifyRuleset(guest_addr, ruleset_file, ABS_PATH, basevm_type, guest_os_type).command()
                        command_list.append(command)

        return command_list, post_execute_program_list

    #########################################################################
    # Generate commands for shuting down and undefining base images
    def shut_down_baseimg(self):
        shutdown_command = ""
        for guest in self.guests:
            shutdown_command += "virsh --quiet shutdown {0} > /dev/null;".format(guest.getBasevmName())
            shutdown_command += "virsh --quiet undefine {0} > /dev/null;".format(guest.getBasevmName())
            # Only run the command below if the running ipaddress file exists
            if os.path.isfile(self.cur_running_ipaddr_file):
                shutdown_command += "sed -i '/{0}/d' {1};".format(guest.getAddrLastBit(), self.cur_running_ipaddr_file)
        return shutdown_command

    #########################################################################
    # Summary commands lists for all base images into a dictionary <guest_id>:<command_list>
    def cyberrange_instantiation_commands(self, basevm_type):
        # Cmd_bfcln is a list of commands for each base vm that need to be performed before the clone phase.
        # Prg_afcln is a list of programs for each base vm that need to be performed after the clone phase,
        # for each individual cloned guest.
        dict_guest_cmd_bfcln = defaultdict(list)
        dict_guest_prg_afcln = defaultdict(list)
        for guest in self.guests:
            dict_guest_cmd_bfcln[guest.getGuestId()], dict_guest_prg_afcln[guest.getGuestId()] = self.get_instantiation_commands(guest, basevm_type)

        return dict_guest_cmd_bfcln, dict_guest_prg_afcln

    #########################################################################
    # Execute shell commands
    def execute_command(self, filename, command):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with open(filename, "a") as myfile:
            for line in p.stdout.readlines():
                myfile.write("-- Execute shell command:\n")
                myfile.write(line)
                myfile.write("\n")

    def os_system(self, filename, command):
        # Make sure the command is executed even if no filename is provided for the log file
        if filename:
            return_value = os.system("{0} >> {1} 2>&1".format(command, filename))
        else:
            return_value = os.system("{0} >> /dev/null".format(command))
        exit_status = os.WEXITSTATUS(return_value)

        if exit_status != 0:
            print "* ERROR: cyris: Issue when executing command (exit status = %d):" % (exit_status)
            print "  %s" % (command)
            print "  Check the log file for details: %s" % (self.creation_log_file)
            self.handle_error()
            quit(-1)
        else:
            global RESPONSE_LIST
            RESPONSE_LIST.append(exit_status)

    #########################################################################
    # Transmit information about cloning part in yaml file, send it to module 
    # class to create script 'instantiation/vm_clone/create_bridges.sh' and
    # get the commands back
    def clone_vm_commands(self, dict_guest_prg_afcln, basevm_type):

        # This function is to check and generate new ports for current cyber range instances
        used_port_list = []           # Contains a set of used ports for previous cyber range instances
        process_list = [] 
        p = subprocess.Popen("ps -aux | grep 'ssh -f -L \| {0}@localhost'".format(MSTNODE_ACCOUNT), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
        for line in p.stdout.readlines(): 
            process_list.append(line) 
        nfields = len(process_list[0].split()) - 1 
        for line in process_list: 
            for element in line.split(None, nfields): 
                if "0.0.0.0" in element: 
                    used_port = element.split(":")[1] 
                    used_port_list.append(used_port)

        if DEBUG2: print("* DEBUG: cyris: clone_vm_commands: INITIAL: used_port_list={}".format(used_port_list))

        # Generate fresh ports for entry points
        ## Generate a list with ports between a minimum and maximum value (both inclusive)
        MIN_PORT_NO = 60000
        MAX_PORT_NO = 65000
        fresh_port_list = range(MIN_PORT_NO, MAX_PORT_NO+1)
        if DEBUG2: print("* DEBUG: cyris: clone_vm_commands: INITIAL: fresh_port_list={}".format(fresh_port_list))
        ## Transform port lists to sets to "subtract" used_port_list values,
        ## then transform the result back to a list
        fresh_port_list=list(set(fresh_port_list) - set(used_port_list))
        if DEBUG2: print("* DEBUG: cyris: clone_vm_commands: FILTERED: fresh_port_list={}".format(fresh_port_list))
        ## Shuffle port list, so that port numbers are used in a random order
        ## (note that shuffling is done in place)
        random.shuffle(fresh_port_list)
        if DEBUG2: print("* DEBUG: cyris: clone_vm_commands: SHUFFLED: fresh_port_list={}".format(fresh_port_list))

        # Set ports for entry points
        self.clone_setting.setCloneHostList(fresh_port_list)

        # Write yaml file with detailed information of the created cyber range
        self.range_details_filename = "{0}{1}{2}.yml".format(self.directory, RANGE_DETAILS_FILE, self.clone_setting.getRangeId())
        self.clone_setting.writeConfig(self.range_details_filename, basevm_type)

        # Pass parameters to the VMClone class
        vm_clone = VMClone(GW_MODE, GW_ACCOUNT, GW_INSIDE_ADDR, self.hosts, self.guests, self.clone_setting, self.creation_log_file, self.setup_fwrule_file, self.setup_dfgw_file, self.create_bridges_file, self.entry_points_file, self.clone_file, self.create_vms_file, self.create_tunnels_file, self.create_entry_accounts_file, self.install_prg_afcln_file, self.install_wordpress_file, self.destruction_file, self.directory, ABS_PATH)
        vm_clone.generate_initif()
        vm_clone.create_bridges()
        vm_clone.clone_vm()
        vm_clone.set_fwrule()
        vm_clone.set_dfgw()
        vm_clone.install_prg_afcln(dict_guest_prg_afcln)
        vm_clone.create_tunnel_entry_account(basevm_type)
        vm_clone.create_destruction_file()

    #########################################################################
    # Check SSH connectivity for access via given command
    def check_ssh_connectivity(self, check_command, if_addr):

        # Compute operation timeout
        crt_time = datetime.now()
        timeout_time = crt_time + timedelta(seconds=CHECK_SSH_TIMEOUT_TOTAL)
        if DEBUG:
            print "* DEBUG: cyris:       Initial time for SSH check:", crt_time
            print "* DEBUG: cyris:       Timeout time for SSH check:", timeout_time

        # Loop while current time is less than the timeout
        while datetime.now() < timeout_time:

            # Create a new process to execute command
            proc = subprocess.Popen(check_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            stdout,stderr = proc.communicate()

            # Check whether CHECK_SSH_CONNECTIVITY_INDICATOR string can be found
            if CHECK_SSH_CONNECTIVITY_INDICATOR not in stderr:
                if DEBUG: print "* DEBUG: cyris:       Check SSH connectivity to {0} => FAILURE".format(if_addr)
            else:
                if DEBUG: print "* DEBUG: cyris:       Check SSH connectivity to {0} => SUCCESS".format(if_addr)
                # Additional sleep seems to be required before successfully connecting
                time.sleep(CHECK_SSH_TIMEOUT_ONCE)
                return

        # This point is only reached on total timeout expiration or error
        print "* ERROR: cyris: Cannot connect to VM."
        if DEBUG:
            print "  Error on connect: %s" % stderr
        print "  Check the log file for details: %s" % (self.creation_log_file)
        self.handle_error()
        quit(-1)

    #########################################################################
    # Check whether all base VMs can be accessed via SSH
    def check_ssh_connectivity_to_basevms(self):
        if DEBUG: print "* DEBUG: cyris: Checking SSH connectivity for base VMs..."

        # Loop over all guests
        for guest in self.guests:

            if DEBUG: print "* DEBUG: cyris: - Checking base VM for guest '{0}' ({1})...".format(guest.getGuestId(), guest.getBasevmAddr())

            # Get interface address for this guest from address list
            if_addr = guest.getBasevmAddr()

            # Build command for checking SSH connectivity
            OPTIONS = "-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o ConnectTimeout={0}".format(CHECK_SSH_TIMEOUT_ONCE)
            check_command = "ssh {0} {1} ls".format(OPTIONS, if_addr)
            if DEBUG: print "* DEBUG: cyris:       Command: {0}".format(check_command)

            # Call function that does the actual check
            self.check_ssh_connectivity(check_command, if_addr)

    #########################################################################
    # Check whether all cloned machines in the cyber range can be accessed via SSH
    def check_ssh_connectivity_to_cr(self):
        if DEBUG: print "* DEBUG: cyris: Checking SSH connectivity for cyber range..."

        # Loop over all hosts
        for host in self.clone_setting.getCloneHostList():

            if DEBUG: print "* DEBUG: cyris: - Checking instances on host '{0}' ({1})...".format(host.getHostId(), host.getMgmtAddr())

            # Loop over all instances on a host
            for instance in host.getInstanceList():

                if DEBUG: print "* DEBUG: cyris:   + Checking instance #{0}...".format(instance.getIndex())

                # Loop over all cloned guests in an instance
                for clone in instance.getCloneGuestList():

                    if DEBUG: print "* DEBUG: cyris:     - Checking cloned guest '{0}'...".format(clone.getGuestId())

                    # Check whether clone has NICs
                    if clone.getNicAddrDict():

                        # Get first interface address for this guest from address list
                        if_addr = clone.getNicAddrDict().values()[0]

                        # Build command for checking SSH connectivity
                        OPTIONS_MGMT = "-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no"
                        OPTIONS_CR = OPTIONS_MGMT + " -o ConnectTimeout={0}".format(CHECK_SSH_TIMEOUT_ONCE)
                        check_command = "ssh {} {} 'ssh {} {} ls'".format(OPTIONS_MGMT, host.getMgmtAddr(), OPTIONS_CR, if_addr)
                        if DEBUG: print "* DEBUG: cyris:       Command: {0}".format(check_command)

                        # Call function that does the actual check
                        self.check_ssh_connectivity(check_command, if_addr)

                    else:
                        print "* WARNING: cyris: No NIC defined for cloned guest '{0}'.".format(clone.getGuestId())

    #########################################################################
    # Send email function (for KVM)
    def send_email(self, username):
        f = open("{0}main/mail_template".format(ABS_PATH), "r")
        contents = f.read()
        f.close()

        if "{instructor}" in contents:
            contents = contents.replace("{instructor}", username)
        if "{ID}" in contents:
            contents = contents.replace("{ID}", str(self.clone_setting.getRangeId()))
        if "{num_cr_instances}" in contents:
            contents = contents.replace("{num_cr_instances}\n", "- Total number of cyber range instances: {0}".format(self.clone_setting.getTotalInstanceNum()))
        information = ""
        instance_index = 1
        # Send email following the gateway mode.
        for host in self.clone_setting.getCloneHostList():
            for instance in host.getInstanceList():
                for host in self.hosts:
                    if instance.getEntryPoint().getHostId() == host.getHostId():
                        entry_point = instance.getEntryPoint()
                        # Write down information following the gateway mode.
                        if GW_MODE:
                            host_name = GW_MGMT_ADDR
                        # Write down information following the un-gateway mode.
                        else:
                            host_name = host.getMgmtAddr()
                        information += "\n\n- Cyber range instance #{0}:\n  Login: ssh {1}@{2} -p {3}\n  Password: {4}".format(instance_index, entry_point.getAccount(), host_name, entry_point.getPort(), entry_point.getPasswd())
                        instance_index += 1
                        break

        if "{info_cr_instances}" in contents:
            contents = contents.replace("{info_cr_instances}", information)

        self.range_notification_filename = "{0}{1}{2}.txt".format(self.directory, RANGE_NOTIFICATION_FILE, self.clone_setting.getRangeId())
        f = open(self.range_notification_filename, "w")
        f.write(contents)
        f.close()

        if USER_EMAIL is not None:
            # Prepare the sendemail command
            sendemail_command = "sendemail -f '" + EMAIL_SENDER + "' -t {0} -u 'Training Session #{1} Is Ready' -s " + EMAIL_SERVER + " -o tls=yes -o message-file={2}{3}{1}.txt -a {2}{4}{1}.yml -xu " + EMAIL_ACCOUNT + " -xp " + EMAIL_PASSWD

            # Copy the email to the gateway to send to user if it's the gateway mode.
            if GW_MODE:
                command = "scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}{1}{2}.txt {3}@{4}:/tmp; scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}{5}{2}.yml {3}@{4}:/tmp;".format(self.directory, RANGE_NOTIFICATION_FILE, self.clone_setting.getRangeId(), GW_ACCOUNT, GW_INSIDE_ADDR, RANGE_DETAILS_FILE)
                sendemail_command = sendemail_command.format(USER_EMAIL, self.clone_setting.getRangeId(),
                                                             "/tmp/",
                                                             RANGE_NOTIFICATION_FILE, RANGE_DETAILS_FILE)
                command += "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}@{1} \"{2}\"".format(GW_ACCOUNT, GW_INSIDE_ADDR, sendemail_command)

            # Send the email directly from the master node if it's the un-gateway mode.
            else:
                command = sendemail_command.format(USER_EMAIL, self.clone_setting.getRangeId(), self.directory,
                                                   RANGE_NOTIFICATION_FILE, RANGE_DETAILS_FILE)
            if DEBUG:
                print command
            print "* INFO: cyris: Send email notification."
            self.os_system(self.creation_log_file, command)

    #########################################################################
    # Send email function for AWS
    def aws_send_email(self, username, key_name):
        f = open("{0}main/mail_template".format(ABS_PATH), "r")
        contents = f.read()
        f.close()

        if "{instructor}" in contents:
            contents = contents.replace("{instructor}", username)
        if "{ID}" in contents:
            contents = contents.replace("{ID}", str(self.clone_setting.getRangeId()))
        if "{num_cr_instances}" in contents:
            contents = contents.replace("{num_cr_instances}\n", "- Total number of cyber range instances: {0}".format(self.clone_setting.getTotalInstanceNum()))

        os_type = ''
        for guest in self.guests:
            if guest.getBasevmOSType() in ['amazon_linux', 'amazon_linux2', 'red_hat']:
                os_type = 'ec2-user'
            elif guest.getBasevmOSType() in ['ubuntu_16', 'ubuntu_18', 'ubuntu_20']:
                os_type = 'ubuntu'
            else:
                os_type = 'xxx'

        information = ""
        instance_index = 1
        for host in self.clone_setting.getCloneHostList():
            for instance in host.getInstanceList():
                information += "\n\n- Cyber range instance #{0}:".format(instance.getIndex())
                for clone_guest in instance.getCloneGuestList():
                    cloned_name = "{0}_cr{1}_{2}_{3}".format(clone_guest.getGuestId(), self.clone_setting.getRangeId(),instance.getIndex(),clone_guest.getIndex())
                    if_addr = clone_guest.getNicAddrDict().values()[0]
                    information += "\n  Guest name: {0}\n  Login: ssh -i {1}.pem {2}@{3}".format( cloned_name, key_name, os_type, if_addr)
                    instance_index += 1

        if "{info_cr_instances}" in contents:
            contents = contents.replace("{info_cr_instances}", information)

        self.range_notification_filename = "{0}{1}{2}.txt".format(self.directory, RANGE_NOTIFICATION_FILE, self.clone_setting.getRangeId())
        f = open(self.range_notification_filename, "w")
        f.write(contents)
        f.close()

        if USER_EMAIL is not None:
            # Prepare the sendemail command
            sendemail_command = "sendemail -f '" + EMAIL_SENDER + "' -t {0} -u 'Training Session #{1} Is Ready' -s " + EMAIL_SERVER + " -o tls=yes -o message-file={2}{3}{1}.txt -a {2}{4}{1}.yml -xu " + EMAIL_ACCOUNT + " -xp " + EMAIL_PASSWD

            # Copy the email to the gateway to send to user if it's the gateway mode.
            if GW_MODE:
                command = "scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}{1}{2}.txt {3}@{4}:/tmp; scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}{5}{2}.yml {3}@{4}:/tmp;".format(self.directory, RANGE_NOTIFICATION_FILE, self.clone_setting.getRangeId(), GW_ACCOUNT, GW_INSIDE_ADDR, RANGE_DETAILS_FILE)
                sendemail_command = sendemail_command.format(USER_EMAIL, self.clone_setting.getRangeId(),
                                                             "/tmp/",
                                                             RANGE_NOTIFICATION_FILE, RANGE_DETAILS_FILE)
                command += "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}@{1} \"{2}\"".format(GW_ACCOUNT, GW_INSIDE_ADDR, sendemail_command)

            # Send the email directly from the master node if it's the un-gateway mode.
            else:
                command = sendemail_command.format(USER_EMAIL, self.clone_setting.getRangeId(), self.directory,
                                                   RANGE_NOTIFICATION_FILE, RANGE_DETAILS_FILE)
            if DEBUG:
                print command
            print "* INFO: cyris: Send email notification."
            self.os_system(self.creation_log_file, command)



    def copy_base_images(self):
        command = ""
        for guest in self.guests:
            # Get the {absolute path}+{file_name} of base image and its config file.
            # Notice: here it assumes that base image and config file have the same name.
            # (config file has .xml extension).
            original_files = guest.getBasevmConfigFile()[:-4]
            # Get the name of config file.
            xml_config_file = "{0}.xml".format(guest.getGuestId())
            # Copy both base image and config file to new location.
            command += "cp {0}.xml {1}{2}; cp {0} {1}{3};".format(original_files, self.directory, xml_config_file, guest.getGuestId())

            # NOTE: The name of the file in which a guest base VM image is stored is given by getGuestId()
            #       However, the name of the VM itself, as registered in KVM, and the associated XML file
            #       are given by getBasevmName()

            # Replace original base vm name with new one as guest's ID.
            command += "sed -i 's#<name>.*#<name>{0}</name>#' {1}{2};".format(guest.getBasevmName(), self.directory, xml_config_file)
            # Replace original location of base image in config file with new one.
            command += "sed -i \"s#<source file=.*#<source file='{0}{1}'/>#\" {0}{2};".format(self.directory, guest.getGuestId(), xml_config_file)
            # Replace original mac addr with new one as guest' IP addr
            guest_last_bit = guest.getBasevmAddr().rsplit(".")[-1]
            # TODO: Really need different value for AWS? '52:54:00:b1:2b:{0}'
            command += "sed -i \"s#<mac.*#<mac address='52:54:00:f8:30:{0}'/>#\" {1}{2};".format(hex(int(guest_last_bit))[2:], self.directory, xml_config_file)
            # Set the basevm_config_file of guest to be the new one.
            guest.setBasevmConfigFile("{0}{1}".format(self.directory, xml_config_file))

        return command

    # Print usage information
    def usage(self):
        print "OVERVIEW: CyRIS: Cyber Range Instantiation System\n"
        print "USAGE: cyris.py [options] RANGE_DESCRIPTION CONFIG_FILE\n"
        print "OPTIONS:"
        print "-h, --help              Display help"
        print "-d, --destroy-on-error  In case of error, try to destroy cyber range"
        print "-v, --verbose           Display verbose messages for debugging purposes\n"

    #########################################################################
    # Main function.
    def main(self):

        # Check prerequisites
        print "* INFO: cyris: Check that prerequisite conditions are met."
        self.check_prerequsites()

        # Parse description
        print "* INFO: cyris: Parse the cyber range description."

        filename = self.training_description
        if check_description(self.training_description, CR_DIR) == False:
            self.handle_error()
            quit(-1)
        self.parse_description(filename)

        if DEBUG:
            print ABS_PATH, GW_MODE, GW_ACCOUNT, GW_MGMT_ADDR, GW_INSIDE_ADDR, USER_EMAIL
            print "MASTER NODE ACCOUNT: " + MSTNODE_ACCOUNT
            print "MASTER NODE MGMT ADDR: " + MSTNODE_MGMT_ADDR

        #####################################################################
        # Start time.
        if TIME_MEASURE:
            start = time.time()

        #####################################################################
        # Preparation work.

        print "* INFO: cyris: Perform the initial setup."

        ####### Set up names for config files #############
        self.set_config_file_name()

        ######## Prepare host files for parallel scp and ssh #########
        ssh_host_file = "{0}settings/{1}pssh_host.txt".format(ABS_PATH, self.clone_setting.getRangeId())
        scp_host_file = "{0}settings/{1}pscp_host.txt".format(ABS_PATH, self.clone_setting.getRangeId())

        # Get the IP address of the current host
        crt_host_ipaddr=socket.gethostbyname(socket.gethostname())
        if DEBUG: print("Current host IP address: " + crt_host_ipaddr)

        # Create list of hosts that are to be skipped when doing scp
        hosts_to_skip_for_scp = ["localhost", "127.0.0.1"]
        hosts_to_skip_for_scp.append(crt_host_ipaddr)
        if DEBUG: print("Host addresses for which to skip pscp before cloning: {}".format(hosts_to_skip_for_scp))

        # Open files with truncation, so that any potential incorrect value is overwritten
        with open(ssh_host_file, "w+") as pssh, open(scp_host_file, "w+") as pscp:
            for host in self.hosts:
                # Prepare the list of hosts to which parallel scp should be done by
                # checking whether the target is different from the current host
                # NOTE: The CyRIS user guide says that the first host in the description file
                # is considered to be "master host", hence one could also check if the current
                # host is the master (first) host, and not copy files to itself
                if not host.getMgmtAddr() in hosts_to_skip_for_scp:
                    #logging.debug("Target '{0}' is different from current host ({1}) => do pscp".format(host.getMgmtAddr(), crt_host_ipaddr))
                    if DEBUG: print("Target '{}' ({}) is different from current host ({}) => do pscp before cloning".format(host.getHostId(), host.getMgmtAddr(), crt_host_ipaddr))
                    pscp.write("{0}:{1} {2}\n".format(host.getMgmtAddr(), 22, host.getAccount()))
                else:
                    #logging.debug("Target '{0}' is same with current host ({1}) => skip pscp".format(host.getMgmtAddr(), crt_host_ipaddr))
                    if DEBUG: print("Target '{}' ({}) is same with the current host ({}) => skip pscp before cloning".format(host.getHostId(), host.getMgmtAddr(), crt_host_ipaddr))

                # Prepare list of hosts to which parallel ssh should be done
                pssh.write("{0}@{1}:{2}\n".format(host.getAccount(), host.getMgmtAddr(), 22))

        # Prepare a generic parallel-ssh command
        parallel_ssh_command = "parallel-ssh -O StrictHostKeyChecking=no -O UserKnownHostsFile=/dev/null -i -h {0} -t {1} -p {2} -x '-tt'".format(ssh_host_file, PSSH_TIMEOUT, PSSH_CONCURRENCY)

        ######## Create directory on individual hosts #########
        command_to_run = "mkdir -p {0}; mkdir {0}images;".format(self.directory)
        command = "{0} \"{1}\"".format(parallel_ssh_command, command_to_run)

        # Run command
        # TODO: Should use os_system function instead of calling os.system directly?!
        if DEBUG:
            print command
            return_value = os.system(command)
        else:
            return_value = os.system("{0} > /dev/null".format(command))
        #self.os_system(self.creation_log_file, command)

        exit_status = os.WEXITSTATUS(return_value)
        if exit_status != 0:
            print "* ERROR: cyris: Issue when creating the directory '%s'." % (self.directory)
            print "  A cyber range with the same id may already exist (or authentication error)."
            is_fatal = True
            self.handle_error(is_fatal)
            quit(-1)

        ######## Deal with different VM types #################
	basevm_type = "kvm"
	for guest in self.guests:
	    if guest.basevm_type == "aws":
		basevm_type = "aws"
                break

        # Deal with KVM
	if basevm_type == "kvm":
	    ######## Copy base images to the directory ##########
	    print "* INFO: cyris: Copy the base images."
	    command = self.copy_base_images()
	    if DEBUG:
		print command
	    self.os_system(self.creation_log_file, command)

	    ######## Start up base images ##########
	    print "* INFO: cyris: Start the base VMs."
	    for guest in self.guests:
		command = BaseImageLaunch(guest.getBasevmConfigFile(), guest.getBasevmName(), ABS_PATH).command()
		self.os_system(self.creation_log_file, command)

	    print "* INFO: cyris: Check that the base VMs are up."
	    self.check_ssh_connectivity_to_basevms()

	    ######## SSH-copy-id and add default gw #########
	    print "* INFO: cyris: Prepare the base VMs for setup."
	    for guest in self.guests:
		# ssh-cp-id and setup hostname to basevm
		command = SSHKeygenHostname(guest.getBasevmAddr(), guest.getRootPasswd(), guest.getGuestId(), MSTNODE_ACCOUNT, ABS_PATH, guest.basevm_os_type).command()
		with open(self.creation_log_file, "a") as myfile:
                    myfile.write("-- Setup SSH keys command:\n")
                    myfile.write(command.getCommand())
                    myfile.write("\n")
		if DEBUG:
		    print command.getCommand()

		self.os_system(self.creation_log_file, command.getCommand())

		# add default gw
		# FIXME: Should use the virbr_addr value instead of the fixed IP below
		if guest.basevm_os_type in ('windows.7'):
		    add_gw_str= "route delete 0.0.0.0 mask 0.0.0.0"
		    command = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} \"{1}\"\n".format(guest.getBasevmAddr(), add_gw_str)
		    add_gw_str= "route add 0.0.0.0 mask 0.0.0.0 192.168.122.1"
		    command += "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} \"{1}\"\n".format(guest.getBasevmAddr(), add_gw_str)
		elif guest.basevm_os_type in ('centos.7'):
		    command = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} route add default gw 192.168.122.1".format(guest.getBasevmAddr())
		if DEBUG:
		    print command
		self.os_system(self.creation_log_file, command)

	# Deal with AWS
	elif basevm_type == "aws":
	    print "* INFO: cyris_aws: Base VM type is AWS"
	    client = boto3.client('ec2', region_name='us-east-1')

	    # create a security group
	    gName = gName = 'cr' + str(self.range_id) + '-sg'
	    status = create_security_group(client, gName)
	    if not status:
		print('* ERROR: cyris_aws:   Create Security Group => FAILURE')

	    # edit ingress
	    edit_ingress(client, gName)

	    # describe_security_groups get
            gNames = []
            gNames.append(gName)

            r = describe_security_groups(client, gNames)
            ipPermissions = r['SecurityGroups'][0]['IpPermissions']
            if ipPermissions:
                if DEBUG: print('* DEBUG: cyris_aws:   Edit Security Group Ingress => SUCCESS')
            else:
                print('* ERROR: cyris_aws:   Edit Security Group Ingress => FAILURE')
            #create instances
            ins_dic = {}
            for guest in self.guests:
                basevm_id = guest.getBasevmName()
                print "* INFO: cyris_aws: Start Create EC2 Instance as base VMs for guest '{0}'... ".format(basevm_id)
                numOfIns = 1
                ins_ids = create_instances(client, gNames, basevm_id, numOfIns, guest.basevm_os_type)
                ins_dic[basevm_id] = ins_ids

            ######## check the state whether is running ########
            print "* INFO: cyris_aws: Checking whether the Status of Instances are running..."
            for guest in self.guests:
                basevm_id = guest.getBasevmName()
                ins_ids =  ins_dic[basevm_id]
                print "* INFO: cyris_aws: - Checking guest '{0}' EC2 Instance...".format(basevm_id)
                for i in range(20):
                    res = describe_instance_status(client, ins_ids)
                    if DEBUG: print "* DEBUG: cyris_aws:   Guest '{0}' EC2 Instance => {1}".format(basevm_id,res)
                    if res == 'running': break
                    time.sleep(5)

            ######## get IP ########
            print "* INFO: cyris: Check that the base VMs are up."
            for guest in self.guests:
                basevm_id = guest.getBasevmName()
                ipAddr = publicIp_get(client,ins_dic[basevm_id])
                guest.setBasevmAddr(ipAddr)

            self.check_ssh_connectivity_to_basevms()

        else:
            print('* ERROR: cyris: Unsupported base VM type')

        #####################################################################
        # Done preparation
        if TIME_MEASURE:
            done_prepare = time.time()
            start_install_guest = time.time()

        #####################################################################
        # Cyber range settings commands
        print "* INFO: cyris: Configure the base VMs for training."
        dict_guest_cmd_bfcln, dict_guest_prg_afcln = self.cyberrange_instantiation_commands(basevm_type)
        for guest in self.guests:
            print "* INFO: cyris: - Configure guest: %s" % (guest.getGuestId())
            # cyber range settings commands
            commands = dict_guest_cmd_bfcln[guest.getGuestId()]
            for command in commands:
                print "* INFO: cyris:   + Action: %s" % (command.getDescription())
                with open(self.creation_log_file, "a") as myfile:
                    if type(command.getCommand()) is list:
                        for i in command.getCommand():
                            myfile.write("-- Base VM configuration command:\n")
                            myfile.write(i)
                            myfile.write("\n")
                    else:
                        myfile.write("-- Base VM configuration command:\n")
                        myfile.write(command.getCommand())
                        myfile.write("\n")
                #self.execute_command(self.creation_log_file, command.getCommand())
                self.os_system(self.creation_log_file, command.getCommand())

        # Write range details file
        # NOTE: Here is too early, as IP addresses are not configured yet...
        #       Actually done in clone_vm_commands below
        #self.range_details_filename = "{0}{1}{2}.yml".format(self.directory, RANGE_DETAILS_FILE, self.clone_setting.getRangeId())
        #self.clone_setting.writeConfig(self.range_details_filename)

        #####################################################################
        # Done installing
        if TIME_MEASURE == True:
            done_install_guest = time.time()
            start_cloning = time.time()

        ######################################################################
        # Clone commands
        ######################################################################
        basevm_type = "kvm"
        for guest in self.guests:
            if guest.basevm_type == "aws":
                basevm_type = "aws"
                BASEVM_OS_TYPE = guest.basevm_os_type
                break

        ######################################################################
        ######## KVM cloning
        ######################################################################
        if basevm_type == "kvm":
            ######## execute self.clone_vm_commands() function (which links to class VMClone in modules.py  ######
            ####################### to create config files and get necessary information #########################
            self.clone_vm_commands(dict_guest_prg_afcln, basevm_type)

            ######## shutdown base images ###########
            print "* INFO: cyris: Shut down the base VMs before cloning."
            shutdown_command = self.shut_down_baseimg()
            self.os_system(self.creation_log_file, shutdown_command)

            # Check whether shutdown completed for all base VMs before distributing images
            if DEBUG: print "* DEBUG: cyris: Checking whether shutdown completed for all base VMs..."
            for guest in self.guests:
                if DEBUG: print "* DEBUG: cyris: - Checking guest '{0}' base VM...".format(guest.getGuestId())
                while (subprocess.check_output("virsh list --all ", shell=True).find(guest.getBasevmName()) != -1):
                    if DEBUG: print "* DEBUG: cyris:   Base VM '{0}' is still running => SLEEP".format(guest.getBasevmName())
                    time.sleep(2)
                if DEBUG: print "* DEBUG: cyris:   Base VM '{0}' was undefined => CONTINUE".format(guest.getBasevmName())

            ######## parallel distribute base images to hosts ###########
            print "* INFO: cyris: Distribute the base images for cloning."
            # Calculate distribute base images time
            if TIME_MEASURE == True:
                start_scp = time.time()
            # Check if the pscp file is empty. If yes, then there's no need for calling parallel-scp
            if os.stat(scp_host_file).st_size != 0:
                command = ""
                parallel_scp_command = "parallel-scp -O StrictHostKeyChecking=no -O UserKnownHostsFile=/dev/null -h {0} -p {1}".format(scp_host_file, PSCP_CONCURRENCY)
                for guest in self.guests:
                    # NOTE: The name of the file in which a guest base VM image is stored is given by getGuestId()
                    #       However, the name of the VM itself, as registered in KVM, and the associated XML file
                    #       are given by getBasevmName() -- See the 'copy_base_images' function
                    command += "{0} {1}{2}* {1} &\n".format(parallel_scp_command, self.directory, guest.getGuestId())
                command += "wait\n"
                if DEBUG:
                    print command
                # FIXME: Why is failure of this command not causing execution to end?
                # Idea: add some bash code to check exit status via "$?" and return -1 on error
                self.os_system(self.creation_log_file, command)

            if TIME_MEASURE == True:
                done_scp = time.time()

            ######## parallel do the clone phase on hosts ########
            print "* INFO: cyris: Start the cloned base images."
            # Calculate parallel clone phase
            if TIME_MEASURE == True:
                start_parallel_clone = time.time()

            # create bridges using the script 'instantiation/vm_clone/create_bridges.sh' that has been
            # created in the function clone_vm_commands
            clone_command = "chmod +x {0}; {0}; ".format(self.create_bridges_file)
            # execute clone.sh script
            clone_command += "chmod +x {0}; {0}; ".format(self.clone_file)
            # create tunnels
            clone_command += "chmod +x {0}; {0}; ".format(self.create_tunnels_file)
            if DEBUG:
                print clone_command
            self.os_system(self.creation_log_file, "{0} \"{1}\"".format(parallel_ssh_command, clone_command))

            ######## check if virtual machines are up #########
            print "* INFO: cyris: Wait for the cloned VMs to start."

            self.check_ssh_connectivity_to_cr()

            print "* INFO: cyris: Perform post-cloning setup of the VMs."

            print "* INFO: cyris: - Configure network settings"

            ######## set up forwarding rules for routing ########
            fw_command = "chmod +x {0}; {0};".format(self.setup_fwrule_file)
            if DEBUG:
                print fw_command
            self.os_system(self.creation_log_file, "{0} \"{1}\"".format(parallel_ssh_command, fw_command))
            if DEBUG:
                print "Forwarding rules for routing are set"

            ######## set up default gateway ########
            dfgw_command = "chmod +x {0}; {0};".format(self.setup_dfgw_file)
            if DEBUG:
                print dfgw_command
            self.os_system(self.creation_log_file, "{0} \"{1}\"".format(parallel_ssh_command, dfgw_command))
            if DEBUG:
                print "Default gateways on vms are set"

            ######## create entry accounts ###########
            cea_command = "chmod +x {0}; {0};".format(self.create_entry_accounts_file)
            if DEBUG:
                print cea_command
            self.os_system(self.creation_log_file, "{0} \"{1}\"".format(parallel_ssh_command, cea_command))
            if DEBUG:
                print "Entry point accounts are created"

            ######### Install programs after cloning ##########
            # Check if any after clone execution is needed for any of the guests
            after_clone_needed = False
            for guest in self.guests:
                if dict_guest_prg_afcln[guest.getGuestId()]:
                    after_clone_needed = True
                    break
            # If after clone execution is needed, proceed
            if after_clone_needed:
                print "* INFO: cyris: - Execute programs after cloning"
                # Install command.
                install_command = "chmod +x {0}; {0};".format(self.install_prg_afcln_file)
                if DEBUG: print install_command
                if DEBUG: print "* DEBUG: cyris:  + Run script %s" % (self.install_prg_afcln_file)
                for guest in self.guests:
                    program_names = [item.program for item in dict_guest_prg_afcln[guest.getGuestId()]]
                    print "* INFO: cyris:   + {}: {}".format(guest.getGuestId(), " ".join(list(map(str, program_names))))
                self.os_system(self.creation_log_file, "{0} \"{1}\"".format(parallel_ssh_command, install_command))
                if DEBUG: print "Post-cloning programs are installed"
            else:
                if DEBUG: print "No post-cloning program exists"

            ######### Logout root account for windows ##########
            for host in self.clone_setting.getCloneHostList():
                for instance in host.getInstanceList():
                    for clone_guest in instance.getCloneGuestList():
                        if clone_guest.getOsType().find("windows")!=-1:
                            print "* INFO: logout root account for windows"
                            command = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} tsdiscon 1".format(clone_guest.getNicAddrDict()["eth0"])
                            self.os_system(self.creation_log_file, command)

            #####################################################################
            # Decide the creation process succeeds by checking return values of
            # system calls in RESPONSE_LIST.
            fail_count = 0
            for value in RESPONSE_LIST:
                if value != 0:
                    fail_count += 1
            with open(self.creation_status_file, "w") as status:
                #if (fail_count)/len(RESPONSE_LIST) >= 0.25:
                if fail_count > 0:
                    creation_status = "FAILURE"
                    status.write("FAILURE\n")
                    self.global_log_message += "Creation result: FAILURE\n"
                else:
                    creation_status = "SUCCESS"
                    status.write("SUCCESS\n")
                    self.global_log_message += "Creation result: SUCCESS\n"

            ######## Create whole-controlled destruction file ########
            with open("{0}whole-controlled-destruction.sh".format(self.directory), "w+") as f:
                f.write("echo \"* INFO: cyris: Destroy cyber range with id {0} and clean up.\"\n".format(self.range_id))
                f.write("command_1=\"{0}\"\n".format(self.destruction_file))
                f.write("{0} \"${{command_1}}\" > /dev/null\n".format(parallel_ssh_command))
                f.write("command_2=\"rm -rf {0}\"\n".format(self.directory))
                f.write("{0} \"${{command_2}}\" > /dev/null\n".format(parallel_ssh_command))
                f.write("rm {0}; rm {1}\n".format(ssh_host_file, scp_host_file))
            self.os_system(self.creation_log_file, "chmod +x {0}whole-controlled-destruction.sh".format(self.directory))

            # Deal with errors first
            if creation_status == "FAILURE":
                self.handle_error()
                quit(-1)

            ######## Send detailed information to users ##############
            # If the status is success, then send notification to user.
            print "* INFO: cyris: Prepare range creation notification and details."
            self.send_email("user")

            #####################################################################
            # Done installing
            if TIME_MEASURE == True:
                done_parallel_clone = time.time()
                done_cloning = time.time()
                self.global_time_message += "\nPrepare time: {0}\n".format(done_prepare - start)
                self.global_time_message += "Install time: {0}\n".format(done_install_guest - start_install_guest)
                self.global_time_message += "Cloning time: {0}\n".format(done_cloning - start_cloning)
                self.global_time_message += "\tParallel scp time: {0}\n".format(done_scp - start_scp)
                self.global_time_message += "\tParallel cloning time: {0}\n".format(done_parallel_clone - start_parallel_clone)
                self.global_time_message += "Total time: {0}\n".format(done_cloning - start)
                self.global_log_message += "Creation time: {0}\n".format(done_cloning - start)
                with open(self.time_measure_file, "a") as time_log, open(self.global_log_file, "a") as cr_log:
                    fcntl.flock(time_log, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(cr_log, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    time_log.write(self.global_time_message)
                    cr_log.write(self.global_log_message)
                    fcntl.flock(time_log, fcntl.LOCK_UN)
                    fcntl.flock(cr_log, fcntl.LOCK_UN)

        #####################################################################
        ######## AWS cloning
        #####################################################################
        elif basevm_type == "aws":

            ########## shutdown base images ##########
            print "* INFO: cyris_aws: Stop the EC2 Instances before cloning."
            stop_ins_ids = []
            for k,v in ins_dic.items():
                stop_ins_ids += v
                stop_instances(client, stop_ins_ids)

            ########## check whether stop completed for all base VMs before distributing images ##########
            print "* INFO: cyris_aws: Checking whether stop completed for all EC2 Instances..."
            for guest in self.guests:
                basevm_id = guest.getBasevmName()
                ins_ids =  ins_dic[basevm_id]
                print "* INFO: cyris_aws: - Checking guest '{0}' base VM...".format(basevm_id)
                for i in range(20):
                    res = describe_instance_status(client, ins_ids)
                    if DEBUG: print "* DEBUG: cyris_aws:   Base VM '{0}' => '{1}'".format(guest.getBasevmName(), res)
                    if res == 'stopped': break
                    time.sleep(5)

            ########## parallel create AMI images on AWS ##########
            print "* INFO: cyris_aws: Create the AMI images for cloning."
            if TIME_MEASURE == True:
                start_scp = time.time()

            img_dic = {}
            for guest in self.guests:
                ami_name = guest.getBasevmName()
                img_id = create_img(client, ins_dic[ami_name][0], ami_name)
                img_dic[ami_name] = img_id

            ########## check whether the AMI images are available ##########
            print "* INFO: cyris_aws: Checking whether the created AMI images are available..."
            for guest in self.guests:
                img_id = img_dic[guest.getBasevmName()]
                for i in range(40):
                    res = describe_image(client, img_id)
                    if DEBUG: print "* DEBUG: cyris_aws:   AMI for '{0}' => '{1}'".format(guest.getBasevmName(), res)
                    if res == 'available': break
                    time.sleep(5)

            if TIME_MEASURE == True:
                done_scp = time.time()

            ########## parallel do the clone phase on AWS ##########
            print "* INFO: cyris_aws: Start the cloned Instances with created AMI images."
            if TIME_MEASURE == True:
                start_parallel_clone = time.time()

            key_name = 'TESTKEY'
            ins_dic = {}
            for host in self.clone_setting.getCloneHostList():
                for instance in host.getInstanceList():
                    for clone_guest in instance.getCloneGuestList():
                        for guest in self.guests:
                            if guest.getGuestId() == clone_guest.getGuestId():
                                basevmName = guest.getBasevmName()
                        cloned_name = "{0}_cr{1}_{2}_{3}".format(clone_guest.getGuestId(), self.clone_setting.getRangeId(),instance.getIndex(),clone_guest.getIndex())
                        img_id = img_dic[basevmName]
                        numOfIns = 1
                        ins_ids = clone_instances(client, gNames, key_name, cloned_name, numOfIns,img_id)
                        ins_dic[cloned_name] = ins_ids

            ########## check if EC2 Instances are running ##########
            print "* INFO: cyris_aws: Wait for the cloned instances to start."
            print "* INFO: cyris_aws: Checking whether the cloned instances are running..."
            for host in self.clone_setting.getCloneHostList():
                for instance in host.getInstanceList():
                    print "* INFO: cyris_aws: - Checking instance #{0}...".format(instance.getIndex())
                    for clone_guest in instance.getCloneGuestList():
                        #print "* DEBUG: cyris_aws: - Checking cloned guest '{0}'...".format(clone_guest.getGuestId())
                        for i in range(20):
                            cloned_name = "{0}_cr{1}_{2}_{3}".format(clone_guest.getGuestId(), self.clone_setting.getRangeId(),instance.getIndex(),clone_guest.getIndex())
                            ins_ids = ins_dic[cloned_name]
                            res = describe_instance_status(client,ins_ids)
                            if DEBUG: print "* DEBUG: cyris_aws:   Cloned Guest EC2 Instance '{0}' => {1}".format(cloned_name,res)
                            if res == 'running':
                                pub_IP_address = publicIp_get(client,ins_ids)
                                clone_guest.addNicAddrDict(int(instance.getIndex()),pub_IP_address)
                                break
                            time.sleep(5)

            self.check_ssh_connectivity_to_cr()

            ######## Send detailed information to users ##############
            # If the status is success, then send notification to user.
            print "* INFO: cyris: Prepare range creation notification and details."
            self.aws_send_email("user", key_name)

            # Write yaml file with detailed information of the created cyber range
            self.range_details_filename = "{0}{1}{2}.yml".format(self.directory, RANGE_DETAILS_FILE, self.clone_setting.getRangeId())
            self.clone_setting.writeConfig(self.range_details_filename, basevm_type)

            #####################################################################
            # Done installing
            if TIME_MEASURE == True:
                done_parallel_clone = time.time()
                done_cloning = time.time()
                self.global_time_message += "\nPrepare time: {0}\n".format(done_prepare - start)
                self.global_time_message += "Install time: {0}\n".format(done_install_guest - start_install_guest)
                self.global_time_message += "Cloning time: {0}\n".format(done_cloning - start_cloning)
                self.global_time_message += "\tParallel AMI create time: {0}\n".format(done_scp - start_scp)
                self.global_time_message += "\tParallel cloning time: {0}\n".format(done_parallel_clone - start_parallel_clone)
                self.global_time_message += "Total time: {0}\n".format(done_cloning - start)
                self.global_log_message += "Creation time: {0}\n".format(done_cloning - start)
                with open(self.time_measure_file, "a") as time_log, open(self.global_log_file, "a") as cr_log:
                    fcntl.flock(time_log, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(cr_log, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    time_log.write(self.global_time_message)
                    cr_log.write(self.global_log_message)
                    fcntl.flock(time_log, fcntl.LOCK_UN)
                    fcntl.flock(cr_log, fcntl.LOCK_UN)

        else:
            print('* ERROR: cyris: Unsupported base VM type')


        #####################################################################
        # Output summary
        print "-------------------------------------------------------------------------"
        print "* INFO: cyris: Cyber range creation status: SUCCESS"
        if TIME_MEASURE == True:
            print "  Total processing time: %.2f s" % (done_cloning - start)
            print "  Instantiation details: %s" % (self.range_details_filename)
            print "  Login notification: %s" % (self.range_notification_filename)
        print "-------------------------------------------------------------------------"

    # Handle execution error
    def handle_error(self, is_fatal=True):

        if not is_fatal:
            try:
                # Write status if file name is provided
                if self.creation_status_file:
                    with open(self.creation_status_file, "w") as status:
                        status.write("FAILURE\n")
                        self.global_log_message += "Creation result: FAILURE\n"

                # Write log if file name is provided
                if self.global_log_file:
                    with open(self.global_log_file, "a") as cr_log:
                        fcntl.flock(cr_log, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        cr_log.write(self.global_log_message)
                        fcntl.flock(cr_log, fcntl.LOCK_UN)
            except IOError, e:
                print "* ERROR: cyris: IOError:", e

        # Only run the command below if the running ipaddress file exists
        if not is_fatal and os.path.isfile(self.cur_running_ipaddr_file):
            erase_command = ""
            # Remove temporary address from file
            for guest in self.guests:
                erase_command += "sed -i '/{0}/d' {1};".format(guest.getAddrLastBit(), self.cur_running_ipaddr_file)
            self.os_system(self.creation_log_file, erase_command)

        # Destroy cyber range if needed
        if not is_fatal and DESTROY_ON_ERROR:
            print "* INFO: cyris: Execution error => try to destroy cyber range and clean up."

            # Try to destroy the cyber range by either executing the
            # whole-controlled-destruction script if it's been created,
            # or by deleting the whole directory otherwise.
            if os.path.exists("{0}whole-controlled-destruction.sh".format(self.directory)):
                self.os_system(self.creation_log_file, "{0}whole-controlled-destruction.sh".format(self.directory))
            else:
                if self.directory:
                    self.os_system(self.creation_log_file, "rm -rf {0}".format(self.directory))

        # Display creation status
        print "-------------------------------------------------------------------------"
        print "* INFO: cyris: Cyber range creation status: FAILURE" 
        if not DESTROY_ON_ERROR and self.creation_log_file:
            print "  Check the log file for details: %s" % (self.creation_log_file)
        print "-------------------------------------------------------------------------"

# Start the program
cyris = CyberRangeCreation(sys.argv[1:])
cyris.main()
