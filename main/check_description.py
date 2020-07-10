#!/usr/bin/python

import yaml
import os
import re

from storyboard import Storyboard

FLAG = True

DEBUG = False


def raise_flag(error):
    print("* ERROR: check_description:", error)
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

# Determine the set of networks that appear in the forwarding rules, both
# as src and dst


def get_network_set(fw_rules):
    src_set = set()
    dst_set = set()
    for rule in fw_rules:
        elements = rule.strip().split(" ")
        for e in elements:
            # Add src networks to set (comma separated values allowed, but no
            # space)
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
    except IOError as e:
        raise_flag(e)
        return FLAG
    except yaml.YAMLError as e:
        raise_flag(e)
        return FLAG

    # For each playbook in the training description.
    host_section = doc[0]
    guest_section = doc[1]
    clone_section = doc[2]

    for element in doc:
        if isinstance(element, dict):
            if Storyboard.HOST_SETTINGS in list(element.keys()):
                host_section = element
            elif Storyboard.GUEST_SETTINGS in list(element.keys()):
                guest_section = element
            elif Storyboard.CLONE_SETTINGS in list(element.keys()):
                clone_section = element
            else:
                raise_flag(
                    "Unknown section in description file: {0}".format(element))
        else:
            raise_flag(
                "Unknown element in description file: {0}".format(element))

    # Store all guest and host ids that were defined in the
    # host_settings section, as well as forwarding rules
    defined_guest_ids = []
    defined_host_ids = []
    defined_forwarding_rules = []

    ###########################################################################
    # Check the HOST_SETTINGS section
    if Storyboard.HOST_SETTINGS not in list(host_section.keys()):
        raise_flag(
            "Section '{0}' is missing.".format(
                Storyboard.HOST_SETTINGS))
    else:
        # for index, host in enumerate(host_section[Storyboard.HOST_SETTINGS]):
        for host in host_section[Storyboard.HOST_SETTINGS]:

            host_id = Storyboard.NOT_AVAIL
            host_keys = list(host.keys())

            # ID tag
            if Storyboard.ID not in host_keys:
                raise_flag(
                    "Tag '{0}' is missing for one of the hosts in section '{1}'.".format(
                        Storyboard.ID, Storyboard.HOST_SETTINGS))
            else:
                host_id = host[Storyboard.ID]
                if not host_id in defined_host_ids:
                    defined_host_ids.append(host_id)
                else:
                    raise_flag(
                        "Host with id '{0}' is duplicated in section '{1}'.".format(
                            host_id, Storyboard.HOST_SETTINGS))
                host_keys.remove(Storyboard.ID)

            # MGMT_ADDR tag
            if Storyboard.MGMT_ADDR not in host_keys:
                raise_flag(
                    "Tag '{0}' is missing for host '{1}' in section '{2}' section.".format(
                        Storyboard.MGMT_ADDR, host_id, Storyboard.HOST_SETTINGS))
            else:
                host_keys.remove(Storyboard.MGMT_ADDR)

            # VIRBR_ADDR tag
            if Storyboard.VIRBR_ADDR not in host_keys:
                raise_flag("Tag '{0}' is missing for host '{1}' in section '{2}'.".format(
                    Storyboard.VIRBR_ADDR, host_id, Storyboard.HOST_SETTINGS))
            else:
                host_keys.remove(Storyboard.VIRBR_ADDR)

            # ACCOUNT tag
            if Storyboard.ACCOUNT not in host_keys:
                raise_flag("Tag '{0}' is missing for host '{1}' in section '{2}.".format(
                    Storyboard.ACCOUNT, host_id, Storyboard.HOST_SETTINGS))
            else:
                host_keys.remove(Storyboard.ACCOUNT)

            # Check whether there are any (unknown) tags left in the list
            if host_keys:
                raise_flag(
                    "Unknown tag(s) for host '{0}' in section '{1}': {2}".format(
                        host_id, Storyboard.HOST_SETTINGS, host_keys))

    ###########################################################################
    # Check the GUEST_SETTINGS section
    if Storyboard.GUEST_SETTINGS not in list(guest_section.keys()):
        raise_flag(
            "Section '{0}' is missing.".format(
                Storyboard.GUEST_SETTINGS))
    else:
        for guest in guest_section[Storyboard.GUEST_SETTINGS]:

            guest_id = Storyboard.NOT_AVAIL
            guest_keys = list(guest.keys())

            # ID4GUEST tag
            if Storyboard.ID4GUEST not in guest_keys:
                raise_flag(
                    "Tag '{0}' is missing for one of the guests in section '{1}'.".format(
                        Storyboard.ID4GUEST, Storyboard.GUEST_SETTINGS))
            else:
                guest_id = guest[Storyboard.ID4GUEST]
                if not guest_id in defined_guest_ids:
                    defined_guest_ids.append(guest_id)
                else:
                    raise_flag(
                        "Guest with id '{0}' is duplicated in section '{1}'.".format(
                            guest_id, Storyboard.GUEST_SETTINGS))
                guest_keys.remove(Storyboard.ID4GUEST)

            # IP_ADDR tag (optional)
            if Storyboard.IP_ADDR in guest_keys:
                guest_keys.remove(Storyboard.IP_ADDR)

            # BASEVM_HOST tag
            if Storyboard.BASEVM_HOST not in guest_keys:
                raise_flag("Tag '{0}' is missing for guest '{1}' in section '{2}'.".format(
                    Storyboard.BASEVM_HOST, guest_id, Storyboard.GUEST_SETTINGS))
            else:
                guest_keys.remove(Storyboard.BASEVM_HOST)

            # BASEVM_CONFIG_FILE tag
            if Storyboard.BASEVM_CONFIG_FILE not in guest_keys:
                raise_flag("Tag '{0}' is missing for guest '{1}' in section '{2}'.".format(
                    Storyboard.BASEVM_CONFIG_FILE, guest_id, Storyboard.GUEST_SETTINGS))
            else:
                config_file = guest[Storyboard.BASEVM_CONFIG_FILE]
                # By convention, that VM disk image has same name with the
                # config file, excluding the extension
                if ".xml" in config_file:
                    harddisk_file = config_file.replace(".xml", "")
                if DEBUG:
                    print(config_file)
                    print(harddisk_file)
                # Check whether the VM config file and disk image have valid
                # names
                if not os.path.exists(config_file):
                    raise_flag(
                        "Tag '{0}' for guest '{1}' in section '{2}' references a non-existing VM configuration file: {3}".format(
                            Storyboard.BASEVM_CONFIG_FILE,
                            guest_id,
                            Storyboard.GUEST_SETTINGS,
                            config_file))
                if not os.path.exists(harddisk_file):
                    raise_flag(
                        "Tag '{0}' for guest '{1}' in section '{2}' implies a non-existing VM disk image: {3}".format(
                            Storyboard.BASEVM_CONFIG_FILE,
                            guest_id,
                            Storyboard.GUEST_SETTINGS,
                            harddisk_file))

                guest_keys.remove(Storyboard.BASEVM_CONFIG_FILE)

            # BASEVM_TYPE tag
            if Storyboard.BASEVM_TYPE not in guest_keys:
                raise_flag("Tag '{0}' is missing for guest '{1}' in section '{2}'.".format(
                    Storyboard.BASEVM_TYPE, guest_id, Storyboard.GUEST_SETTINGS))
            else:
                guest_keys.remove(Storyboard.BASEVM_TYPE)

            # BASEVM_OS_TYPE tag (optional)
            if Storyboard.BASEVM_OS_TYPE in guest_keys:
                guest_keys.remove(Storyboard.BASEVM_OS_TYPE)

            # TASKS tag
            if Storyboard.TASKS in guest_keys:
                for task in guest[Storyboard.TASKS]:

                    task_keys = list(task.keys())

                    # ADD_ACCOUNT tag
                    if Storyboard.ADD_ACCOUNT in task_keys:
                        for account in task[Storyboard.ADD_ACCOUNT]:

                            account_keys = list(account.keys())

                            # ACCOUNT tag
                            if Storyboard.ACCOUNT not in account_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.ACCOUNT,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.ADD_ACCOUNT,
                                        guest_id))
                            else:
                                account_keys.remove(Storyboard.ACCOUNT)

                            # PASSWD tag
                            if Storyboard.PASSWD not in account_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.PASSWD,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.ADD_ACCOUNT,
                                        guest_id))
                            else:
                                account_keys.remove(Storyboard.PASSWD)

                            # FULL_NAME tag (optional)
                            if Storyboard.FULL_NAME in account_keys:
                                account_keys.remove(Storyboard.FULL_NAME)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if account_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS, Storyboard.TASKS, Storyboard.ADD_ACCOUNT, guest_id, account_keys))

                        task_keys.remove(Storyboard.ADD_ACCOUNT)

                    # MODIFY_ACCOUNT tag
                    if Storyboard.MODIFY_ACCOUNT in task_keys:
                        for account in task[Storyboard.MODIFY_ACCOUNT]:

                            account_keys = list(account.keys())

                            # ACCOUNT tag
                            if Storyboard.ACCOUNT not in account_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.ACCOUNT,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.MODIFY_ACCOUNT,
                                        guest_id))
                            else:
                                account_keys.remove(Storyboard.ACCOUNT)

                            # NEW_ACCOUNT and/or NEW_PASSWD tags
                            new_tag_present = False
                            if Storyboard.NEW_ACCOUNT in account_keys:
                                new_tag_present = True
                                account_keys.remove(Storyboard.NEW_ACCOUNT)
                            if Storyboard.NEW_PASSWD in account_keys:
                                new_tag_present = True
                                account_keys.remove(Storyboard.NEW_PASSWD)
                            if not new_tag_present:
                                raise_flag(
                                    "Neither tag '{0}' nor '{1}' are present in section '{2}', subsection '{3}' for task '{4}' of guests '{5}'.".format(
                                        Storyboard.NEW_ACCOUNT,
                                        Storyboard.NEW_PASSWD,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.MODIFY_ACCOUNT,
                                        guest_id))

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if account_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.MODIFY_ACCOUNT,
                                        guest_id,
                                        account_keys))

                        task_keys.remove(Storyboard.MODIFY_ACCOUNT)

                    # INSTALL_PACKAGE tag
                    if Storyboard.INSTALL_PACKAGE in task_keys:
                        for package in task[Storyboard.INSTALL_PACKAGE]:

                            package_keys = list(package.keys())

                            # PACKAGE_MANAGER tag (optional)
                            if Storyboard.PACKAGE_MANAGER in package_keys:
                                package_keys.remove(Storyboard.PACKAGE_MANAGER)

                            # NAME4PACKAGE tag
                            if Storyboard.NAME4PACKAGE not in package_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.NAME4PACKAGE,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.INSTALL_PACKAGE,
                                        guest_id))
                            else:
                                package_keys.remove(Storyboard.NAME4PACKAGE)

                            # VERSION tag (optional)
                            if Storyboard.VERSION in package_keys:
                                package_keys.remove(Storyboard.VERSION)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if package_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.INSTALL_PACKAGE,
                                        guest_id,
                                        package_keys))

                        task_keys.remove(Storyboard.INSTALL_PACKAGE)

                    # EMULATE_ATTACK tag
                    if Storyboard.EMULATE_ATTACK in task_keys:
                        for attack in task[Storyboard.EMULATE_ATTACK]:

                            attack_keys = list(attack.keys())

                            # ATTACK_TYPE tag
                            if Storyboard.ATTACK_TYPE not in attack_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.ATTACK_TYPE,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_ATTACK,
                                        guest_id))
                            else:
                                attack_keys.remove(Storyboard.ATTACK_TYPE)

                            # TARGET_ACCOUNT type
                            if Storyboard.TARGET_ACCOUNT not in attack_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.TARGET_ACCOUNT,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_ATTACK,
                                        guest_id))
                            else:
                                attack_keys.remove(Storyboard.TARGET_ACCOUNT)

                            # ATTEMPT_NUMBER tag
                            if Storyboard.ATTEMPT_NUMBER not in attack_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.ATTEMPT_NUMBER,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_ATTACK,
                                        guest_id))
                            else:
                                attack_keys.remove(Storyboard.ATTEMPT_NUMBER)

                            # ATTACK_TIME tag (optional)
                            if Storyboard.ATTACK_TIME in attack_keys:
                                # Check parameter format is correct
                                attack_time = attack[Storyboard.ATTACK_TIME]
                                time_pattern1 = re.compile(
                                    "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]")
                                time_pattern2 = re.compile(
                                    "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]")
                                if not time_pattern1.match(
                                        str(attack_time)) and not time_pattern2.match(str(attack_time)):
                                    raise_flag(
                                        "Format for value of tag '{0}' in section '{1}', subsection '{2}' for task '{3}' of guest '{4}' doesn't match pattern YYYY[-]MM[-]DD: {5}".format(
                                            Storyboard.ATTACK_TIME,
                                            Storyboard.GUEST_SETTINGS,
                                            Storyboard.TASKS,
                                            Storyboard.EMULATE_ATTACK,
                                            guest_id,
                                            attack_time))
                                attack_keys.remove(Storyboard.ATTACK_TIME)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if attack_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_ATTACK,
                                        guest_id,
                                        attack_keys))

                        task_keys.remove(Storyboard.EMULATE_ATTACK)

                    # EMULATE_TRAFFIC_CAPTURE_FILE tag
                    if Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE in task_keys:
                        for capture in task[Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE]:

                            attack_type = Storyboard.NOT_AVAIL
                            capture_keys = list(capture.keys())

                            # FORMAT tag
                            if Storyboard.FORMAT not in capture_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.FORMAT,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE,
                                        guest_id))
                            else:
                                capture_keys.remove(Storyboard.FORMAT)

                            # FILE_NAME tag
                            if Storyboard.FILE_NAME not in capture_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.FILE_NAME,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE,
                                        guest_id))
                            else:
                                capture_keys.remove(Storyboard.FILE_NAME)

                            # ATTACK_TYPE tag
                            if Storyboard.ATTACK_TYPE not in capture_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.ATTACK_TYPE,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE,
                                        guest_id))
                            else:
                                attack_type = capture[Storyboard.ATTACK_TYPE]
                                capture_keys.remove(Storyboard.ATTACK_TYPE)

                            # ATTACK_SOURCE tag
                            if Storyboard.ATTACK_SOURCE not in capture_keys:
                                if attack_type == Storyboard.SSH_ATTACK:
                                    raise_flag(
                                        "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}' (attack type '{5}').".format(
                                            Storyboard.ATTACK_SOURCE,
                                            Storyboard.GUEST_SETTINGS,
                                            Storyboard.TASKS,
                                            Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE,
                                            guest_id,
                                            attack_type))
                                else:
                                    # Nothing to do, since this tag is only
                                    # required for the above attack
                                    pass
                            else:
                                capture_keys.remove(Storyboard.ATTACK_SOURCE)

                            # NOISE_LEVEL tag
                            if Storyboard.NOISE_LEVEL not in capture_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.NOISE_LEVEL,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE,
                                        guest_id))
                            else:
                                capture_keys.remove(Storyboard.NOISE_LEVEL)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if capture_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE,
                                        guest_id,
                                        capture_keys))

                        task_keys.remove(
                            Storyboard.EMULATE_TRAFFIC_CAPTURE_FILE)

                    # EMULATE_MALWARE tag
                    if Storyboard.EMULATE_MALWARE in task_keys:
                        for malware in task[Storyboard.EMULATE_MALWARE]:

                            malware_mode = Storyboard.NOT_AVAIL
                            malware_keys = list(malware.keys())

                            # NAME4MALWARE tag
                            if Storyboard.NAME4MALWARE not in malware_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.NAME4MALWARE,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_MALWARE,
                                        guest_id))
                            else:
                                malware_keys.remove(Storyboard.NAME4MALWARE)

                            # MODE tag
                            if Storyboard.MODE not in malware_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.MODE,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_MALWARE,
                                        guest_id))
                            else:
                                malware_mode = malware[Storyboard.MODE]
                                malware_keys.remove(Storyboard.MODE)

                            # CPU_UTILIZATION tag
                            if Storyboard.CPU_UTILIZATION not in malware_keys:
                                if malware_mode == Storyboard.DUMMY_CALCULATION:
                                    raise_flag(
                                        "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}' (mode '{5}').".format(
                                            Storyboard.CPU_UTILIZATION,
                                            Storyboard.GUEST_SETTINGS,
                                            Storyboard.TASKS,
                                            Storyboard.EMULATE_MALWARE,
                                            guest_id,
                                            malware_mode))
                                else:
                                    pass
                            else:
                                malware_keys.remove(Storyboard.CPU_UTILIZATION)

                            # PORT tag
                            if Storyboard.PORT not in malware_keys:
                                if malware_mode == Storyboard.PORT_LISTENING:
                                    raise_flag(
                                        "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}' (mode '{5}').".format(
                                            Storyboard.PORT,
                                            Storyboard.GUEST_SETTINGS,
                                            Storyboard.TASKS,
                                            Storyboard.EMULATE_MALWARE,
                                            guest_id,
                                            malware_mode))
                                else:
                                    pass
                            else:
                                malware_keys.remove(Storyboard.PORT)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if malware_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EMULATE_MALWARE,
                                        guest_id,
                                        malware_keys))

                        task_keys.remove(Storyboard.EMULATE_MALWARE)

                    # COPY_CONTENT tag
                    if Storyboard.COPY_CONTENT in task_keys:
                        for content in task[Storyboard.COPY_CONTENT]:

                            content_keys = list(content.keys())

                            # SRC tag
                            if Storyboard.SRC not in content_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.SRC,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.COPY_CONTENT,
                                        guest_id))
                            else:
                                content_keys.remove(Storyboard.SRC)

                            # DST tag
                            if Storyboard.DST not in content_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.DST,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.COPY_CONTENT,
                                        guest_id))
                            else:
                                content_keys.remove(Storyboard.DST)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if content_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS, Storyboard.TASKS, Storyboard.COPY_CONTENT, guest_id, content_keys))

                        task_keys.remove(Storyboard.COPY_CONTENT)

                    # EXECUTE_PROGRAM tag
                    if Storyboard.EXECUTE_PROGRAM in task_keys:
                        for program in task[Storyboard.EXECUTE_PROGRAM]:

                            program_keys = list(program.keys())

                            # PROGRAM tag
                            if Storyboard.PROGRAM not in program_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.PROGRAM,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EXECUTE_PROGRAM,
                                        guest_id))
                            else:
                                program_keys.remove(Storyboard.PROGRAM)

                            # ARGS tag (optional)
                            if Storyboard.ARGS in program_keys:
                                program_keys.remove(Storyboard.ARGS)

                            # INTERPRETER tag
                            if Storyboard.INTERPRETER not in program_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.INTERPRETER,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EXECUTE_PROGRAM,
                                        guest_id))
                            else:
                                program_keys.remove(Storyboard.INTERPRETER)

                            # EXECUTE_TIME tag (optional)
                            if Storyboard.EXECUTE_TIME in program_keys:
                                program_keys.remove(Storyboard.EXECUTE_TIME)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if program_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.EXECUTE_PROGRAM,
                                        guest_id,
                                        program_keys))

                        task_keys.remove(Storyboard.EXECUTE_PROGRAM)

                    # FIREWALL_RULES tag
                    if Storyboard.FIREWALL_RULES in task_keys:
                        for rule in task[Storyboard.FIREWALL_RULES]:

                            rule_keys = list(rule.keys())

                            # RULE tag
                            if Storyboard.RULE not in rule_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for task '{3}' of guest '{4}'.".format(
                                        Storyboard.RULE,
                                        Storyboard.GUEST_SETTINGS,
                                        Storyboard.TASKS,
                                        Storyboard.FIREWALL_RULES,
                                        guest_id))
                            else:
                                rule_keys.remove(Storyboard.RULE)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if program_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}' for task '{2}' of guest '{3}': {4}".format(
                                        Storyboard.GUEST_SETTINGS, Storyboard.TASKS, Storyboard.FIREWALL_RULES, guest_id, rule_keys))

                        task_keys.remove(Storyboard.FIREWALL_RULES)

                    # Check whether there are any (unknown) tags left in the
                    # list
                    if task_keys:
                        raise_flag(
                            "Unknown tag in section '{0}', subsection '{1}': {2}".format(
                                Storyboard.GUEST_SETTINGS, Storyboard.TASKS, task_keys))

                guest_keys.remove(Storyboard.TASKS)

            # Check whether there are any (unknown) tags left in the list
            if guest_keys:
                raise_flag(
                    "Unknown tag(s) in section '{0}': {1}".format(
                        Storyboard.GUEST_SETTINGS, guest_keys))

    ###########################################################################
    # Check the CLONE_SETTINGS section
    if Storyboard.CLONE_SETTINGS not in list(clone_section.keys()):
        raise_flag(
            "Section '{0}' is missing.".format(
                Storyboard.CLONE_SETTINGS))
    else:

        # Check syntax and keywords
        # Only one clone entry is supported in CLONE_SETTINGS, so we just get the first element
        # TODO: Print error if more entries are found
        clone = clone_section[Storyboard.CLONE_SETTINGS][0]
        clone_keys = list(clone.keys())

        # RANGE_ID tag
        if Storyboard.RANGE_ID not in clone_keys:
            raise_flag(
                "Tag '{0}' is missing in section '{1}'.".format(
                    Storyboard.RANGE_ID,
                    Storyboard.CLONE_SETTINGS))
        else:
            range_id = int(clone[Storyboard.RANGE_ID])
            cr_id_list = get_existed_cr_id_list(abspath)
            if range_id in cr_id_list:
                raise_flag(
                    "Range with id '{0}' already exists. Please choose another id.".format(range_id))
            clone_keys.remove(Storyboard.RANGE_ID)

        # HOSTS tag
        if Storyboard.HOSTS not in clone_keys:
            raise_flag(
                "Tag '{0}' is missing in section '{1}'.".format(
                    Storyboard.HOSTS,
                    Storyboard.CLONE_SETTINGS))
        else:
            for host in clone[Storyboard.HOSTS]:

                host_id = Storyboard.NOT_AVAIL
                host_keys = list(host.keys())

                # HOST_ID tag
                if Storyboard.HOST_ID not in host_keys:
                    raise_flag("Tag '{0}' is missing in section '{1}', subsection '{2}'.".format(
                        Storyboard.HOST_ID, Storyboard.CLONE_SETTINGS, Storyboard.HOSTS))
                else:
                    # Check whether the host id was already defined in the
                    # host_settings section
                    host_id = host[Storyboard.HOST_ID]
                    # Convert to list of hosts, in case comma-separated format is used
                    # (and make sure to remove potential spaces first)
                    host_id_list = host_id.replace(" ", "").split(",")
                    for host_id_item in host_id_list:
                        # Check host id existence
                        if host_id_item not in defined_host_ids:
                            raise_flag(
                                "Host with id '{0}' mentioned in section '{1}', subsection '{2}' was not defined in the section '{3}'.".format(
                                    host_id_item, Storyboard.CLONE_SETTINGS, Storyboard.HOSTS, Storyboard.HOST_SETTINGS))
                    host_keys.remove(Storyboard.HOST_ID)

                # INSTANCE_NUMBER tag
                if Storyboard.INSTANCE_NUMBER not in host_keys:
                    raise_flag("Tag '{0}' is missing in section '{1}', subsection '{2}'.".format(
                        Storyboard.INSTANCE_NUMBER, Storyboard.CLONE_SETTINGS, Storyboard.HOSTS))
                else:
                    host_keys.remove(Storyboard.INSTANCE_NUMBER)

                # GUESTS tag
                if Storyboard.GUESTS not in host_keys:
                    raise_flag("Tag '{0}' is missing in section '{1}', subsection '{2}'.".format(
                        Storyboard.GUESTS, Storyboard.CLONE_SETTINGS, Storyboard.HOSTS))
                else:
                    entry_point_count = 0
                    for guest in host[Storyboard.GUESTS]:
                        hosts_guest_keys = list(guest.keys())

                        # GUEST_ID tag
                        if Storyboard.GUEST_ID not in hosts_guest_keys:
                            raise_flag(
                                "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}' of host '{4}'.".format(
                                    Storyboard.GUEST_ID,
                                    Storyboard.CLONE_SETTINGS,
                                    Storyboard.HOSTS,
                                    Storyboard.GUESTS,
                                    host_id))
                        else:
                            guest_id = guest[Storyboard.GUEST_ID]
                            if guest_id not in defined_guest_ids:
                                raise_flag(
                                    "Guest with id '{0}' mentioned in section '{1}', subsection '{2}' was not defined in the section '{3}'.".format(
                                        guest_id, Storyboard.CLONE_SETTINGS, Storyboard.GUESTS, Storyboard.GUEST_SETTINGS))
                            hosts_guest_keys.remove(Storyboard.GUEST_ID)

                        # NUMBER tag
                        # TODO: Add guest_id to messages
                        if Storyboard.NUMBER not in hosts_guest_keys:
                            raise_flag(
                                "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}' of host '{4}'.".format(
                                    Storyboard.NUMBER,
                                    Storyboard.CLONE_SETTINGS,
                                    Storyboard.HOSTS,
                                    Storyboard.GUESTS,
                                    host_id))
                        else:
                            hosts_guest_keys.remove(Storyboard.NUMBER)

                        # ENTRY_POINT tag
                        if Storyboard.ENTRY_POINT in hosts_guest_keys:
                            entry_point_count += 1
                            hosts_guest_keys.remove(Storyboard.ENTRY_POINT)

                        # FORWARDING_RULES tag
                        if Storyboard.FORWARDING_RULES in hosts_guest_keys:
                            defined_forwarding_rules = []
                            for rule_set in guest[Storyboard.FORWARDING_RULES]:
                                if Storyboard.RULE not in list(
                                        rule_set.keys()):
                                    raise_flag(
                                        "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}', subsubsection '{4}' of host '{5}'.".format(
                                            Storyboard.RULE,
                                            Storyboard.CLONE_SETTINGS,
                                            Storyboard.HOSTS,
                                            Storyboard.GUESTS,
                                            Storyboard.FORWARDING_RULES,
                                            host_id))
                                else:
                                    defined_forwarding_rules.append(
                                        rule_set[Storyboard.RULE])
                            hosts_guest_keys.remove(
                                Storyboard.FORWARDING_RULES)

                        # Check whether there are any (unknown) tags left in
                        # the list
                        if hosts_guest_keys:
                            raise_flag(
                                "Unknown tag(s) in section '{0}', subsection '{1}', for subsection '{2}' of host '{3}': {4}".format(
                                    Storyboard.CLONE_SETTINGS, Storyboard.HOSTS, Storyboard.GUESTS, host_id, host_keys))

                    # TODO: How to check this in case multiple hosts are used?!
                    if entry_point_count == 0:
                        raise_flag(
                            "Tag '{0}' doesn't appear for any guest in section '{1}', subsection '{2}' for subsection '{3}' of host '{4}'.".format(
                                Storyboard.ENTRY_POINT,
                                Storyboard.CLONE_SETTINGS,
                                Storyboard.HOSTS,
                                Storyboard.GUESTS,
                                host_id))
                    if entry_point_count > 1:
                        raise_flag(
                            "Tag '{0}' appears for more than one guest in section '{1}', subsection '{2}' for subsection '{3}' of host '{4}'.".format(
                                Storyboard.ENTRY_POINT,
                                Storyboard.CLONE_SETTINGS,
                                Storyboard.HOSTS,
                                Storyboard.GUESTS,
                                host_id))

                    host_keys.remove(Storyboard.GUESTS)

                # TOPOLOGY tag
                if Storyboard.TOPOLOGY not in host_keys:
                    raise_flag(
                        "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}' of host '{4}'.".format(
                            Storyboard.TOPOLOGY,
                            Storyboard.CLONE_SETTINGS,
                            Storyboard.HOSTS,
                            Storyboard.GUESTS,
                            host_id))
                else:
                    topology = host[Storyboard.TOPOLOGY][0]
                    topology_keys = list(topology.keys())

                    # TYPE tag
                    if Storyboard.TYPE not in topology_keys:
                        raise_flag(
                            "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}' of host '{4}'.".format(
                                Storyboard.TYPE,
                                Storyboard.CLONE_SETTINGS,
                                Storyboard.HOSTS,
                                Storyboard.TOPOLOGY,
                                host_id))
                    else:
                        topology_keys.remove(Storyboard.TYPE)

                    # NETWORKS tag
                    if Storyboard.NETWORKS not in topology_keys:
                        raise_flag(
                            "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}' of host '{4}'.".format(
                                Storyboard.NETWORKS,
                                Storyboard.CLONE_SETTINGS,
                                Storyboard.HOSTS,
                                Storyboard.TOPOLOGY,
                                host_id))
                    else:
                        # Process each network definition, and check whether the forwarding rules specified previously
                        # contain any undefined networks
                        nw_set = get_network_set(defined_forwarding_rules)
                        for network in topology[Storyboard.NETWORKS]:

                            nw_name = Storyboard.NOT_AVAIL
                            network_keys = list(network.keys())

                            # NAME tag
                            if Storyboard.NAME not in network_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}', subsubsection '{4}' of host '{5}'.".format(
                                        Storyboard.NAME,
                                        Storyboard.CLONE_SETTINGS,
                                        Storyboard.HOSTS,
                                        Storyboard.TOPOLOGY,
                                        Storyboard.NETWORKS,
                                        host_id))
                            else:
                                nw_name = network[Storyboard.NAME]
                                # If network name present in nw_set, remove it
                                # to signify it was defined already
                                if nw_name in nw_set:
                                    nw_set.remove(nw_name)
                                network_keys.remove(Storyboard.NAME)

                            # MEMBERS tag
                            if Storyboard.MEMBERS not in network_keys:
                                raise_flag(
                                    "Tag '{0}' is missing in section '{1}', subsection '{2}' for subsection '{3}', subsubsection '{4}' of host '{5}'.".format(
                                        Storyboard.MEMBERS,
                                        Storyboard.CLONE_SETTINGS,
                                        Storyboard.HOSTS,
                                        Storyboard.TOPOLOGY,
                                        Storyboard.NETWORKS,
                                        host_id))
                            else:
                                network_keys.remove(Storyboard.MEMBERS)

                            # GATEWAY tag
                            if Storyboard.GATEWAY in network_keys:
                                network_keys.remove(Storyboard.GATEWAY)

                            # Check whether there are any (unknown) tags left
                            # in the list
                            if network_keys:
                                raise_flag(
                                    "Unknown tag(s) in section '{0}', subsection '{1}', for subsection '{2}', subsubsection '{3}' of host '{4}', network '{5}': {6}".format(
                                        Storyboard.CLONE_SETTINGS,
                                        Storyboard.HOSTS,
                                        Storyboard.GUESTS,
                                        Storyboard.TOPOLOGY,
                                        host_id,
                                        nw_name,
                                        network_keys))

                        # If there are still elements in nw_set, it means that the forwarding rules specified
                        # previously contain undefined networks
                        if nw_set:
                            raise_flag(
                                "Undefined network(s) in section '{0}', subsection '{1}' for subsection '{2}', subsubsection '{3}' for host '{4}': {5}".format(
                                    Storyboard.CLONE_SETTINGS,
                                    Storyboard.HOSTS,
                                    Storyboard.GUESTS,
                                    Storyboard.FORWARDING_RULES,
                                    host_id,
                                    list(nw_set)))

                        topology_keys.remove(Storyboard.NETWORKS)

                    # Check whether there are any (unknown) tags left in the
                    # list
                    if topology_keys:
                        raise_flag(
                            "Unknown tag(s) in section '{0}', subsection '{1}', for subsection '{2}', subsubsection '{3}' of host '{4}': {5}".format(
                                Storyboard.CLONE_SETTINGS,
                                Storyboard.HOSTS,
                                Storyboard.GUESTS,
                                Storyboard.TOPOLOGY,
                                host_id,
                                host_keys))

                    host_keys.remove(Storyboard.TOPOLOGY)

                # Check whether there are any (unknown) tags left in the list
                if host_keys:
                    raise_flag(
                        "Unknown tag(s) in section '{0}', subsection '{1}': {2}".format(
                            Storyboard.CLONE_SETTINGS, Storyboard.HOSTS, host_keys))

            clone_keys.remove(Storyboard.HOSTS)

        # Check whether there are any (unknown) tags left in the list
        if clone_keys:
            raise_flag(
                "Unknown tag(s) in section '{0}': {1}".format(
                    Storyboard.CLONE_SETTINGS,
                    clone_keys))

    return FLAG
