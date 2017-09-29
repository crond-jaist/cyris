#!/bin/bash

# The flow of the emulation will be as followed:
# - Install the tool hping3 for the base image
# - Start tcpdump on the host to listen to traffic comming to the virtual bridge virbr0 (kvm)
# - Copy the script attacks_emulation/launch_dos.sh to the base image and start the attack to nic virbr0 of the host
#   with user-specified source address (source_addr) and destination port (dport)
# - Terminate the attack after two seconds
# - Change the victim address in the pcap file (currently virbr0 addr) to image's address
# - Use mergePcap.py to add noise to the pcap file, and copy it to the base image
#
abs_path=$1
virbr_addr=$2
image_addr=$3
image_passwd=$4
noise_level=$5
file_path=$6
file_name=$7
source_addr=$8 # the address that starts the attack
dport=$9
cr_dir=${10}

inst_dir="instantiation"

# install hping3 for base image
sshpass -p ${image_passwd} ssh root@${image_addr} yum install -y hping3;

# opens tcpdump to start capturing packets on two interfaces: eth0 and virbr0
sudo bash -c "exec -a virbr0_dos_pcap tcpdump -i virbr0 -c 1000 port ${dport} -w ${cr_dir}virbr0_dos.pcap &";

# base image starts attacking the host by dos
sshpass -p ${image_passwd} scp ${abs_path}${inst_dir}/attacks_emulation/launch_dos.sh root@${image_addr}:/bin/cyberrange;
sshpass -p ${image_passwd} ssh root@${image_addr} /bin/cyberrange/launch_dos.sh ${source_addr} ${virbr_addr} ${dport};

sudo pkill -f virbr0_dos_pcap;

echo "done"
sudo apt-get install -y tcpreplay;

# changes ipaddresses in two pcap files and merges them as one
tcprewrite -S ${virbr_addr}/32:${image_addr}/32 -i ${cr_dir}virbr0_dos.pcap -o ${cr_dir}virbr0_3.pcap;
tcprewrite -D ${virbr_addr}/32:${image_addr}/32 -i ${cr_dir}virbr0_3.pcap -o ${cr_dir}attack.pcapng;

# change timestamp of noise file and merge with the attack pcap file
sudo python ${abs_path}${inst_dir}/logs_preparation/mergePcap.py ${noise_level} ${file_name} ${abs_path} ${cr_dir};

sudo rm -f ${cr_dir}virbr0*.pcap;

# copy pcap file to trainee's directory
sshpass -p ${image_passwd} scp ${cr_dir}${file_name} root@${image_addr}:${file_path};
sudo rm -f ${cr_dir}${file_name};
