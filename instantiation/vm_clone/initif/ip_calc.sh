#!/bin/bash

#argument="192.168.122.0/24"
argument=${1}

ip_address=`echo ${argument} | cut -d '/' -f 1`
ip_bytes=`echo ${ip_address} | sed "s/\./ /g"`
netmask_suffix=`echo ${argument} | cut -d '/' -f 2`

netmask_address=""
broadcast_address=""

for byte in ${ip_bytes};
do
    if [ ${byte} -ne 0 ];
    then
	netmask_address="${netmask_address}.255"
	broadcast_address="${broadcast_address}.${byte}"
    else
	netmask_address="${netmask_address}.0"
	broadcast_address="${broadcast_address}.255"
    fi
done

netmask_address=`echo ${netmask_address} | cut -d '.' -f 2-`
broadcast_address=`echo ${broadcast_address} | cut -d '.' -f 2-`

echo -e "Address:\t${ip_address}"
echo -e "Netmask:\t${netmask_address} / ${netmask_suffix}"
echo -e "Broadcast:\t${broadcast_address}"
echo -e "Network:\t${argument}"

