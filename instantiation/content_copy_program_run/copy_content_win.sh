#!/bin/bash

# this script is for copying content from outside to cyber range

src=$1
dst=$2
image_addr=$3
image_passwd=$4

# check if the dst directory exists
dir_exist=`sshpass -p ${image_passwd} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${image_addr} "powershell Test-Path ${dst}"`
if [ $(echo "${dir_exist}" | grep -e 'True') ]; then
    :
else
    sshpass -p ${image_passwd} ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${image_addr} "mkdir ${dst}"
fi

# copy content from src to dst
sshpass -p ${image_passwd} scp  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r $src root@${image_addr}:"${dst}"

