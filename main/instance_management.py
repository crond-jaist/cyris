#!/usr/bin/python

import parse_config
import subprocess
import sys
import getopt
import yaml
import os
import fcntl
from datetime import datetime, timedelta
import time

SSH_COMMAND = "ssh -E /dev/null -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

# Timeout for a single SSH connection attempt
CHECK_SSH_TIMEOUT_ONCE = 5
# Timeout in total for all SSH connection attempts
CHECK_SSH_TIMEOUT_TOTAL = 1200
# String used to identify a successful SSH connection attempt
CHECK_SSH_CONNECTIVITY_INDICATOR = "Permission denied"

"""
InstanceManagement:
This class has all important and auxiliar methods for a fine-grained instance control in
a specific cyber range, instantiated by CyRIS.
This class acts as a module, which can be used in CyRIS without additional changes to the
original code. Only a minor change was needed in entities.py, which does not affect the 
rest of the features.
There is a dependency to the parse_config function developed for CyRIS, which
we use for the same purposes.

Developed by:
- Rodrigo Gallardo - rgallardo@fing.edu.uy
- Guillermo Guerrero - guilleguerrero23@gmail.com
"""
class InstanceManagement():

    """
    cleanup_cr:
    If all instances were destroyed on the cyber range, destroy all remaining
    files and folders using the whole-controlled-destruction script created
    on cyber range instantiation.
    """
    def cleanup_cr(self, cr):
        print "* INFO: No instances left on cyber range. Doing whole cyber range cleanup"
        print "* INFO: Using auto-generated whole-controlled-destruction.sh script"
        destruction_script = "{0}{1}/whole-controlled-destruction.sh".format(CR_DIR, str(cr))
        code = subprocess.call(["bash", destruction_script])
        
    """
    destroy_interfaces:
    Edit the /etc/network/interfaces file for deleting the bridges and
    interfaces created for the specified instance.
    """
    def destroy_interfaces(self, cr, instance, host_acc, host_addr, dev_null):
        # Get the content of /etc/network/interfaces over ssh
        command = "sudo cat /etc/network/interfaces"
        ssh_command = SSH_COMMAND + " {0}@{1} '{2}'".format(host_acc, host_addr, command)

        try:
            content = subprocess.check_output(ssh_command, shell = True, stderr = dev_null)
        except:
            print "*    ERROR: Error trying to destroy interfaces on host " + host_addr
            return False

        lines = content.split("\n")
        new_lines = []
        i = 0
        # Search the interfaces created for the instance and delete
        # the next 10 lines (deleting the interface and the bridge)
        while i < len(lines):
            if "auto eth{0}-{1}".format(cr, str(instance)) in lines[i]:
                i = i + 10
            else:
                new_lines.append(lines[i])
                i = i + 1

        # Create string to overwrite the file
        new_content = ""
        for l in new_lines:
            new_content = new_content + l + "\n"

        # Overwrite file on remote host
        command = "echo \"{0}\" | sudo tee /etc/network/interfaces".format(new_content)
        ssh_command = SSH_COMMAND + " {0}@{1} '{2}'".format(host_acc, host_addr, command)

        try:
            output = subprocess.check_output(ssh_command, shell = True, stderr = dev_null)
            print "*    INFO: Interfaces were destroyed"
            return True
        except Exception, e:
            print "*    ERROR: Error trying to destroy interfaces on host " + str(e)
            return False

    """
    destroy_bridges:
    Destroy the bridges and interfaces created on the host for the
    specified instance, belonging to the cyber range.
    """
    def destroy_bridges(self, cr, instance, host_acc, host_addr, dev_null):
        # First, check if the bridges exist on the host. Bridges created
        # by CyRIS are identified by br{cr}-{instance}, where cr and instance
        # are the cyber range and instance identifiers respectively.

        # Build the remote command to query the host for the list of bridges to destroy
        base_command = "ifconfig | grep br{0}-{1}".format(str(cr), str(instance))
        command = SSH_COMMAND + " {0}@{1} '{2}'".format(host_acc, host_addr, base_command)
        bridges = []

        print "*    INFO: Searching bridges to destroy"
        try:
            output = subprocess.check_output(command, shell = True, stderr = dev_null)
            for line in output.split("\n"):
                if (line != ""):
                    bridges.append(line.split(":")[0])
        except:
            print "*    ERROR: Error searching bridges to destroy. Instance may be already undefined."
            return False

        # Then, shut down the bridges previously obtained
        if bridges != []:
            print "*    INFO: Shutting down bridges"
            # Build the remote command to shut down all the necessary bridges
            base_command = ""
            for b in bridges:
                base_command = base_command + "sudo ifdown {0}; ".format(b)

            command = SSH_COMMAND + " {0}@{1} '{2}'".format(host_acc, host_addr, base_command)
            try:
                output = subprocess.check_output(command, shell = True)
            except:
                print "*    ERROR: Error trying to destroy bridges."
                return False

        # Modify /etc/network/interfaces to remove the bridges and
        # interfaces created for the instance
        return self.destroy_interfaces(cr, instance, host_acc, host_addr, dev_null)

    """
    check_ssh_connectivity:
    Check that the guests are up and a SSH connection can be established,
    in order to perform additional configurations once the guest has
    started.
    """
    def check_ssh_connectivity(self, host_acc, host_addr, if_addr):
        # Build command for checking SSH connectivity from remote host
        options = "-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o ConnectTimeout={0}".format(CHECK_SSH_TIMEOUT_ONCE)
        check_command_host = "ssh {0} {1} ls".format(options, if_addr)

        # Build command for checking SSH connectivity from main host
        options_mgmt = "-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PasswordAuthentication=no"
        check_command = "ssh {} {}@{} '{}'".format(options_mgmt, host_acc, host_addr, check_command_host)

        # Compute operation timeout
        crt_time = datetime.now()
        timeout_time = crt_time + timedelta(seconds=CHECK_SSH_TIMEOUT_TOTAL)

        # Loop while current time is less than the timeout
        while datetime.now() < timeout_time:

            # Create a new process to execute command
            proc = subprocess.Popen(check_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            stdout,stderr = proc.communicate()

            # Check whether CHECK_SSH_CONNECTIVITY_INDICATOR string can be found
            if CHECK_SSH_CONNECTIVITY_INDICATOR not in stderr:
                pass
                #if DEBUG: print "* DEBUG: cyris:       Check SSH connectivity to {0} => FAILURE".format(if_addr)
            else:
                #if DEBUG: print "* DEBUG: cyris:       Check SSH connectivity to {0} => SUCCESS".format(if_addr)
                # Additional sleep seems to be required before successfully connecting
                time.sleep(CHECK_SSH_TIMEOUT_ONCE)
                return True

        # This point is only reached on total timeout expiration or error
        print "* ERROR: cyris: Cannot connect to VM."
        #if DEBUG:
        #    print "  Error on connect: %s" % stderr
        return False

    """
    setup_startup:
    Perform network and firewall configurations on guest startup.
    This configurations are non-persistent, so they need to be made
    every time the guest is started up. The configurations include
    setting up default gateways on the guests, starting the firewall
    if needed and including firewall rules.
    """
    def setup_startup(self, cr, instance, guest, host_acc, host_addr, dev_null):
        if ("gateways" in guest.keys() or "firewall_rule" in guest.keys()):
            if not self.check_ssh_connectivity(host_acc, host_addr, guest['ip_addrs']['eth0']):
                print "*    ERROR: Could not connect to guest" + guest['kvm_domain']
                return False
            print "*    INFO: Connection to guest " + guest['kvm_domain'] + " successful"

            # If needed, configure default gateway on the guest
            if ("gateways" in guest.keys()):
                interface = guest['gateways'].keys()[0]
                route_command = "route add default gw {0} {1}".format(guest['gateways'][interface], interface)
                command_host = SSH_COMMAND + " root@{0} '{1}'".format(guest['ip_addrs']['eth0'], route_command)

                remote_command = SSH_COMMAND + " {0}@{1} \"{2}\"".format(host_acc, host_addr, command_host)
                try:
                    output = subprocess.check_output(remote_command, shell = True, stderr = dev_null)
                    print "*        INFO: Default gatways setup successfully"
                except:
                    print "*        ERROR: Could not start guest successfully. Routing info may be corrupt."
                    return False

            # If needed, start iptables and add firewall rules to the guest
            if ("firewall_rule" in guest.keys()):
                base_command = "systemctl stop firewalld; systemctl start iptables; systemctl start ip6tables; "
                for r in sorted(guest['firewall_rule'].keys()):
                    base_command = base_command + guest['firewall_rule'][r] + ";"

                command_host = SSH_COMMAND + " root@{0} '{1}'".format(guest['ip_addrs']['eth0'], base_command)
                remote_command = SSH_COMMAND + " {0}@{1} \"{2}\"".format(host_acc, host_addr, command_host)
                try:
                    output = subprocess.check_output(remote_command, shell = True, stderr = dev_null)
                    print "*        INFO: Firewall rules setup successfully"
                except:
                    print "*        ERROR: Could not start guest successfully. Routing info may be corrupt."
                    return False


    """
    control_instances:
    Given an action, a cyber range identifier and a list of instance identifiers,
    this function tries to apply the action to all instances identified on the 
    list belonging to the desired cyber range.
    The action argument can be "destroy", "shutdown" or "start".
    """
    def control_instances(self, action, cr, instances):
        # Parse the cyber range description file and obtain hosts,
        # instances and guests info
        doc = self.parse_yaml_file(cr)
        if (doc is None):
            return

        dev_null = open(os.devnull, 'w')

        # Obtain the list of previously destroyed instances
        destroyed_instances = self.parse_destroyed_instances_file(cr)
        # List of newly destroyed instances to keep track of
        new_destroyed_instances = []
        # Count the number of instances on the cyber range
        num_instances = 0

        if (action == "start"):
            base_command = "virsh start "
            print "* INFO: Starting specified instances"
            not_started = []
        elif (action == "shutdown"):
            base_command = "virsh shutdown "
            print "* INFO: Shutting down specified instances"
        elif (action == "destroy"):
            base_command = "virsh shutdown "
            print "* INFO: Destroying specified instances"

        # For all hosts in which the cyber range is deployed
        for h in doc['hosts']:
            # Count the number of instances deployed on the host
            num_instances += len(h['instances'])
            # For all instances deployed on the host
            for i in h['instances']:
                # If instance is referenced as a target of the action
                if (i['instance_index'] in instances or instances == []):
                    # If instance was previously destroyed, no action can be made
                    if (i['instance_index'] in destroyed_instances):
                        print "* INFO: Instance " + str(i['instance_index']) + " was already destroyed"
                    else:
                        print "* INFO: Instance " + str(i['instance_index'])

                        err = False

                        # If the instance must be destroyed, destroy the created bridges
                        # and interfaces. In case of error, do not continue with the
                        # destruction of the instance.
                        if (action == "destroy"):
                            err = not self.destroy_bridges(cr, i['instance_index'], h['account'], h['mgmt_addr'], dev_null)

                        if (not err):
                            # For each guest in the instance, apply the specific action
                            for g in i['guests']:
                                sys.stdout.write("*    INFO: " + g['kvm_domain'] + "... ")
                                sys.stdout.flush()

                                # Build the remote command to shutdown/start/destroy the guest,
                                # execute the command and obtain the output
                                virsh_command = base_command + "{0}".format(g['kvm_domain'])

                                if (action == "destroy"):
                                    virsh_command = virsh_command + "; virsh undefine {0}".format(g['kvm_domain'])

                                command = SSH_COMMAND + " {0}@{1} '{2}'".format(h['account'], h['mgmt_addr'], virsh_command)
                                try:
                                    output = subprocess.check_output(command, shell = True, stderr=dev_null)
                                    output = output.replace("\n", " ")
                                    print output
                                except:
                                    err = True
                                    if (action == "start"):
                                        not_started.append(i['instance_index'])
                                    print "Error trying to " + action + " " + g['kvm_domain']

                        # Only add the instance to the destroyed_instances file if
                        # it was completely destroyed.
                        if (not err and action == "destroy"):
                            new_destroyed_instances.append(str(i['instance_index']) + "\n")

        # If instances were started, configure default gateways and firewall
        # rules as described in the details file.
        if (action == "start"):
            print "* INFO: Configuring default gateways and firewall on startup..."
            for h in doc['hosts']:
                for i in h['instances']:
                    if ((i['instance_index'] in instances or instances == []) and i['instance_index'] not in destroyed_instances and i['instance_index'] not in not_started):
                        print "* INFO: Instance " + str(i['instance_index'])
                        for g in i['guests']:
                            self.setup_startup(cr, i['instance_index'], g, h['account'], h['mgmt_addr'], dev_null)

        # If instances were destroyed, check to see if all instances on the cyber range
        # were destroyed. In that case, clean the whole cyber range. Otherwise, append
        # the newly destroyed instances to the destroyed_instances file.
        if (action == "destroy"):
            if (num_instances == len(new_destroyed_instances) + len(destroyed_instances)):
                self.cleanup_cr(cr)
            elif (new_destroyed_instances):
                destroyed_instances_filename = "{0}{1}/destroyed_instances.txt".format(CR_DIR, str(cr))
                if (action == "destroy" and new_destroyed_instances):
                    try:
                        with open(destroyed_instances_filename, "a+") as f:
                            f.writelines(new_destroyed_instances)
                    except Exception, e:
                        print str(e)
                        print "* ERROR: Could not write destroyed_instances file. Cyber range information may be corrupt."

    """
    parse_yaml_file:
    Auxiliary function for parsing the cyber range description file created
    on instantiation. This file hold important information of the hosts
    on which the cyber range is deployed, of the instances deployed on the 
    hosts and of the guests included in the instances.
    This function parses the YAML file and returns a dictionary data
    structure with the cyber range info.
    """               
    def parse_yaml_file(self, cr):
        range_details_filename = "{0}{1}/range_details-cr{1}.yml".format(CR_DIR, str(cr))
        try:
            with open(range_details_filename, "r") as f:
                # This funcion parses the YAML file and returns the dictionary structure
                doc = yaml.load(f)
                return doc
        except yaml.YAMLError, exc:
            print "* ERROR: cyris: Issue with the cyber range details file: ", exc
            return None
        except:
            print "* ERROR: cyris: Error with the cyber range details file."
            return None

    """
    parse_destroyed_instances_file:
    The destroyed_instances file holds a list of all previously destroyed
    instances on the cyber range, in order to keep track of the remaining
    instances and to avoid trying to apply actions on destroyed instances.
    This function returns a list containing the identifiers of all
    destroyed instances.
    """
    def parse_destroyed_instances_file(self, cr):
        destroyed_instances_filename = "{0}{1}/destroyed_instances.txt".format(CR_DIR, str(cr))
        try:
            with open(destroyed_instances_filename, "r") as f:
                ls = f.readlines()
                for i in range(len(ls)):
                    ls[i] = ls[i].replace("\n","")
                return ls
        except:
            return []

    """
    pretty_print:
    Auxiliary function for displaying strings on the table.
    """
    def pretty_print(self, s, size):
        if len(s) >= size:
            return s
        for i in range(size - len(s)):
            s += " "
        return s

    """
    list_status:
    For a specific cyber range and a list of instance identifies,
    this functions prints the status of all guests inside the
    instances specified in the list.
    The status for a guest may be:
    - running: the VM is on
    - shut off: the VM is off
    - error: there was an error checking the status of the guest
    - destroyed: the instance has been destroyed
    """
    def list_status(self, cr, instances):
        # Parse the cyber range description file and obtain hosts,
        # instances and guests info
        doc = self.parse_yaml_file(cr)
        if (doc is None):
            return

        # Obtain the list of previously destroyed instances
        destroyed_instances = self.parse_destroyed_instances_file(cr)

        dev_null = open(os.devnull, 'w')

        print "\nHost                       | Instance   | Guest name     | Guest number   | Status   "
        print "---------------------------------------------------------------------------------------"

        # For all hosts in which the cyber range is deployed
        for h in doc['hosts']:
            # For all instances deployed in the host
            for i in h['instances']:
                if (i['instance_index'] in instances or instances == []):
                    # For all guests in that instance
                    for g in i['guests']:
                        names = g['kvm_domain'].split("_")
                        # If the instance was previously destroyed, we avoid checking the
                        # status with the host.
                        if (str(i['instance_index']) not in destroyed_instances):
                            # Build the remote command to query the host for the status of
                            # the guest, execute the command and obtain the output
                            virsh_command = "virsh domstate {0}".format(g['kvm_domain'])
                            command = SSH_COMMAND + " {0}@{1} '{2}'".format(h['account'], h['mgmt_addr'], virsh_command)
                            try:
                                output = subprocess.check_output(command, shell = True, stderr = dev_null)
                                output = output.replace("\n", "")
                            except:
                                output = "error"
                        else:
                            output = "destroyed"
                        print "{0}| {1}| {2}| {3}| {4}\n".format(self.pretty_print(h['mgmt_addr'], 15), self.pretty_print(str(i['instance_index']), 11), self.pretty_print(names[0], 15), self.pretty_print(names[3], 15), output)
    
    """
    usage:
    Auxiliary function for printing the instrunctions on how to
    use the module.
    """
    def usage(self):
        print "OVERVIEW: Instance Management module. This module allows to shutdown/start/destroy individual instances of a cyber range."
        print "          It can also print the status of instances of a cyber range.\n"
        print "USAGE: instance_management.py [options] ACTION RANGE_ID INSTANCES CONFIG_FILE\n"
        print "       ACTION is one of the following: shutdown, start, destroy, list.\n"
        print "       RANGE_ID is the identifier of the instatiated cyber range, as specified in the cyber range description file.\n"
        print "       INSTANCES is a list of individual instance identifiers or ranges of instance identifiers, separated by a ','."
        print "         It can also take the special value ALL, to reference all instances in the cyber range."
        print "         For example: 50-54,71,73 identifies the instances [50,51,52,53,54,71,73]."
        print "                      20,25-28,30-32 identifies the instances [20,25,26,27,28,30,31,32]."
        print "                      ALL identifies all the instances in the cyber range.\n"
        print "       CONFIG_FILE is the path of the CyRIS configuration file.\n"
        print "OPTIONS:"
        print "-h --help        Display help"
        print "-v --verbose     Display verbose messages for debugging purposes"

    """
    parse_instances_arg:
    Auxiliary method for parsing the instances string argument. As described in
    the usage function, this argument is a list of individual instance identifiers 
    or ranges of instance identifiers, separated by a ','. It can also take the 
    special value ALL, to reference all instances in the cyber range.

    This function returns a list with all instance identifiers referenced by
    the string argument. An empty list references all instances, and a None
    value indicates an error.
    """
    def parse_instances_arg(self, arg):
        result = []
        if (arg == "ALL"):
            # An empty list references all instances in the cyber range
            return result
        else:
            # First we split by ","
            ranges = arg.split(",")
            for r in ranges:
                try:
                    # If the token is an individual identifier, add it to the list
                    int(r)
                    result.append(int(r))
                except:
                    # If the token is a range of identifiers, add all identifiers
                    # on that range to the list
                    borders = r.split("-")
                    if (len(borders) != 2):
                        return None
                    try:
                        int(borders[0])
                        int(borders[1])
                        rng = range(int(borders[0]), int(borders[1]) + 1)
                        result = result + rng
                    except:
                        # If the string argument is invalid, return None
                        return None
        return list(set(result))


    def parse_config_file(self, config):
        global ACTION
        global DEBUG
        # Get global parameters from CONFIG file.
        global ABS_PATH
        global CR_DIR
        global GW_MODE
        global GW_ACCOUNT
        global GW_MGMT_ADDR
        global GW_INSIDE_ADDR
        global USER_EMAIL

        # Get global parameters from CONFIG file.
        print "* INFO: cyris: Parse the configuration file."
        ABS_PATH, CR_DIR, GW_MODE, GW_ACCOUNT, GW_MGMT_ADDR, GW_INSIDE_ADDR, USER_EMAIL = parse_config.parse_config(config)
        if ABS_PATH == False:
            print "* ERROR: cyris: Error parsing configuration file. Check if path is correct."
            quit(-1)

    """
    main:
    Receives and parses the command-line arguments and options and
    invokes the corresponding methods to complete the specified
    action.
    """
    def main(self, argv):

        # Parse options and command-line arguments
        try:
            opts, args = getopt.getopt(argv, "hv", ["help", "verbose"])
        except getopt.GetoptError as err:
            print "* ERROR: cyris: Command-line argument error: %s" % (str(err))
            self.usage()
            quit(-1)

        DEBUG = False
        # Deal with options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                self.usage()
                quit(-1)
            elif opt in ("-v", "--verbose"):
                DEBUG = True
                print "* DEBUG: cyris: Debug mode enabled."

        # Deal with command-line arguments
        if len(args)<4:
            print "* ERROR: cyris: Not enough command-line arguments."
            self.usage()
            quit(-1)

        # Deal with unrecognized actions
        if args[0] not in ["destroy", "list", "shutdown", "start"]:
            print "* ERROR: cyris: Action not recognized."
            self.usage()
            quit(-1)

        # Parse the instances string argument to build a list of
        # all referenced instances
        instances = self.parse_instances_arg(args[2])
        if instances is None:
            print "* ERROR: cyris: Instances argument is not correct."
            self.usage()
            quit(-1)

        print "#########################################################################"
        print "Instance Management - Cyber Range Instantiation System"
        print "#########################################################################"

        self.parse_config_file(args[3])



        # Invoke the desired action
        if (args[0] in ["destroy", "shutdown", "start"]):
            self.control_instances(args[0], args[1], instances)
        elif (args[0] == "list"):
            self.list_status(args[1], instances)

im = InstanceManagement()
#im.main(sys.argv[1:])
