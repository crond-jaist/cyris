#!/bin/bash

abs_path=$1
virbr_addr=$2
host_account=$3
image_addr=$4
image_passwd=$5
attack_source=$6
num=$7
noise_level=$8
file_path=$9
file_name=${10}
cr_dir=${11}
basevm_type=${12}

inst_dir="instantiation"

# opens tcpdump to start capturing packets on two interfaces: eth0 and virbr0
sudo bash -c "exec -a virbr0_ssh_pcap tcpdump -i virbr0 -w ${cr_dir}virbr0_ssh.pcap &";

# base image starts attacking the host by ssh
sshpass -p ${image_passwd} scp ${abs_path}${inst_dir}/attacks_emulation/attack_paramiko_ssh.py root@${image_addr}:/bin/cyberrange/;
sshpass -p ${image_passwd} ssh -o StrictHostKeyChecking=no root@${image_addr} "python /bin/cyberrange/attack_paramiko_ssh.py ${virbr_addr} ${host_account} ${num} none ${basevm_type}";

sudo pkill -f virbr0_ssh_pcap;

#echo "done"
sudo apt-get install -y tcpreplay;

# changes ipaddresses in two pcap files and merges them as one
sudo tcprewrite -S ${image_addr}/32:${attack_source}/32 -i ${cr_dir}virbr0_ssh.pcap -o ${cr_dir}virbr0_1.pcap;
sudo tcprewrite -D ${image_addr}/32:${attack_source}/32 -i ${cr_dir}virbr0_1.pcap -o ${cr_dir}virbr0_2.pcap;
sudo tcprewrite -S ${virbr_addr}/32:${image_addr}/32 -i ${cr_dir}virbr0_2.pcap -o ${cr_dir}virbr0_3.pcap;
sudo tcprewrite -D ${virbr_addr}/32:${image_addr}/32 -i ${cr_dir}virbr0_3.pcap -o ${cr_dir}attack.pcapng;

# change timestamp of noise file and merge with the attack pcap file
sudo python ${abs_path}${inst_dir}/logs_preparation/mergePcap.py ${noise_level} ${file_name} ${abs_path} ${cr_dir};

# remove unecessary pcap files
sudo rm ${cr_dir}virbr0*.pcap;

# copy pcap file to trainee's directory
sshpass -p ${image_passwd} scp ${cr_dir}${file_name} root@${image_addr}:${file_path};
sudo rm ${cr_dir}${file_name};
