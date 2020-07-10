#!/bin/bash

# This script is for preparing host Ubuntu Server 20.04 ready for CyRIS.

sudo apt-get update

# Install depedencies
sudo apt-get install qemu-kvm nstall qemu-kvm libvirt-clients libvirt-daemon-system ubuntu-vm-builder bridge-utils virt-manager python3-pip python3-paramiko tcpreplay wireshark sshpass pssh python3-yaml python3-scapy sendemail ifupdown -y


# ssh-copy-id to itself and other hosts.
ssh-copy-id localhost

# https://askubuntu.com/a/944787
echo "Edit `/etc/NetworkManager/NetworkManager.conf` with `managed=true`"


sudo apt-get install bridge-utils
