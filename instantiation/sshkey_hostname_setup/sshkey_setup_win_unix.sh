#!/bin/bash

ABS_PATH=$1
INSTANTIATION_DIR=$2
vm_addr=$3
vm_passwd=$4
mstnode_account=$5

echo "windows sshkey setup("${vm_addr}")"

# clear old ssh keys if exist
ssh-keygen -f "/home/${mstnode_account}/.ssh/known_hosts" -R ${vm_addr} > /dev/null

#echo "## make .ssh dir"
sshpass -p ${vm_passwd} ssh -o StrictHostKeyChecking=no root@${vm_addr} "mkdir C:\Users\root\.ssh"

#echo "## add sshkey in authorized_keys"
sshkey=`cat ~/.ssh/id_rsa.pub`
sshpass -p ${vm_passwd} ssh  root@${vm_addr} "echo ${sshkey} >> C:\Users\root\.ssh\authorized_keys"

#echo "## create change acl script"
sshpass -p ${vm_passwd} scp ${ABS_PATH}${INSTANTIATION_DIR}/sshkey_hostname_setup/create_ch_acl.ps1 root@${vm_addr}:"C:\Users\root\.ssh\create_ch_acl.ps1"

#echo "## exe change acl script"
sshpass -p ${vm_passwd} ssh root@${vm_addr} "powershell C:\Users\root\.ssh\create_ch_acl.ps1"

#echo "## delete acl script"
sshpass -p ${vm_passwd} ssh root@${vm_addr} "del /Q C:\Users\root\.ssh\create_ch_acl.ps1"