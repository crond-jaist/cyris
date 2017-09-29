#!/bin/bash

vm_addr=$1
vm_passwd=$2
mstnode_account=$3

# clear old ssh keys if exist
ssh-keygen -f "/home/${mstnode_account}/.ssh/known_hosts" -R ${vm_addr} > /dev/null

# copy it to basevm
COMMAND="ssh-copy-id -o StrictHostKeyChecking=no root@${vm_addr}"
sshpass -p ${vm_passwd} ${COMMAND} > /dev/null
