#!/bin/bash

vm_addr=$1
vm_passwd=$2
mstnode_account=$3

# Clear old ssh keys from base VM if they exist
ssh-keygen -f "/home/${mstnode_account}/.ssh/known_hosts" -R ${vm_addr} > /dev/null

# Copy new ssh key to base VM
# NOTE: We are sending both stdout and stderr to /dev/null via the '&>' redirector
#       to get rid of INFO messages, but this may cause actual errors to be hidden
COMMAND="ssh-copy-id -o StrictHostKeyChecking=no root@${vm_addr}"
sshpass -p ${vm_passwd} ${COMMAND} &> /dev/null
