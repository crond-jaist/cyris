#!/bin/bash

# This script is for preparing host Ubuntu Server 16.04 ready for CyRIS.

sudo apt-get update

# 1. Install kvm.
sudo apt-get install qemu-kvm libvirt-bin ubuntu-vm-builder bridge-utils

# 2. Install virt-manager.
sudo apt-get install virt-manager

# 3. Install pip.
sudo apt-get install python-pip

# 4. Install python-paramiko.
sudo apt-get install python-paramiko

# 5. Install tcpreplay.
sudo apt-get install tcpreplay

# 6. Install wireshark.
sudo apt-get install wireshark

# 7. Install sshpass.
sudo apt-get install sshpass

# 8. Install pssh.
sudo apt-get install pssh

# 9. Install yaml for python.
sudo apt-get install python-yaml

# 10. Install scapy for python.
sudo apt-get install python-scapy

# 11. Install sendemail
sudo apt-get install sendemail

# 12. ssh-copy-id to itself and other hosts.
ssh-copy-id localhost

