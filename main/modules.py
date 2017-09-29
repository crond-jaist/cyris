#!/usr/bin/python

#############################################################################
# Classes of CyRIS features
#############################################################################

INSTANTIATION_DIR = "instantiation"

# External imports
from entities import Command

#########################################################################
# Class Modules is the parent class of every other modules / features
class Modules(object):
    def __init__(self, name, abspath):
	self.name = name
        self.abspath = abspath

    def getName(self):
	return self.name

    def getAbsPath(self):
        return self.abspath
############################################################
# Copy ssh keygen from the local machine to a remote one
class SSHKeygenHostname(Modules):
    def __init__(self, vm_addr, root_passwd, hostname, mstnode_account, abspath):
        Modules.__init__(self, "SSHKeygen", abspath)
        self.vm_addr = vm_addr
        self.root_passwd = root_passwd
        self.hostname = hostname
        self.mstnode_account = mstnode_account

    def command(self):
        desc = "Generate ssh keys and do hostname setup"
        command_string = "{0}{5}/sshkey_hostname_setup/sshkey_setup.sh {1} {2} {3}; {0}{5}/sshkey_hostname_setup/hostname_setup.sh {1} {2} {4};".format(self.getAbsPath(), self.vm_addr, self.root_passwd, self.mstnode_account, self.hostname, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

#########################################################################
# Manage users in the system. Contains functions for adding new accounts
# and edit info of existing accounts.
class ManageUsers(Modules):
    def __init__(self, addr, abspath):
	Modules.__init__(self, "ManageUsers", abspath)
	self.addr = addr

    def add_account(self, new_account, new_passwd, full_name):
        desc = "Add user account '{0}'".format(new_account)
        if full_name:
            full_name_arg=full_name
        else:
            full_name_arg=""

        command_string = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} 'bash -s' < {1}{5}/users_managing/add_user.sh {2} {3} yes {4}".format(self.addr, self.getAbsPath(), new_account, new_passwd, full_name_arg, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

    def modify_account(self, account, new_account, new_passwd):
        sub_desc = "new name: {0}  new password: {1}".format(new_account, new_passwd)
        if new_account == "null":
            sub_desc = "new password: {0}".format(new_passwd)
        elif new_passwd == "null":
            sub_desc = "new name: {0}".format(new_account)
        desc = "Modify user account '{0}': {1}".format(account, sub_desc)
        command_string = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{0} 'bash -s' < {1}{5}/users_managing/modify_user.sh {2} {3} {4}".format(self.addr, self.getAbsPath(), account, new_account, new_passwd, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

#########################################################################
# Install tools from (i) package manager (apt-get, yum, etc.), (ii) source
class InstallTools(Modules):
    def __init__(self, addr, account, abspath):
	Modules.__init__(self, "InstallTools", abspath)
	self.addr = addr
	self.account = account

    def package_install_command(self, package_manager, tool_name, version):
	if self.addr != "host":
            if version == "":
                desc = "Install package '{0}'".format(tool_name)
            else:
                desc = "Install package '{0}' version {1}".format(tool_name, version)
            command_string = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {0}@{1} {2} install -y {3} {4}".format(self.account, self.addr, package_manager, tool_name, version)
            command = Command(command_string, desc)
            return command
	else:
	    return "sudo {0} install -y {1} {2}".format(package_manager, tool_name, version)

    def source_install_command(self, chdir, compiler):
        return "Install source '{0}' using '{1}'".format(chdir, compiler)
    
class EmulateAttacks(Modules):
    #def __init__(self):
    #	pass
	
    def __init__(self, attack_type, target_addr, target_account, number, attack_time, abspath):
	Modules.__init__(self, "EmulateAttacks", abspath)
        self.attack_type = attack_type
	self.target_addr = target_addr
	self.target_account = target_account
	self.number = number
        self.attack_time = attack_time

    def command(self):
        if self.attack_type == "ssh_attack":
            desc = "Perform ssh attack on account '{0}' (repeat {1} times)".format(self.target_account, self.number)
            command_string = "{0}{5}/attacks_emulation/install_paramiko.sh; python {0}{5}/attacks_emulation/attack_paramiko_ssh.py {1} {2} {3} {4}".format(self.getAbsPath(), self.target_addr, self.target_account, self.number, self.attack_time, INSTANTIATION_DIR)
            command = Command(command_string, desc)
            return command

class GenerateTrafficCaptureFiles(Modules):
    def __init__(self, virbr_addr, image_addr, image_passwd, attack_type, noise_level, file_path, file_name, abspath, cr_dir):
        Modules.__init__(self, "LogsPreparation", abspath)
        self.virbr_addr = virbr_addr
        self.image_addr = image_addr
        self.image_passwd = image_passwd
        self.attack_type = attack_type
        self.noise_level = noise_level
        self.file_path = file_path
        self.file_name = file_name
        self.cr_dir = cr_dir

    def ssh_attack(self, target_account, attack_source, number):
        desc = "Generate traffic capture file containing ssh attack trace"
        command_string = "{0}{11}/logs_preparation/pcap_sshattack_generator.sh {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10}".format(self.getAbsPath(), self.virbr_addr, target_account, self.image_addr, self.image_passwd, attack_source, number, self.noise_level, self.file_path, self.file_name, self.cr_dir, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

    def ddos_attack(self):
        desc = "Generate traffic capture file containing DDoS attack trace"
        command_string = "{0}{8}/logs_preparation/pcap_ddosattack_generator.sh {0} {1} {2} {3} {4} {5} {6} {7}".format(self.getAbsPath(), self.virbr_addr, self.image_addr, self.image_passwd, self.noise_level, self.file_path, self.file_name, self.cr_dir, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

    def dos_attack(self, attack_source, dport):
        desc = "Generate traffic capture file containing DoS attack trace"
        command_string = "{0}{10}/logs_preparation/pcap_dosattack_generator.sh {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}".format(self.getAbsPath(), self.virbr_addr, self.image_addr, self.image_passwd, self.noise_level, self.file_path, self.file_name, attack_source, dport, self.cr_dir, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

class EmulateMalware(Modules):
    def __init__(self, addr, malware_name, mode, crspd_option, abspath):
        Modules.__init__(self, "EmulateMalware", abspath)
        self.addr = addr
        self.malware_name = malware_name
        self.mode = mode
        self.crspd_option = crspd_option

    def command(self):
        desc = "Deploy dummy malware"
        command_string = "{0}{5}/malware_creation/malware_launch.sh {1} {2} {3} {4} {0}".format(self.getAbsPath(), self.addr, self.malware_name, self.mode, self.crspd_option, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

class ModifyRuleset(Modules):
    def __init__(self, image_addr, image_passwd, ruleset_file, abspath):
        Modules.__init__(self, "ModifyRuleset", abspath)
        self.image_addr = image_addr
        self.image_passwd = image_passwd
        self.ruleset_file = ruleset_file

    def command(self):
        desc = "Modify firewall ruleset"
        command_string = "{0}{4}/ruleset_modification/ruleset_modify.sh {0} {1} {2} {3}".format(self.getAbsPath(), self.image_addr, self.image_passwd, self.ruleset_file, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

class CopyContent(Modules):
    def __init__(self, src, dst, image_addr, image_passwd, abspath):
        Modules.__init__(self, "CopyContent", abspath)
        self.src = src
        self.dst = dst
        self.image_addr = image_addr
        self.image_passwd = image_passwd

    def command(self):
        desc = "Copy file '{0}'".format(self.src)
        command_string = "{0}{5}/content_copy_program_run/copy_content.sh {1} {2} {3} {4}".format(self.getAbsPath(), self.src, self.dst, self.image_addr, self.image_passwd, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

class ExecuteProgram(Modules):
    def __init__(self, program, interpreter, args, image_addr, image_passwd, log_file, abspath):
        Modules.__init__(self, "ExecuteProgram", abspath)
        self.program = program
        self.interpreter = interpreter
        self.args = args
        self.image_addr = image_addr
        self.image_passwd = image_passwd
        self.log_file = log_file

    def getProgram(self):
        return self.program

    # This command_post_clone is for tasks that are required to be executed after the cloning step
    def command_post_clone(self, image_addr):
        desc = "Execute program post-cloning '{0}'".format(self.program)
        command_string = "python {0}{7}/content_copy_program_run/run_program.py {1} {2} {3} {4} {5} {6}".format(self.getAbsPath(), self.program, self.interpreter, self.args, image_addr, self.image_passwd, self.log_file, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command

    def command(self):
        desc = "Execute program '{0}'".format(self.program)
        command_string = "python {0}{7}/content_copy_program_run/run_program.py {1} {2} {3} {4} {5} {6}".format(self.getAbsPath(), self.program, self.interpreter, self.args, self.image_addr, self.image_passwd, self.log_file, INSTANTIATION_DIR)
        command = Command(command_string, desc)
        return command


class BaseImageLaunch(Modules):
    def __init__(self, xml_config, image_name, abspath):
	Modules.__init__(self, "LaunchBaseImage", abspath)
	self.xml_config = xml_config
	self.image_name = image_name

    def command(self):
	return "virsh --quiet define {0} > /dev/null; virsh --quiet start {1} > /dev/null".format(self.xml_config, self.image_name)

