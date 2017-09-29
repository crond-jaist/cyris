#!/bin/bash

vm_addr=$1
vm_passwd=$2
host_name=$3

# copy it to basevm
sshpass -p ${vm_passwd} ssh -o StrictHostKeyChecking=no root@${vm_addr} "echo $host_name > /etc/hostname"
