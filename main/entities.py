#!/usr/bin/python

#########################################################################################
# Classes related to entities that CyRIS uses for reading the cyber range description file.
#########################################################################################

# External imports.
from collections import OrderedDict
import yaml
import string
import random
import os

# Internal imports
from storyboard import Storyboard


DEBUG = False

def represent_ordereddict(dumper, data):
    value = []
    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        value.append((node_key, node_value))
    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

yaml.add_representer(OrderedDict, represent_ordereddict)

''' 
Object host is created for containing information about hosts that are 
specified in the description. It has variables for:
    + host_id: id of the host.
    + virbr_addr: default virtual bridge that KVM uses to connect to virtual machines.
    + mgmt_addr: management address that the host uses to connect to other hosts.
    + account: account on the host for cyris to operate.
'''
class Host(object):
    def __init__(self, host_id, virbr_addr, mgmt_addr, account):
        self.host_id = host_id
        self.virbr_addr = virbr_addr
        self.mgmt_addr = mgmt_addr
        self.account = account

    def getHostId(self):
        return self.host_id

    def getVirbrAddr(self):
        return self.virbr_addr

    def getMgmtAddr(self):
        return self.mgmt_addr

    def getAccount(self):
        return self.account

    def __str__(self):
        return "host_id: " + self.getHostId() + ", virbr_addr: " + self.getVirbrAddr() + ", mgmt_addr: " + self.getMgmtAddr() + ", account: " + self.getAccount()

'''
Object guest is created for containing information of base image guests that are specified 
in the description. It has variables for:
    @param    guest_id              Id of the guest (desktop, webserver, etc.).
    @param    basevm_addr           IP address of the base image guest.
    @param    root_passwd           Password of the root account for cyris to access and operate.
    @param    basevm_host           The location of the host that has the base image guest. 
                                    Normally it is on the master host.
    @param    basevm_config_file    The location of the xml config file of the base image guest. 
                                    Normally it is in the same location of the basevm_host.
    @param    basevm_type           Type of the base image guest (raw, qcow2, etc.). This info is 
                                    not really necessary.
    @param    basevm_name           Name of the base image guest that is used by KVM to define, start or stop it.
    @param    tasks                 A list of content that are defined by instructors and supposed to install 
                                    on the base image guest.
'''
class Guest(object):
    def __init__(self, guest_id, basevm_addr, root_passwd, basevm_host, basevm_config_file, basevm_os_type, basevm_type, basevm_name, tasks):
        self.guest_id = guest_id
        self.basevm_addr = basevm_addr
        self.basevm_host = basevm_host
        self.root_passwd = root_passwd
        self.basevm_config_file = basevm_config_file
        self.basevm_os_type =basevm_os_type
        self.basevm_type = basevm_type
        self.basevm_name = basevm_name
        self.tasks = tasks

    def getGuestId(self):
        return self.guest_id

    def getBasevmAddr(self):
        return self.basevm_addr

    def setBasevmAddr(self, basevm_addr):
        self.basevm_addr = basevm_addr

    def getRootPasswd(self):
        return self.root_passwd
    
    def setRootPasswd(self, new_passwd):
        self.root_passwd = new_passwd

    def getBasevmHost(self):
        return self.basevm_host

    def getBasevmConfigFile(self):
        return self.basevm_config_file

    def setBasevmConfigFile(self, new_file):
        self.basevm_config_file = new_file

    def getBasevmOSType(self):
        return self.basevm_os_type

    def getBasevmType(self):
        return self.basevm_type

    def getBasevmName(self):
        return self.basevm_name

    def setBasevmName(self, basevm_name):
        self.basevm_name = basevm_name

    def getAddrLastBit(self):
        last_bit = self.basevm_addr.split(".")[-1]
        return last_bit 

    def getTasks(self):
        return self.tasks

'''
Object Bridges are created for connecting virtual machines with the host.
Each virtual machine network interface has one corresponding bridge.
    @param    bridge_id     The id (name) of the bridge.
    @param    addr          The IP address of the bridge.
'''
class Bridge(object):
    def __init__(self, bridge_id, addr):
        self.bridge_id = bridge_id
        self.addr = addr

    def getId(self):
        return self.bridge_id

    def getAddr(self):
        return self.addr

    def __str__(self):
        return "bridge_id: " + self.getId() + ", addr: " + self.getAddr()

'''
Object EntryPoints are created in each cyber range instance for trainees connect directly from 
outside to their environment.
    @param    addr       The address of the entry.
    @param    port       The port for trainees to connect to it via ssh connection.
    @param    account    The account that is generated randomly for the entry point.
    @param    passwd     The password that is generated randomly for the entry point.
'''
class EntryPoint(object):
    def __init__(self):
        self.addr = ""
        self.port = ""
        self.account = ""
        self.passwd = ""
        self.host_id = ""


    def getAddr(self):
        return self.addr

    def setAddr(self, addr):
        self.addr = addr

    def getPort(self):
        return self.port

    def setPort(self, port):
        self.port = port

    def getAccount(self):
        return self.account

    def setAccount(self, account):
        self.account = account

    def getPasswd(self):
        return self.passwd

    def setPasswd(self, passwd):
        self.passwd = passwd

    def getHostId(self):
        return self.host_id

    def setHostId(self, host_id):
        self.host_id = host_id

    def __str__(self):
        return "entry_point addr: " + self.getAddr() + ", port: " + str(self.getPort()) + ", account: " + self.getAccount() + ", passwd: " + self.getPasswd() + ", host_id: " + self.getHostId()

'''
Object FirewallRule is created for containing information of a firewall rule in one clone_guest.
This firewall rule is for routing traffic. It has four arguments:
    @param    src      Source ip of the incoming traffic.
    @param    dst      Destination ip of the incoming traffic.
    @param    sport    Source port.
    @param    dport    Destination port.
'''
class FirewallRule(object):
    def __init__(self, src, dst, sport, dport):
        self.src = src
        self.dst = dst
        self.sport = sport
        self.dport = dport

    def getSrc(self):
        return self.src

    def getDst(self):
        return self.dst

    def getSport(self):
        return self.sport

    def getDport(self):
        return self.dport

'''
Object CloneGuest is created for containing information of hosts that are specified as tag "guests"
in the session "clone_settings" of the cyber range description. It has two variables:
    @param    guest_id               Id of the guest that is cloned (desktop, webserver, etc.). This id has 
                                     been specified above in the "guest_settings" part of the description.
    @param    network_interfaces     List of network interfaces of that guest.
'''
class CloneGuest(object):
    #def __init__(self, guest_id, index, has_fw_setup, fwrule_desc_list, is_entry_point,os_type):
    def __init__(self, guest_id, index, instance_id, cyberrange_id, has_fw_setup, fwrule_desc_list, is_entry_point, os_type):
        self.guest_id = guest_id
        self.index = index
        self.up_instance = instance_id
        self.up_cyberrange = cyberrange_id
        self.nic_addr_dict = OrderedDict()
        self.nic_gw_dict = OrderedDict()
        self.gateway = ""
        self.has_fw_setup = has_fw_setup
        self.fwrule_desc_list = fwrule_desc_list
        self.fwrule_list = []
        self.is_entry_point = is_entry_point
        self.os_type=os_type
        self.sepchar = ","

    def getFullId(self):
        return "cr" + str(self.up_cyberrange) + self.sepchar \
                           + "ins" + str(self.up_instance) + self.sepchar \
                           + str(self.guest_id) + self.sepchar \
                           + str(self.index)

    def getMidId(self):
        return "ins" + str(self.up_instance) + self.sepchar \
               + str(self.guest_id) + self.sepchar \
               + str(self.index)

    def getGuestId(self):
        return self.guest_id

    def getIndex(self):
        return self.index

    def setIndex(self, index):
        self.index = index

    def getNicAddrDict(self):
        return self.nic_addr_dict

    def addNicAddrDict(self, nic, addr):
        self.nic_addr_dict[nic] = "{0}".format(addr)

    def getNicGwDict(self):
        return self.nic_gw_dict

    def addNicGwDict(self, nic, gw):
        self.nic_gw_dict[nic] = "{0}".format(gw)

    def getHasFwSetup(self):
        return self.has_fw_setup

    def setHasFwSetup(self, value):
        self.has_fw_setup = value

    def getFwRuleDescList(self):
        return self.fwrule_desc_list

    def getFwRuleList(self):
        return self.fwrule_list

    def setFwRuleList(self, fwrule_list):
        self.fwrule_list = fwrule_list

    def getIsEntryPoint(self):
        return self.is_entry_point

    def setIsEntryPoint(self, value):
        self.is_entry_point = value

    def getOsType(self):
        return self.os_type

    def __str__(self):
        return "guest_id: " + self.getGuestId() + ", guest_index: " + str(self.getIndex()) + ", guest_nic_addr: " + str(self.getNicAddrDict()) + ", guest_nic_gw: " + str(self.getNicGwDict()) + ", fwrule_desc: " + str(self.getFwRuleDescList()) + ", fwrule_list: " + str(self.getFwRuleList()) + ", is_entry_point: " + str(self.getIsEntryPoint())

'''
Object SubNetwork is created for containing information of a subnetwork in the cyber range
description. It has two variables:
    @param    name            Describe name of the subnetwork.
    @param    member_list     Describe elements in the subnetwork.
    @param    gateway         The gateway of that subnetwork.
'''
class CloneSubnetwork(object):
    
    def __init__(self, name, members, gateway):
        self.name = name
        self.gateway = gateway
        self.node_list = self.setNodeList(members)

    def getName(self):
        return self.name

    def getGateway(self):
        return self.gateway

    def setNodeList(self, members_str):
        if DEBUG:
            print members_str
	# Remove all whitespaces in the members_str.
        members_str = members_str.replace(" ", "")
        node_list = []
        if "," in members_str:
            node_list = members_str.split(",")
            if node_list[-1] == "":
                node_list.pop()
            # Remove space if any in node name.
            for node in node_list:
                node = node.strip()
        else:
            node_list.append(members_str)
        # Add gateway as a member of the network.
        if(self.getGateway() != ""):
            node_list.append(self.getGateway())
        return node_list

    def getNodeList(self):
        return self.node_list

'''
Object CloneInstance is created for containing information of a entire instance of 
the cyber range, including virtual machines, their ip addresses and network. It has 
three variables:
    @param    index                 Index of the instance, calculated by looping the instance_number.
    @param    clone_guest_list      A list of guest.
    @param    clone_subnw_list      A list of subnetwork. It and @clone_guest_list will be used to
                                    generate ip addresses for each guest in the instance.

The function setCloneGuestList set ip addresses for the guests in clone_guest_list.
IP address of one guest's nic is defined as <range_id>.<instance_index>.i.j, in that:
    + i is the position of the segment/subnetwork that guest's nic belongs to in the clone_subnw_list.
    + j is the position of guest's nic in its segment/subnetwork.
'''
class CloneInstance(object):
    def __init__(self, index, clone_guest_list, clone_subnw_list):
        self.index = index
        self.clone_guest_list = clone_guest_list
        self.clone_subnw_list = clone_subnw_list
        self.bridge_list = []
        self.entry_point = EntryPoint()

    def getIndex(self):
        return self.index

    def getCloneSubnwList(self):
        return self.clone_subnw_list

    def getCloneGuestList(self):
        return self.clone_guest_list

    # Function for getting a list of IPs (source IPs or destination IPs) from 
    # source network/destination network in the firewall_rules description.
    def getIpList(self, block, nwname_nodes_dict, nwname_ipaddrs_dict):
        ip_list = []
        if "," in block:
            element_list = block.split(",")
        else:
            element_list = []
            element_list.append(block)
        # For each element in element_list, get the corresponding IP address.
        for element in element_list:
            # If source is under from <network>.<guest_id>, then break them down.
            if "." in element:
                nw_id = element.split(".")[0]
                guest_id = element.split(".")[1]
                # Get the corresponding IP address from nwname_nodes_dict 
                # and nwname_ipaddrs_dict, then add them to the ip_list.
                for i, member in enumerate(nwname_nodes_dict[nw_id]):
                    if guest_id in member:
                        ip_list.append(nwname_ipaddrs_dict[nw_id][i])
                        break
            # Otherwise add all IPs in the network to the ip_list.
            else:
                for ip in nwname_ipaddrs_dict[element]:
                    ip_list.append(ip)
        return ip_list

    # Functions for generating ip addresses, gateway, and firewall rules for each guest 
    # in the instance. Since there's no ip addressess in the beginning, it's mandatory to 
    # generate ip addresses before parsing gateway address for each guest in the instance.
    def setCloneGuestList(self, range_id):
        # Dictionary of <network_name>:<a list of members' ipaddr>.
        nwname_ipaddrs_dict = dict()
        # Dictionary of <network_name>:<a list of (node_id).(interface)>.
        nwname_nodes_dict = dict()
        # For each subnetwork/segment in the clone_subnetwork_list.
        # i is the index, start from 0. i is used as the third byte in the ipaddr.
        # Bytes in ip addr couldnt be 0, that's why it's i+1.
        for i, subnw_element in enumerate(self.getCloneSubnwList()):
            # j is used as the index of node_element in each subnetwork/segment.
            # j is the fourth byte in the ipaddr.
            # Last byte in ip addr couldn't be 0 nor 1, that's why it's j+2.
            j = 0
            # Network name.
            nwname = subnw_element.getName()
            # List of ip addr of members in the network.
            ipaddr_list = []
            # List of nodes.interface in the network.
            node_list = []
            if DEBUG:
                print subnw_element.getNodeList()
            for node_element in subnw_element.getNodeList():
                # Split the segment value to get node_id and node_nic.
                node_id, node_nic = node_element.split(".")
                # Check node_id of each guest in the clone_guest_list to get the correct guest. 
                # Depending on the number of the guest specified in the field "number" of "guests", 
                # it will generate the corresponding last bit.
                for guest in self.getCloneGuestList():
                    if guest.getGuestId() == node_id:
                        ip_addr = "{0}.{1}.{2}.{3}".format(range_id, self.getIndex(), i+1, j+2)
                        if node_element != subnw_element.getGateway():
                            if DEBUG:
                                print ip_addr
                            # Add element to ipaddr_list (gateway is not included).
                            ipaddr_list.append(ip_addr)
                            # Add elements to node_list (gateway is not included).
                            node_list.append(node_element)
                        guest.addNicAddrDict(node_nic, ip_addr)
                        j += 1
                # Add element to the dictionary nwname_ipaddrs_dict.
                nwname_ipaddrs_dict[nwname] = ipaddr_list
                nwname_nodes_dict[nwname] = node_list

            # Set gateway for each guest in the list.
            # If user specify gateway for the guest via tag "gateway", then extract gateway_id and gateway_nic from it.
            if (subnw_element.getGateway() != ""):
                gateway_addr = ""
                gateway_id, gateway_nic = subnw_element.getGateway().split(".")
                # Compare gateway_id and gateway_nic with each guest in 
                # the clone guest list to find out the gateway_addr.
                for guest in self.getCloneGuestList():
                    if guest.getGuestId() == gateway_id:
                        gateway_addr = guest.getNicAddrDict()[gateway_nic]
                        break
                # Set gateway_addr for each guest in the clone guest list.
                for node_element in subnw_element.getNodeList():
                    node_id, node_nic = node_element.split(".")
                    for guest in self.getCloneGuestList():
                        if guest.getGuestId() == node_id and guest.getGuestId() != gateway_id:
                            guest.addNicGwDict(node_nic, gateway_addr)
            # Otherwise, set gateway for the guest by default rule: gateway_ipaddr = {three first bits of guest_ipaddr}.1
            # Ex: if guest_ipaddr = 112.1.1.3, then gateway_ipaddr = 112.1.1.1.
            # Note that this rule only applies for vm that doesn't have a gateway installed before. When there exists a gateway
            # configured in the vm, then the rule will be passed.
            else:
                for guest in self.getCloneGuestList():
                    if len(guest.getNicGwDict()) == 0:
                        for guest_nic, guest_addr in guest.getNicAddrDict().items():
                            bits = guest_addr.split(".")
                            bits.pop()
                            bits.append("1")
                            gateway_addr = ".".join(bits)
                            guest.addNicGwDict(guest_nic, gateway_addr)
                            break
                
        if DEBUG:
            print nwname_ipaddrs_dict, nwname_nodes_dict

        # Set rules for each guest in list clone_guest based on src=ipaddr, dst=ipaddr.
        for guest in self.getCloneGuestList():
            if guest.getHasFwSetup() == True:
                fwrule_list = []
                fwrule_list.append("sysctl -w net.ipv4.ip_forward=1; sysctl -p");
                for rule_desc in guest.getFwRuleDescList():
                    elements = rule_desc.strip().split(" ")
                    src_nw = ""
                    dst_nw = ""
                    sport = ""
                    dport = ""
                    multiport = ""
                    for e in elements:
                        if "src" in e:
                            src_nw = e.split("=")[1]
                        if "dst" in e:
                            dst_nw = e.split("=")[1]
                        if "sport" in e:
                            sport = e.split("=")[1]
                        if "dport" in e:
                            dport = e.split("=")[1]
                            if "," in dport:
                                multiport = "-m multiport"

                    # Get the list of source IP list and destination IP list from getIpList function.
                    src_ip_list = self.getIpList(src_nw, nwname_nodes_dict, nwname_ipaddrs_dict)
                    dst_ip_list = self.getIpList(dst_nw, nwname_nodes_dict, nwname_ipaddrs_dict)

                    # Combine IPs in these above lists to put them in one firewall statement.
                    src_ip_str = ",".join(src_ip_list[:])
                    dst_ip_str = ",".join(dst_ip_list[:])
                    if sport != "" and dport != "":
                        fw_rule = "iptables -A FORWARD -m state -p tcp -s {0} -d {1} {2} --sport {3} --dport {4} --state NEW,ESTABLISHED,RELATED -j ACCEPT".format(src_ip_str, dst_ip_str, multiport, sport, dport)
                    elif sport != "" and dport == "":
                        fw_rule = "iptables -A FORWARD -m state -p tcp -s {0} -d {1} --sport {2} --state NEW,ESTABLISHED,RELATED -j ACCEPT".format(src_ip_str, dst_ip_str, sport)
                    elif sport == "" and dport != "":
                        fw_rule = "iptables -A FORWARD -m state -p tcp -s {0} -d {1} {2} --dport {3} --state NEW,ESTABLISHED,RELATED -j ACCEPT".format(src_ip_str, dst_ip_str, multiport, dport)
                    else:
                        fw_rule = "iptables -A FORWARD -m state -p tcp -s {0} -d {1} --state NEW,ESTABLISHED,RELATED -j ACCEPT".format(src_ip_str, dst_ip_str)
                    fwrule_list.append(fw_rule)
                # Append the final rules as allowing all allowed traffic above comming back.
                if len(fwrule_list) != 0:
                    fw_rule = "iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT"
                    fwrule_list.append(fw_rule)
                #print fwrule_list
                guest.setFwRuleList(fwrule_list)

    # Function for generating ip addresses for bridges in the instance.
    def getBridgeList(self):
        return self.bridge_list

    def setBridgeList(self, range_id):
        for i, subnw_element in enumerate(self.getCloneSubnwList()):
            # bridge_id = <range_id>-<instance_index>-<position of the subnet in the instance>
            # bridge_addr = <range_id>.<instance_index>.<position of the subnet in the instance>.1
            bridge_id = "{0}-{1}-{2}".format(range_id, self.getIndex(), i+1)
            bridge_addr = "{0}.{1}.{2}.1".format(range_id, self.getIndex(), i+1)
            append = 1
            for bridge in self.bridge_list:
                if bridge_id == bridge.getId():
                    append = 0
                    break
            if append == 1:
                self.bridge_list.append(Bridge(bridge_id, bridge_addr))

    # Function for generating entry point in the instance.
    # The current mechanism is to take the first desktop as the entry point.
    def getEntryPoint(self):
        return self.entry_point

    def setEntryPoint(self, instance_id, port, host_id):
        for clone_guest in self.getCloneGuestList():
            #if clone_guest.getGuestId() == "desktop" and clone_guest.getIndex() == 1:
            if clone_guest.getIsEntryPoint() == True and clone_guest.getIndex() == 1:
                self.entry_point.setAddr(clone_guest.getNicAddrDict()["eth0"])
        self.entry_point.setPort(port) 
        # Generate random account and passwd for entry point.
        s = string.lowercase+string.digits
        # OLD VERSION: Random suffix of 5 digits
        #account = "trainee{0}".format(''.join(random.sample(s,5)))
        # NEW VERSION: Use instance id as suffix (add 1 so as to start from 1)
        # Use leading zeros (up to 2 digits) to match current Moodle settings
        account = "trainee{number:02d}".format(number=(instance_id+1))
        passwd = ''.join(random.sample(s,10))
        self.entry_point.setAccount(account)
        self.entry_point.setPasswd(passwd)
        self.entry_point.setHostId(host_id)
    
'''
Object CloneHost is created for containing information of the tag "hosts" in the cyber range
description. It has two variables:
    @param    host_id            Id of the host that cyber range instances are deployed.
    @param    instance_list      List of instances.
'''
class CloneHost(Host):
    def __init__(self, host, instance_list):
        if host:
            self.host_id = host.getHostId()
            self.virbr_addr = host.getVirbrAddr()
            self.mgmt_addr = host.getMgmtAddr()
            self.account = host.getAccount()

        self.instance_list = instance_list

    def getHostId(self):
        return self.host_id

    def getInstanceList(self):
        return self.instance_list

    # Pass the range_id variable for the function setCloneGuestList in 
    # the class CloneInstance to calculate ip addresses for virtual machines.
    def setInstanceList(self, range_id, port_list):
        for i, instance in enumerate(self.getInstanceList()):
            instance.setCloneGuestList(range_id)
            instance.setBridgeList(range_id)
            instance.setEntryPoint(i, port_list[i], self.getHostId())

'''
Object CloneSetting is created for containing information of the tag "clone_settings" in the cyber range
description. It has three variables:
    @param    range_id           Id of the cyber range.
    @param    clone_host_list    A list of CloneHost object.
'''
class CloneSetting(object):
    def __init__(self, range_id, topology_type, clone_host_list):
        self.range_id = range_id
        self.topology_type = topology_type
        self.clone_host_list = clone_host_list

    def getRangeId(self):
        return self.range_id

    def getCloneHostList(self):
        return self.clone_host_list

    def getTopologyType(self):
        return self.topology_type

    def getTotalInstanceNum(self):
        instance_num = 0
        for clone_host in self.getCloneHostList():
            instance_num += len(clone_host.getInstanceList())
        return instance_num

    # Pass the range_id variable for the function setInstanceList in the class CloneHost.
    def setCloneHostList(self, port_list):
        for i, clone_host in enumerate(self.getCloneHostList()):
            port_sublist = port_list[0:len(clone_host.getInstanceList())]
            clone_host.setInstanceList(self.getRangeId(), port_list)
            port_list = [port for port in port_list if port not in port_sublist]

    # Write down the detailed configuration file for the range depending on base VM type.
    def writeConfig(self, filename, base_vm_type):
        data = OrderedDict()
        data[Storyboard.RANGE_ID] = self.getRangeId()
        hostdict_list = []
        for host in self.getCloneHostList():
            host_dict = OrderedDict()
            host_dict[Storyboard.HOST_ID] = host.getHostId()
            host_dict[Storyboard.MGMT_ADDR] = host.getMgmtAddr()
            host_dict[Storyboard.INSTANCE_COUNT] = len(host.getInstanceList())
            instancedict_list = []
            for instance in host.getInstanceList():
                instance_dict = OrderedDict()
                instance_dict[Storyboard.INSTANCE_INDEX] = instance.getIndex()
                guestdict_list = []
                for j,guest in enumerate(instance.getCloneGuestList()):
                    guest_dict = OrderedDict()
                    addr_dict = OrderedDict()
                    for key,value in guest.getNicAddrDict().items():
                        addr_dict[key] = value
                    gateway_dict = OrderedDict()
                    for key,value in guest.getNicGwDict().items():
                        gateway_dict[key] = value
                    fwrule_dict = OrderedDict()
                    for i,rule in enumerate(guest.getFwRuleList()):
                        fwrule_dict['rule{0}'.format(i)] = rule
                    guest_dict[Storyboard.GUEST_ID] = guest.getGuestId()
                    # Generate KVM/AWS domain name at this point so that we can output it
                    # TODO: Field name below should be just 'domain', but seems used in other files too
                    guest.kvm_domain = "{0}_cr{1}_{2}_{3}".format(guest.getGuestId(), self.getRangeId(), instance.getIndex(), guest.getIndex())
                    if base_vm_type == 'kvm':
                        guest_dict[Storyboard.KVM_DOMAIN] = guest.kvm_domain
                    elif base_vm_type == 'aws':
                        guest_dict[Storyboard.AWS_DOMAIN] = guest.kvm_domain
                    guest_dict[Storyboard.IP_ADDRS] = addr_dict
                    if len(gateway_dict) != 0:
                        guest_dict[Storyboard.GATEWAYS] = gateway_dict
                    if len(fwrule_dict) != 0:
                        guest_dict[Storyboard.FIREWALL_RULE] = fwrule_dict
                    # Deal with network membership information
                    networks_dict = self.generateNetworkMembership(instance.clone_subnw_list,
                                                                   guest.getGuestId())
                    if networks_dict:
                        guest_dict[Storyboard.NETWORK_MEMBERSHIP] = networks_dict
                    guestdict_list.append(guest_dict)
                #instance_dict['node{0}'.format(j)] = guestdict_list
                instance_dict[Storyboard.GUESTS] = guestdict_list
                instancedict_list.append(instance_dict)
            host_dict[Storyboard.INSTANCES] = instancedict_list
            hostdict_list.append(host_dict)
        data[Storyboard.HOSTS] = hostdict_list

        # Write to temporary file first, then rename it, so as to make sure that programs
        # (e.g., CyRIS-vis) watching the output file do not read truncated versions
        filename_tmp = filename + ".tmp"
        with open(filename_tmp, 'w') as yaml_file:
            yaml.dump(data, yaml_file, width=float("inf"), allow_unicode=True, default_flow_style=False, explicit_start=True)
        os.rename(filename_tmp, filename)
        #print data

    def generateNetworkMembership(self, clone_subnw_list, guest_id):
        networks_dict = OrderedDict()
        if DEBUG:
            print "* DEBUG: cyris: Network info in cyber range of guest '{0}': ".format(guest_id)
        for clone_subnw in clone_subnw_list:
            if DEBUG:
                print "* DEBUG: cyris:   Network name: ", clone_subnw.getName()
                print "* DEBUG: cyris:   Node list: ", clone_subnw.getNodeList()
            for node_interface in clone_subnw.getNodeList():
                node_interface_list = node_interface.split(".")
                if node_interface_list:
                    if node_interface_list[0] == guest_id:
                        networks_dict[node_interface_list[1]] = clone_subnw.getName()
        if DEBUG:
            print "* DEBUG: cyris: Generated networks dictionary: ", networks_dict
        return networks_dict

class Command(object):
    #def __init__(self, command, description):
    def __init__(self, command, description, comtag="-"):
        self.command = command
        self.description = description
        self.comtag = comtag

    def getCommand(self):
        return self.command

    def getDescription(self):
        return self.description

    def __str__(self):
        return "command: " + self.getCommand() + " description: " + self.getDescription()

"""
def main():
    yaml_file = sys.argv[1]
    try:
        with open(yaml_file, "r") as f:
            doc = yaml.load(f)
    except yaml.YAMLError, exc:
        print "Error in the cyber range description file: ", exc
        return
    hosts = []
    clone_setting = None
    for element in doc:
	if "host_settings" in element.keys():
	    for i in element["host_settings"]:
		if i == 0:
		    MSTNODE_ACCOUNT = i["account"]
		    MSTNODE_MGMT_ADDR = i["mgmt_addr"]
		host = Host(i["id"], i["virbr_addr"], i["mgmt_addr"], i["account"])
		hosts.append(host)

        if "clone_settings" in element.keys():
            range_id = element["clone_settings"][0]["range_id"]
            clone_host_list = []
            for host in element["clone_settings"][0]["hosts"]:
                host_id_str = host["host_id"].strip()
                host_id_list = []
                if "," in host_id_str:
                    host_id_list = host_id_str.replace(" ","").split(",")
                else:
                    host_id_list.append(host_id_str)
                for host_id in host_id_list:
                    instance_num = host["instance_number"]
                    nw_type = host["topology"][0]["type"]
#                    for subnetwork in host["topology"][0]["networks"]:
#                        name = subnetwork["name"]
#                        members = subnetwork["members"]
#                        if "gateway" in subnetwork.keys():
#                            gateway = subnetwork["gateway"]
#                        else:
#                            gateway = ""
#                        clone_subnetwork = CloneSubnetwork(name, members, gateway)
#                        clone_subnw_list.append(clone_subnetwork)
                    instance_list = []
                    for i in range(1, instance_num+1):
                        # Since each instance reuse the information of the guest, it's important to 
                        # recreate a clone_guest_list when creating a new instance. It is the main
                        # reason why clone_guest_list is created here but not in the same place with
                        # the clone_subnw_list.
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
                            firewall_rules = []
                            if "forwarding_rules" in guest.keys():
                                has_fw_setup = True
                                for rule in guest["forwarding_rules"]:
                                    firewall_rules.append(rule["rule"])
                            else:
                                has_fw_setup = False

                            if "entry_point" in guest.keys():
                                is_entry_point = True
                            else:
                                is_entry_point = False
                            # Create a list of clone_guest with size=number.
                            for k in range(1, number+1):
                                clone_guest = CloneGuest(guest_id, k, has_fw_setup, firewall_rules, is_entry_point)
                                clone_guest_list.append(clone_guest)
                        instance = CloneInstance(i, clone_guest_list, clone_subnw_list)
                        instance_list.append(instance)
                    clone_host = CloneHost(host_id, instance_list)
                    clone_host_list.append(clone_host)
            clone_setting = CloneSetting(range_id, nw_type, clone_host_list)
            clone_setting.setCloneHostList([2,3,4,5,6,7,8,9,10])
            clone_setting.writeConfig("result.yml")

    for host in clone_setting.getCloneHostList():
        print host.getHostId()
        for i,instance in enumerate(host.getInstanceList()):
            print "instance",i
            for bridge in instance.getBridgeList():
                print bridge
            for guest in instance.getCloneGuestList():
                print guest
                print "\n"
            print "entry point: ", instance.getEntryPoint()
    # Send email function
#    f = open("/home/cyuser/cyris-development/main/mail_template", "r")
#    contents = f.readlines()
#    f.close()
#    contents.insert(0, "Dear John Doe,")
#    contents.insert(4, "\n- Number of cyber range instances: {0}".format(clone_setting.getTotalInstanceNum()))
#    information = ""
#    instance_index = 1
#    for host in clone_setting.getCloneHostList():
#        for instance in host.getInstanceList():
#            for host in hosts:
#                if instance.getEntryPoint().getHostId() == host.getHostId():
#                    entry_point = instance.getEntryPoint()
#                    information += "\n- Cyber range instance {0}:\n\turl: ssh {1}@{2} -p {3}\n\tpasswd: {4}\n".format(instance_index, entry_point.getAccount(), host.getMgmtAddr(), entry_point.getPort(), entry_point.getPasswd())	
#                    instance_index += 1
#                    break
#    contents.insert(6, "{0}\n".format(information))
#    f = open("/home/cyuser/cyris-development/main/inform_email", "w")
#    contents = "".join(contents)
#    f.write(contents)
#    f.close()

            
main()
"""
