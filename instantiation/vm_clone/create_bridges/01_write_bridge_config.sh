#!/bin/bash

bridge_id=$1
bridge_addr=$2

# create logical interfaces and bridges configuration
NEWLINE=$'\n'
config="${NEW_LINE}
auto eth${bridge_id}${NEW_LINE}
iface eth${bridge_id} inet manual${NEW_LINE}
${NEW_LINE}
auto br${bridge_id}${NEW_LINE}
iface br${bridge_id} inet static${NEW_LINE}
address ${bridge_addr}${NEW_LINE}
netmask 255.255.255.0${NEW_LINE}
bridge_ports eth${bridge_id}${NEW_LINE}
bridge_stp off${NEW_LINE}
bridge_fd 0"

flock -x /etc/network/interfaces echo "${config}" >> /etc/network/interfaces
