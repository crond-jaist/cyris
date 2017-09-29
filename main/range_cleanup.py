#!/usr/bin/python

#############################################################################
# Range cleanup program
#############################################################################

import os
import sys
import subprocess
import logging

import parse_config

logging.basicConfig(level=logging.INFO, format='* %(levelname)s: %(filename)s: %(message)s')


# Default values for the essential parameters
RANGE_ID = 123
CYRIS_PATH = "/home/cyuser/cyris/"
RANGE_PATH = "/home/cyuser/cyris/cyber_range/"

# Constants
SETTINGS_DIR = "settings/"
DESTRUCTION_SCRIPT = "whole-controlled-destruction.sh"

# Try to call the range destruction script prepared by CyRIS
# Return True on success, False on failure, or if the script does not exist
def range_destruction(range_id, range_path):

    # Create the full name of the destruction script
    destruction_script_full = "{0}{1}/{2}".format(range_path, range_id, DESTRUCTION_SCRIPT)
    if os.path.isfile(destruction_script_full):
        # Try to call the script
        logging.debug("Use destruction script: " + destruction_script_full)
        exit_value = subprocess.call(["bash", destruction_script_full])
        if exit_value == 0:
            return True

    logging.warning("Destruction script not found or error.")

    return False

# Forceful cleanup of storage (relevant files and directories)
def storage_cleanup(range_id, cyris_path, range_path):

    # Create the range directory name
    range_dir = "{0}{1}/".format(range_path, range_id)
    # Try to call the script
    logging.info("Cleanup range directory: " + range_dir)

    # Run rm command (should use confirmation?)
    subprocess.call(["rm", "-rf", range_dir])

    # TODO: clean up special files in settings: 123pssh.txt, etc.
    pscp_filename = "{0}{1}{2}pscp_host.txt".format(cyris_path, SETTINGS_DIR, range_id) 
    pssh_filename = "{0}{1}{2}pssh_host.txt".format(cyris_path, SETTINGS_DIR, range_id)
    logging.info("Cleanup range host files: " + pscp_filename + " and " + pssh_filename)
    subprocess.call(["rm", "-f", pscp_filename])
    subprocess.call(["rm", "-f", pssh_filename])
    
# Forceful cleanup via KVM virsh
def kvm_cleanup(range_id):

    range_string = "_cr{0}_".format(range_id)
    command = "virsh list --all"
    output = subprocess.check_output(command, shell=True)
    lines = output.splitlines()
    cleanup_done = False
    for line in lines:
        if range_string in line:
            fields = line.split()
            for field in fields:
                if range_string in field:
                    cleanup_done = True
                    subprocess.call(["virsh", "destroy", field])
                    subprocess.call(["virsh", "undefine", field])

    if not cleanup_done:
        logging.warning("No relevant KVM domains found.")

def main(argv):

    # Assign default values
    range_id = RANGE_ID
    cyris_path = CYRIS_PATH
    range_path = RANGE_PATH

    if len(argv) >= 1:
        # First argument (if exists) is range id
        range_id = argv[0]
        if len(argv) >= 2:
            # Second argument (if exists) is config file name
            config_file = argv[1]
            cyris_path_parsed, range_path_parsed, p2, p3, p4, p5, p6 = parse_config.parse_config(config_file)
            if cyris_path_parsed:
                cyris_path = cyris_path_parsed
            if range_path_parsed:
                range_path = range_path_parsed

    # Handle case when directory names don't end with "/"
    if not cyris_path.endswith("/"):
        cyris_path += "/"
    if not range_path.endswith("/"):
        range_path += "/"

    logging.info("Do cleanup for range #{0}.".format(range_id))

    # First we try the normal range destruction
    did_destroy = range_destruction(range_id, range_path)

    # Then we do cleanup via KVM virsh in case normal destruction failed
    if not did_destroy:
        storage_cleanup(range_id, cyris_path, range_path)
        kvm_cleanup(range_id)

if __name__ == '__main__':
    main(sys.argv[1:])
