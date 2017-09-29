#!/bin/bash

abs_path=$1
image_addr=$2
image_passwd=$3
ruleset_file=$4

inst_dir="instantiation"

# install iptables-service package in centos 7
sshpass -p ${image_passwd} ssh root@${image_addr} "yum install iptables-services";

# deactivate firewalld and activate iptables
sshpass -p ${image_passwd} ssh root@${image_addr} "systemctl stop firewalld && systemctl start iptables; systemctl start ip6tables";

# Disable the FirewallD Service and Enable the Iptables Services
sshpass -p ${image_passwd} ssh root@${image_addr} "systemctl disable firewalld; systemctl mask firewalld; systemctl enable iptables; systemctl enable ip6tables";

# apply ruleset
# copy iptables template to another file called iptables
cp ${abs_path}${inst_dir}/ruleset_modification/iptables_template ${abs_path}${inst_dir}/ruleset_modification/iptables;
# add rules to iptables file
python ${abs_path}${inst_dir}/ruleset_modification/append_ruleset.py ${ruleset_file} ${abs_path}${inst_dir}/ruleset_modification/iptables;
# copy iptables file to base vm
sshpass -p ${image_passwd} scp ${abs_path}${inst_dir}/ruleset_modification/iptables root@${image_addr}:/etc/sysconfig;
#sshpass -p ${image_passwd} ssh root@${image_addr} 'bash -s' < ${abs_path}${inst_dir}/ruleset_modification/firewall_ruleset.sh;
#sshpass -p ${image_passwd} ssh root@${image_addr} "iptables-save > /etc/sysconfig/iptables";
sshpass -p ${image_passwd} ssh root@${image_addr} "iptables-restore /etc/sysconfig/iptables";

