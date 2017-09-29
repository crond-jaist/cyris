#!/usr/bin/python

import yaml
import os

from storyboard import Storyboard

FLAG = True

DEBUG = False

def raise_flag(error):
    print "* ERROR: check_description:", error
    global FLAG
    if FLAG == True:
        FLAG = False
    else:
        pass

def get_existed_cr_id_list(abspath):
    cr_id_list = []
    if os.path.isdir("{0}cyberrange/"):
        for cr_id in os.listdir("{0}cyberrange/".format(abspath)):
            cr_id_list.append(int(cr_id))
    return cr_id_list

# Determine the set of networks that appear in the forwarding rules, both as src and dst
def get_network_set(fw_rules):
    src_set = set()
    dst_set = set()
    for rule in fw_rules:
        elements = rule.strip().split(" ")
        for e in elements:
            # Add src networks to set (comma separated values allowed, but no space)
            if "src" in e:
                src_nw_string = e.split("=")[1]
                src_set = set().union(src_set, src_nw_string.split(","))
            # Add dst networks to set (remove guest suffix that may follow)
            if "dst" in e:
                dst_nw_string = e.split("=")[1]
                dst_set = set().union(dst_set, [dst_nw_string.split(".")[0]])

    # Create final set as union of src and dst networks
    nw_set = set().union(src_set, dst_set)

    return nw_set

def check_description(filename, abspath):
    try:
        with open(filename, "r") as f:
            doc = yaml.load(f)
    except IOError, e:
        raise_flag(e)
        return FLAG
    except yaml.YAMLError, e:
        raise_flag(e)
        return FLAG

    # For each playbook in the training description.
    host_section = doc[0]
    guest_section = doc[1]
    clone_section = doc[2]

    # Store all host ids that were defined in the host_settings section
    defined_host_ids = []
    defined_forwarding_rules = []

    # Check the "host_settings" part of the description.
    if Storyboard.HOST_SETTINGS not in host_section.keys():
        raise_flag("Tag 'host_settings' is missing.")
    else:
        for i,h in enumerate(host_section[Storyboard.HOST_SETTINGS]):
            
            host_id = "N/A"

            # Check syntax and keywords.
            if Storyboard.ID not in h.keys():
                raise_flag("Tag 'id' is missing for one of the hosts in 'host_settings' section.")
            else:
                host_id = h[Storyboard.ID]
                if not host_id in defined_host_ids:
                    defined_host_ids.append(host_id)
                else:
                    raise_flag("Host with id {0} is duplicated in the 'host_settings' section.".format(host_id))
            if Storyboard.MGMT_ADDR not in h.keys():
                raise_flag("Tag 'mgmt_addr' is missing for host {0} in 'host_settings' section.".format(host_id))
            if Storyboard.VIRBR_ADDR not in h.keys():
                raise_flag("Tag 'virbr_addr' is missing for host {0} in 'host_settings' section.".format(host_id))
            if Storyboard.ACCOUNT not in h.keys():
                raise_flag("Tag 'account' is missing for host {0} in 'host_settings' section.".format(host_id))
    
    # Check the "guest_settings" part of the description.
    if "guest_settings" not in guest_section.keys():
        raise_flag("Tag 'guest_settings' is missing.")
    else:
        for i,g in enumerate(guest_section["guest_settings"]):
            # Check syntax and keywords.
            if "id" not in g.keys():
                raise_flag("Tag 'id' is missing for one of the guests in 'guest_settings' section.")
            if "basevm_config_file" not in g.keys():
                raise_flag("Tag 'basevm_config_file' is missing for one of the guests in 'guest_settings' section.")
            else:
                config_file = g["basevm_config_file"]
                if ".xml" in config_file:
                    harddisk_file = config_file.replace(".xml", "")
                if DEBUG:
                    print config_file
                    print harddisk_file
                if not os.path.exists(config_file):
                    raise_flag("The config file of one of the guests in 'guest_settings' section doesn't exist.")
                if not os.path.exists(harddisk_file):
                    raise_flag("The hard disk file of one of the guests in 'guest_settings' section doesn't exist.")

            if "basevm_type" not in g.keys():
                raise_flag("Tag 'basevm_type' is missing for on of the guests in 'guest_settings' section.")
            if "tasks" in g.keys():
                for task in g["tasks"]:
                    if "add_account" in task.keys():
                        for a in task["add_account"]:
                            if "account" not in a.keys():
                                raise_flag("Tag 'account' is missing for task 'add_account' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "passwd" not in a.keys():
                                raise_flag("Tag 'passwd' is missing for task 'add_account' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "modify_account" in task.keys():
                        for a in task["modify_account"]:
                            if "account" not in a.keys():
                                raise_flag("Tag 'account' is missing for task 'modify_account' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "new_passwd" not in a.keys() and "new_account" not in a.keys():
                                raise_flag("Either tag 'new_account' or tag 'new_passwd' is missing for task 'modify_account' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "install_package" in task.keys():
                        for a in task["install_package"]:
                            #if "package_manager" not in a.keys():
                            #    raise_flag("Tag 'package_manager' is missing for task 'install_package' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "name" not in a.keys():
                                raise_flag("Tag 'name' is missing for task 'install_package' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "emulate_attack" in task.keys():
                        for a in task["emulate_attack"]:
                            if "attack_type" not in a.keys():
                                raise_flag("Tag 'attack_type' is missing for task 'emulate_attack' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "target_account" not in a.keys():
                                raise_flag("Tag 'target_account' is missing for task 'emulate_attack' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "attempt_number" not in a.keys():
                                raise_flag("Tag 'attempt_number' is missing for task 'emulate_attack' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "emulate_traffic_capture_file" in task.keys():
                        for a in task["emulate_traffic_capture_file"]:
                            if "format" not in a.keys():
                                raise_flag("Tag 'format' is missing for task 'emulate_traffic_capture_file' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "file_name" not in a.keys():
                                raise_flag("Tag 'file_name' is missing for task 'emulate_traffic_capture_file' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "attack_type" not in a.keys():
                                raise_flag("Tag 'attack_type' is missing for task 'emulate_traffic_capture_file' in one of the guests in 'guest_settings' - 'tasks' section.")
                            else:
                                if "ssh" in a["attack_type"]:
                                    if "attack_source" not in a.keys():
                                        raise_flag("Tag 'attack_source' is missing for task ssh_attack in 'emulate_traffic_capture_file' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "noise_level" not in a.keys():
                                raise_flag("Tag 'noise_level' is missing for task 'emulate_traffic_capture_file' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "emulate_malware" in task.keys():
                        for a in task["emulate_malware"]:
                            if "name" not in a.keys():
                                raise_flag("Tag 'name' is missing for task 'emulate_malware' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "mode" not in a.keys():
                                raise_flag("Tag 'mode' is missing for task 'emulate_malware' in one of the guests in 'guest_settings' - 'tasks' section.")
                            else:
                                if "calculation" in a["mode"]:
                                    if "cpu_utilization" not in a.keys():
                                        raise_flag("Tag 'cpu_utilization' is missing for running dummy_calculation mode in task 'emulate_malware' in one of the guests in 'guest_settings' - 'tasks' section.")
                                if "listening" in a["mode"]:
                                    if "port" not in a.keys():
                                        raise_flag("Tag 'port' is missing for running port_listening mode in task 'emulate_malware' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "copy_content" in task.keys():
                        for a in task["copy_content"]:
                            if "src" not in a.keys():
                                raise_flag("Tag 'src' is missing for task 'copy_content' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "dst" not in a.keys():
                                raise_flag("Tag 'dst' is missing for task 'copy_content' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "execute_program" in task.keys():
                        for a in task["execute_program"]:
                            if "program" not in a.keys():
                                raise_flag("Tag 'program' is missing for task 'execute_program' in one of the guests in 'guest_settings' - 'tasks' section.")
                            if "interpreter" not in a.keys():
                                raise_flag("Tag 'interpreter' is missing for task 'execute_program' in one of the guests in 'guest_settings' - 'tasks' section.")
                    if "firewall_rules" in task.keys():
                        for a in task["firewall_rules"]:
                            if "rule" not in a.keys():
                                raise_flag("Tag 'rule' is missing for task 'firewall_rules' in one of the guests in 'guest_settings' - 'tasks' section.")

    # Check the "clone_settings" part of the description.
    if Storyboard.CLONE_SETTINGS not in clone_section.keys():
        raise_flag("Tag 'clone_settings' is missing.")
    else:
        clone = clone_section[Storyboard.CLONE_SETTINGS][0]
        # Check syntax and keywords.
        if Storyboard.RANGE_ID not in clone.keys():
            raise_flag("Tag 'range_id' is missing in 'clone_settings' section.")
        else:
            range_id = int(clone[Storyboard.RANGE_ID])
            cr_id_list = get_existed_cr_id_list(abspath)
            if range_id in cr_id_list:
                raise_flag("Range with id {0} already exists. Please choose another id.".format(range_id))
        if Storyboard.HOSTS not in clone.keys():
            raise_flag("Tag 'hosts' is missing in 'clone_settings' section.")
        else:
            for host in clone[Storyboard.HOSTS]:
                if Storyboard.HOST_ID not in host.keys():
                    raise_flag("Tag 'host_id' is missing for tag 'hosts', 'clone_settings' section.")
                else:
                    # Check whether the host id was already defined in the host_settings section
                    host_id = host[Storyboard.HOST_ID]
                    # Convert to list of hosts, in case comma-separated format is used
                    # (and make sure to remove potential spaces first)
                    host_id_list = host_id.replace(" ","").split(",")
                    for host_id_item in host_id_list:
                        # Check host id existence
                        if host_id_item not in defined_host_ids:
                            raise_flag("Host with id \"{0}\" in the 'clone_settings' - 'hosts' section not defined in the 'host_settings' section.".format(host_id_item))
                if Storyboard.INSTANCE_NUMBER not in host.keys():
                    raise_flag("Tag 'instance_number' is missing for tag 'hosts', 'clone_settings' section.")
                if Storyboard.GUESTS not in host.keys():
                    raise_flag("Tag 'guests' is missing for tag 'hosts', 'clone_settings' section.")
                else:
                    entry_point_count = 0
                    for guest in host[Storyboard.GUESTS]:
                        if Storyboard.GUEST_ID not in guest.keys():
                            raise_flag("Tag 'guest_id' is missing for tag 'guests', 'clone_settings' - 'hosts' section.")
                        if Storyboard.NUMBER not in guest.keys():
                            raise_flag("Tag 'number' is missing for tag 'guests', 'clone_settings' - 'hosts' section.")
                        if Storyboard.ENTRY_POINT in guest.keys():
                            entry_point_count += 1
                        if Storyboard.FORWARDING_RULES in guest.keys():
                            defined_forwarding_rules = []
                            for rule_set in guest[Storyboard.FORWARDING_RULES]:
                                if Storyboard.RULE not in rule_set.keys():
                                    raise_flag("Tag 'rule' is missing for task 'forwarding_rules' in one of the guests in 'clone_settings' - 'guests' section.")
                                else:
                                    defined_forwarding_rules.append(rule_set[Storyboard.RULE])

                    # TODO: How to check this in case multiple hosts are used?!
                    if entry_point_count == 0:
                        raise_flag("Tag 'entry_point' is missing for tag 'guests', 'clone_settings' - 'hosts' section.")
                    if entry_point_count > 1:
                        raise_flag("Tag 'entry_point' appears more than once for tag 'guests', 'clone_settings' - 'hosts' section.")

                if Storyboard.TOPOLOGY not in host.keys():
                    raise_flag("Tag 'topology' is missing for tag 'hosts', 'clone_settings' section.")
                else:
                    topology = host[Storyboard.TOPOLOGY][0]
                    if Storyboard.TYPE not in topology.keys():
                        raise_flag("Tag 'type' is missing for tag 'topology', 'clone_settings' - 'hosts' section.")
                    if Storyboard.NETWORKS not in topology.keys():
                        raise_flag("Tag 'networks' is missing for tag 'topology', 'clone_settings' - 'hosts' section.")
                    else:
                        # Process each network definition, and check whether the forwarding rules specified previously
                        # contain any undefined networks
                        nw_set = get_network_set(defined_forwarding_rules)
                        for network in topology[Storyboard.NETWORKS]:
                            if Storyboard.NAME not in network.keys():
                                raise_flag("Tag 'name' is missing for tag 'network', 'topology' - 'clone_settings' - 'hosts' section.")
                            else:
                                nw_name = network[Storyboard.NAME]
                                # If network name present in nw_set, remove it to signify it was defined already
                                if nw_name in nw_set:
                                    nw_set.remove(nw_name)
                            if Storyboard.MEMBERS not in network.keys():
                                raise_flag("Tag 'members' is missing for tag 'network', 'topology' - 'clone_settings' - 'hosts' section.")
                        # If there are still elements in nw_set, it means that the forwarding rules specified
                        # previously contain undefined networks
                        if nw_set:
                            raise_flag("Undefined networks in rule of 'forwarding_rules' for one of the guests in 'clone_settings' - 'guests' section: {0}".format(list(nw_set)))

    return FLAG
