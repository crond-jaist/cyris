#!/usr/bin/python

#############################################################################
# Classes of CyRIS clone feature
#############################################################################

# External imports
#import sys
import os
#from entities import Command
import paramiko
#import subprocess
#import string
#import random
import urllib
import string
from cyvar import CyVarBox

# Internal imports
#from entities import Host, Guest, Bridge, EntryPoint, CloneGuest, CloneSubnetwork, CloneInstance, CloneHost, CloneSetting
from modules import ManageUsers

INSTANTIATION_DIR = "instantiation"
CLEANUP_DIR = "cleanup"

DEBUG = False

##########################################################################
# The VMClone class takes inputs as:
# @gw_account, @gw_addr   The info of the gateway in the physical topology, 
#                          so that it can create bridges to connect from outside 
#                          to each cyber range instance
# @host_list              List of hosts that user specify in the "host_settings" tag in
#                          the cyber range description file
# @guest_list             List of guests that user specify in the "guest_settings" tag
#                          in the cyber range description file
# @clone_setting          The CloneSetting object from entity classes (entities.py)
# @*_file                 Related clone files. Refer to the main class (cyris.py) for more info
# @directory              Directory containing all related files for the clone phase of the being created cyber range
# @abspath                The absolute path to the cyris directory
class VMClone(object):
    def __init__(self, gw_mode, gw_account, gw_addr, host_list, guest_list, clone_setting, log_file, setup_fwrule_file, setup_dfgw_file, create_bridges_file, entry_points_file, clone_file, create_vms_file, create_tunnels_file, create_entry_accounts_file, install_prg_afcln_file, install_wordpress_file, destruction_file, directory, abspath):
        self.gw_mode = gw_mode
        self.gw_account = gw_account
        self.gw_addr = gw_addr
        self.host_list = host_list
        self.guest_list = guest_list
        self.clone_setting = clone_setting
        self.log_file = log_file
        self.setup_fwrule_file = setup_fwrule_file
        self.setup_dfgw_file = setup_dfgw_file
        self.create_bridges_file = create_bridges_file
        self.entry_points_file = entry_points_file
        self.clone_file = clone_file
        self.create_vms_file = create_vms_file
        self.create_tunnels_file = create_tunnels_file
        self.create_entry_accounts_file = create_entry_accounts_file
        self.install_prg_afcln_file = install_prg_afcln_file
        self.install_wordpress_file = install_wordpress_file
        self.destruction_file = destruction_file
        self.directory = directory
        self.abspath = abspath
        self.mgmt_addr = "{0}.0.0.0/8".format(self.clone_setting.getRangeId())   # management address of the whole cyber range

    #########################################################################
    # Generate management address for the cyber range
    # <range_id>.0.0.0/8

    #########################################################################
    # Generate ipaddr & netmask for the initif.conf file, and copy it to the base images
    def generate_initif(self):
#        initif_commands_list = []
        # Check how many network interface in each guest
        for guest in self.guest_list:
            for host in self.clone_setting.getCloneHostList():
                for instance in host.getInstanceList():
                    for clone_guest in instance.getCloneGuestList():
                        if guest.getGuestId() == clone_guest.getGuestId():
                            nic_num = len(clone_guest.getNicAddrDict())
                            # Add ip_range to initif.conf file
                            filename = "{0}initif.conf".format(self.directory)
                            content = "\n"
                            for i in range(0,nic_num):
                                initif_mac_addr_5="%x" % int(clone_guest.getNicAddrDict()["eth"+str(i)].split(".")[2])
                                initif_mac_addr_6="%x" % int(clone_guest.getNicAddrDict()["eth"+str(i)].split(".")[3])
                                content += "eth{0} {1} {2}:{3}\n".format(i, self.mgmt_addr, initif_mac_addr_5.zfill(2), initif_mac_addr_6.zfill(2))
                            with open(filename, "w") as f:
                                f.write(content)
                            if guest.getBasevmOSType() =='windows.7':
                                command = "scp {0}initif.conf root@{1}:'C:\CyberRange\initif'".format(self.directory, guest.getBasevmAddr())
                            else:
                                command = "scp {0}initif.conf root@{1}:/bin/cyberrange/initif".format(self.directory, guest.getBasevmAddr())
                            os.system(command + ">> {0} 2>&1".format(self.log_file))
                            break
                    break
                break

    #########################################################################
    # Generate files for creating bridges
    def create_bridges(self):
        # Write create_bridges.sh file in parallel in multiple hosts
        for clone_host in self.clone_setting.getCloneHostList():
            # Get mgmt_addr and account of corresponding host
            for host in self.host_list:
                if clone_host.getHostId() == host.getHostId():
                    account = host.getAccount()
                    mgmt_addr = host.getMgmtAddr()

            # Setup and create an SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # The command below causes a warning to be displayed => inform users that it's harmless
            # NOTE: After upgrade to Ubuntu 18.04 warning disappeared, so message was commented out
            #print "* NOTE: cyris: The warning below can be safely ignored (caused by use of paramiko library in 'clone_environment.py')."
            ssh.connect(mgmt_addr, username=account)

            # Open an SFTP session on the SSH server
            sftp_client = ssh.open_sftp()

            # Create the bridges
            with sftp_client.open(self.create_bridges_file,"a+") as myfile:
                for instance in clone_host.getInstanceList():
                    for bridge in instance.getBridgeList():
                        # Write bridge config in /etc/network/interface by calling 01_write_bridge_config.sh
                        myfile.write("sudo -S {0}{3}/vm_clone/create_bridges/01_write_bridge_config.sh {1} {2}\n".format(self.abspath, bridge.getId(), bridge.getAddr(), INSTANTIATION_DIR))
                        # Call ifup bridge
                        myfile.write("sudo -S ifup br{0} &\n".format(bridge.getId()))
                # Wait for creating bridges get done
                myfile.write("wait\n")
                myfile.write("echo \" bridges are up\"")

            # Destruct the bridges
            with sftp_client.open(self.destruction_file, "a+") as myfile:
                for instance in clone_host.getInstanceList():
                    for bridge in instance.getBridgeList():
                        myfile.write("sudo ifdown br{0};\n".format(bridge.getId()))

            # Close the SFTP and SSH sessions
            sftp_client.close()
            ssh.close()

    #########################################################################
    # Generate files for cloning vm phase
    def clone_vm(self):
        #command_list = []
        for clone_host in self.clone_setting.getCloneHostList():
            # Get mgmt_addr and account of corresponding host
            for host in self.host_list:
                if clone_host.getHostId() == host.getHostId():
                    account = host.getAccount()
                    mgmt_addr = host.getMgmtAddr()
            # ssh connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(mgmt_addr, username=account)
            sftp_client = ssh.open_sftp()

            # Write list of entry points in the current host to file
            with sftp_client.open(self.entry_points_file, "a+") as f:
                for instance in clone_host.getInstanceList():
                    f.write("{0}\n".format(instance.getEntryPoint().getAddr()))

            # Write files for clone vm phase
            with sftp_client.open(self.clone_file, "a+") as f:
                # For each instance in the host
                for instance in clone_host.getInstanceList():
                    # For each guest in the instance
                    for clone_guest in instance.getCloneGuestList():
                        # Get the basevm_name and basevm_addr of that guest's base image 
                        # (types here are webserver, desktop, firewall, etc.)
                        #for guest in self.guest_list:
                        #    if clone_guest.getGuestId() == guest.getGuestId():
                        #        basevm_name = guest.getBasevmName()
                        #        break
                        # For each vmaddr in the vm addresses list, create an 
                        # vm_id = <guest_id>_<range_id>_<instance_index>_<guest_index>,
                        
                        # The KVM domain name is now defined in entities.py, writeConfig function
                        if clone_guest.kvm_domain:
                            if DEBUG:
                                print "* DEBUG: KVM domain name already defined => use it."
                            vm_id = clone_guest.kvm_domain # Save KVM domain name
                        else:
                            print "* WARNING: KVM domain name not yet defined => generate now."
                            vm_id = "{0}_cr{1}_{2}_{3}".format(clone_guest.getGuestId(), self.clone_setting.getRangeId(), instance.getIndex(), clone_guest.getIndex())

                        # Generate bridge_id_list and addr_list for the vm
                        # addr_list consists of ip addresses of every nic in the vm
                        # bridge_id_list consists of bridge_id of every nic in the vm
                        bridge_id_list = []
                        addr_list = []
                        for key,value in clone_guest.getNicAddrDict().items():
                            addr_list.append(value)
                            bits_vmaddr = value.split(".")
                            for bridge in instance.getBridgeList():
                                bits_bridge = bridge.getAddr().split(".")
                                if bits_bridge[0] == bits_vmaddr[0] and bits_bridge[1] == bits_vmaddr[1] and bits_bridge[2] == bits_vmaddr[2]:
                                    bridge_id_list.append(bridge.getId())
                                    break
                        # Transform bridge_id_list and addr_list to bridge_id_str and addr_str
                        # as inputs for the create_vm.sh script
                        bridge_id_str = ",".join(bridge_id_list)
                        addr_str = ",".join(addr_list)
                        f.write("{0}{6}/vm_clone/create_vms.sh 1 {1} {2} {0} {3} {4} {5};\n".format(self.abspath, vm_id, clone_guest.getGuestId(), self.directory, bridge_id_str, addr_str, INSTANTIATION_DIR))


    #########################################################################
    # Generate files for setting up firewall rules for guests
    def set_fwrule(self):
        for clone_host in self.clone_setting.getCloneHostList():
            # Get mgmt_addr and account of corresponding host
            for host in self.host_list:
                if clone_host.getHostId() == host.getHostId():
                    account = host.getAccount()
                    mgmt_addr = host.getMgmtAddr()
            # ssh connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(mgmt_addr, username=account)
            sftp_client = ssh.open_sftp()
            with sftp_client.open(self.setup_fwrule_file, "a+") as fwrule_file:
                for instance in clone_host.getInstanceList():
                    command = ""
                    for guest in instance.getCloneGuestList():
                        if len(guest.getFwRuleList()) != 0:
                            rule_str = ";".join(guest.getFwRuleList()[:])
                            command += "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} \"{1}\"\n".format(guest.getNicAddrDict().values()[0], rule_str)
                    fwrule_file.write(command)

    #########################################################################
    # Generate files for setting up default gateway for guests
    def set_dfgw(self):
        for clone_host in self.clone_setting.getCloneHostList():
            # Get mgmt_addr and account of corresponding host
            for host in self.host_list:
                if clone_host.getHostId() == host.getHostId():
                    account = host.getAccount()
                    mgmt_addr = host.getMgmtAddr()
            # ssh connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(mgmt_addr, username=account)
            sftp_client = ssh.open_sftp()
            with sftp_client.open(self.setup_dfgw_file, "a+") as dfgw_file:
                for instance in clone_host.getInstanceList():
                    command = ""
                    for guest in instance.getCloneGuestList():
                        if len(guest.getNicGwDict()) != 0:
                            for nic,gw in guest.getNicGwDict().items():
                                if guest.getOsType() == "windows.7":
                                    add_gw_str= "route delete 0.0.0.0 mask 0.0.0.0"
                                    command += "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} \"{1}\"\n".format(guest.getNicAddrDict().values()[0], add_gw_str)
                                    add_gw_str= "route add 0.0.0.0 mask 0.0.0.0 {0}".format(gw)
                                    command += "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} \"{1}\"\n".format(guest.getNicAddrDict().values()[0], add_gw_str)
                                else:
                                    add_gw_str = "route add default gw {0} {1}".format(gw, nic)
                                    command += "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} \"{1}\"\n".format(guest.getNicAddrDict().values()[0], add_gw_str)
                    dfgw_file.write(command)


    #########################################################################
    # Generate files for creating tunnels to entry points of each cyber range.
    def create_tunnel_entry_account(self, basevm_type):
        #entry_account_list = []
        #entry_passwd_list = []
        #entry_port_list = []
        for clone_host in self.clone_setting.getCloneHostList():
            # Get mgmt_addr and account of corresponding host.
            for host in self.host_list:
                if clone_host.getHostId() == host.getHostId():
                    account = host.getAccount()
                    mgmt_addr = host.getMgmtAddr()
            # ssh connection.
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(mgmt_addr, username=account)
            sftp_client = ssh.open_sftp()
            with sftp_client.open(self.create_tunnels_file, "a+") as tunnel_file:
                # Get entry_point from each instance.
                for instance in clone_host.getInstanceList():
                    # Create tunnels following the gateway mode.
                    if self.gw_mode:
                        # Create tunnel on the crond-gw machine with tunnel name is "ct{range_id}{port}".
                        command = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}@{1} -f \"bash -c 'exec -a ct{2}_{3} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -f -L 0.0.0.0:{3}:{4}:{3} {0}@localhost -N'\";\n".format(self.gw_account, self.gw_addr, self.clone_setting.getRangeId(), instance.getEntryPoint().getPort(), mgmt_addr)
                        # Create tunnel in the corresponding host.
                        command += "bash -c 'exec -a ct{0}_{1} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -f -L 0.0.0.0:{1}:{2}:22 {3}@localhost -N'\n".format(self.clone_setting.getRangeId(), instance.getEntryPoint().getPort(), instance.getEntryPoint().getAddr(), account)
                    # Create tunnels following the un-gateway mode.
                    else:
                        for guest in instance.getCloneGuestList():
                            if guest.getIsEntryPoint()==True:
                                os_type=guest.getOsType()
                        if os_type=="windows.7":
                            command = "bash -c 'exec -a ct{0}_{1} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -f -L 0.0.0.0:{1}:{2}:3389 {3}@localhost -N'\n".format(self.clone_setting.getRangeId(), instance.getEntryPoint().getPort(), instance.getEntryPoint().getAddr(), account)
                        else:
                            command = "bash -c 'exec -a ct{0}_{1} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -f -L 0.0.0.0:{1}:{2}:22 {3}@localhost -N'\n".format(self.clone_setting.getRangeId(), instance.getEntryPoint().getPort(), instance.getEntryPoint().getAddr(), account)
                    # Execute command.
                    tunnel_file.write(command)
                command = "chmod +x {0};\n".format(self.destruction_file)
                tunnel_file.write(command)
            
            # Write commands to create entry accounts.
            with sftp_client.open(self.create_entry_accounts_file, "a+") as entry_file:
                # For each entry element in the dictionary of {key="entry_point addr", value="port"}.
                for instance in clone_host.getInstanceList():
                    # Create random account and passwd.
                    FULL_NAME="" # No full name setting for the trainee account
                    command = ManageUsers(instance.getEntryPoint().getAddr(), self.abspath).add_account(instance.getEntryPoint().getAccount(), instance.getEntryPoint().getPasswd(), FULL_NAME, os_type, basevm_type).getCommand()
                    entry_file.write("{0};\n".format(command))

            # Write commands to destruct tunnels using tunnel names.
            with sftp_client.open(self.destruction_file, "a+") as destroy_file:
                for instance in clone_host.getInstanceList():
                    # Gateway mode.
                    if self.gw_mode:
                        command = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}@{1} \"pkill -f ct{2}_{3}\";\n".format(self.gw_account, self.gw_addr, self.clone_setting.getRangeId(), instance.getEntryPoint().getPort())
                        command += "pkill -f ct{0}_{1};\n".format(self.clone_setting.getRangeId(), instance.getEntryPoint().getPort())
                    else:
                        command = "pkill -f ct{0}_{1};\n".format(self.clone_setting.getRangeId(), instance.getEntryPoint().getPort())
                    destroy_file.write(command)


    #########################################################################
    # Generate files for installing commands on individual cloned guest

    # This function is for the old approach: user specifies a file on the local physical host,
    # and CyRIS will copy the file into the cyber range and execute it there, then delete it.
    # For the new approach, refer to the function after this one
    def copy_install_prg_afcln(self, dict_guest_prg_afcln):
        for clone_host in self.clone_setting.getCloneHostList():
            # Get mgmt_addr and account of corresponding host
            for host in self.host_list:
                if clone_host.getHostId() == host.getHostId():
                    account = host.getAccount()
                    mgmt_addr = host.getMgmtAddr()
            # ssh connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(mgmt_addr, username=account)
            sftp_client = ssh.open_sftp()
            with sftp_client.open(self.install_prg_afcln_file, "a+") as install_file: 
                for instance in clone_host.getInstanceList():
                    for guest in instance.getCloneGuestList():
                        # If the guest is in the dict of dict_guest_prg_afcln, 
                        # write down the commands need to be performed.
                        if guest.getGuestId() in dict_guest_prg_afcln.keys():
                            guest_addr = guest.getNicAddrDict()["eth0"]
                            program_list = dict_guest_prg_afcln[guest.getGuestId()]
                            for program in program_list:
                                install_file.write("{0};\n".format(program.command_post_clone(guest_addr).getCommand()))

    # This function is for executing scripts after the cloning step. User copies the file to the
    # base image in advance using the "copy" task, then uses this function to execute them afterwards.
    def install_prg_afcln(self, dict_guest_prg_afcln):
        for clone_host in self.clone_setting.getCloneHostList():
            # Get mgmt_addr and account of corresponding host.
            for host in self.host_list:
                if clone_host.getHostId() == host.getHostId():
                    account = host.getAccount()
                    mgmt_addr = host.getMgmtAddr()
            # ssh connection.
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(mgmt_addr, username=account)
            sftp_client = ssh.open_sftp()
            with sftp_client.open(self.install_prg_afcln_file, "a+") as install_file: 
                for instance in clone_host.getInstanceList():
                    for guest in instance.getCloneGuestList():
                        # If the guest is in the dict of dict_guest_prg_afcln, 
                        # write down the commands need to be performed.
                        if guest.getGuestId() in dict_guest_prg_afcln.keys():
                            guest_addr = guest.getNicAddrDict()["eth0"]
                            program_list = dict_guest_prg_afcln[guest.getGuestId()]
                            for program in program_list:
                                install_file.write("TARGET=\"{0}\";".format(guest_addr))
                                install_file.write("COMTAGPREFIX=\"{0}\";".format(guest.getMidId()))
                                origwrap = program.command_post_clone(guest_addr).getCommand()
                                qbox = CyVarBox()
                                qbox.entry1("instance_index", guest.up_instance)
                                qbox.entry1("guest_index", guest.index)
                                qbox.entry1("trainee", instance.entry_point.getAccount())
                                cookwrap = qbox.safe_project_URLchunks(origwrap)
                                install_file.write("{0};\n".format(cookwrap))
                                install_file.write("{0};\n".format(program.command_post_clone(guest_addr).getCommand()))

    #########################################################################
    # Generate the whole cyber range destruction file
    def create_destruction_file(self):
        for host in self.host_list:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host.getMgmtAddr(), username=host.getAccount())
            sftp_client = ssh.open_sftp()
            with sftp_client.open(self.destruction_file, "a+") as f:
                # down the bridges
                f.write("sudo python {0}{1}/downbridges.py /etc/network/interfaces {2};\n".format(self.abspath, CLEANUP_DIR, self.clone_setting.getRangeId()))
                # delete vms
                # TODO: Script should be in cleanup directory...
                f.write("{0}{3}/vm_clone/vm_destroy_xml.sh {1} {2};\n".format(self.abspath, self.clone_setting.getRangeId(), self.directory, INSTANTIATION_DIR))
                f.write("rm {0};".format(self.destruction_file))
