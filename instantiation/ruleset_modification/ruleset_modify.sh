#!/bin/bash

abs_path=$1
image_addr=$2
ruleset_file=$3
os_type=$4
basevm_type=$5

inst_dir="instantiation"

echo "-- Firewall ruleset modification started"

# Check whether the specified ruleset file actually exists
if [ ! -f "${ruleset_file}" ]; then
    echo
    echo "ruleset_modify.sh: Firewall ruleset file '${ruleset_file}' doesn't exist => abort firewall setting"
    exit 1
fi

# Apply rules depending on what virtualization technology is used
if [ ${basevm_type} = "kvm" ]; then

    # Set up iptables
    ## Install iptables-service package in CentOS 7 (if it is not installed already)
    #echo "ruleset_modify.sh: Install iptables-services..."
    #sshpass -p ${image_passwd} ssh root@${image_addr} "yum install iptables-services -y"
    ## Stop the default CentOS 7 firewall 'firewalld' and start iptables
    echo "ruleset_modify.sh: Stop firewalld and start iptables services..."
    ssh root@${image_addr} "systemctl stop firewalld; systemctl start iptables; systemctl start ip6tables"
    ## Disable firewalld and enable iptables
    echo "ruleset_modify.sh: Disable firewalld and enable iptables services..."
    ssh root@${image_addr} "systemctl disable firewalld; systemctl mask firewalld; systemctl enable iptables; systemctl enable ip6tables"

    # Prepare the new iptables configuration
    ## Copy 'iptables_template' ruleset base to a new file called 'iptables'
    echo "ruleset_modify.sh: Prepare iptables file from template..."
    cp ${abs_path}${inst_dir}/ruleset_modification/iptables_template ${abs_path}${inst_dir}/ruleset_modification/iptables;
    ## Append 'firewall_rules' task rules to the 'iptables' file
    echo "ruleset_modify.sh: Append 'firewall_rules' task rules to file..."
    python ${abs_path}${inst_dir}/ruleset_modification/append_ruleset.py ${ruleset_file} ${abs_path}${inst_dir}/ruleset_modification/iptables;
    ## Copy the 'iptables' file to the base VM
    echo "ruleset_modify.sh: Copy iptables configuration file to base VM..."
    scp ${abs_path}${inst_dir}/ruleset_modification/iptables root@${image_addr}:/etc/sysconfig;
    # Restore iptables rules from configuration file
    echo "ruleset_modify.sh: Restore iptables configuration from file..."
    echo "                   (will also appear in the cloned VMs on reboot)"
    ssh root@${image_addr} "iptables-restore /etc/sysconfig/iptables";

elif [ ${basevm_type} = "aws" ]; then
    if [ ${os_type} = "amazon_linux" -o ${os_type} = "amazon_linux2" ]; then
        cp ${abs_path}${inst_dir}/ruleset_modification/iptables_template ${abs_path}${inst_dir}/ruleset_modification/iptables;
        python ${abs_path}${inst_dir}/ruleset_modification/append_ruleset.py ${ruleset_file} ${abs_path}${inst_dir}/ruleset_modification/iptables;
        scp -i TESTKEY.pem -o StrictHostKeyChecking=no ${abs_path}${inst_dir}/ruleset_modification/iptables ec2-user@${image_addr}:
        ssh -i TESTKEY.pem ec2-user@${image_addr} "sudo mv iptables /etc/sysconfig/iptables"
        ssh -i TESTKEY.pem ec2-user@${image_addr} "sudo iptables-restore /etc/sysconfig/iptables";
    elif [ ${os_type} = "red_hat" ]; then
        ssh -i TESTKEY.pem -o StrictHostKeyChecking=no ec2-user@${image_addr} "sudo yum install iptables-services -y";
        ssh -i TESTKEY.pem ec2-user@${image_addr} "sudo systemctl start iptables; sudo systemctl start ip6tables";
        ssh -i TESTKEY.pem ec2-user@${image_addr} "sudo systemctl enable iptables; sudo systemctl enable ip6tables";
        cp ${abs_path}${inst_dir}/ruleset_modification/iptables_template ${abs_path}${inst_dir}/ruleset_modification/iptables;
        python ${abs_path}${inst_dir}/ruleset_modification/append_ruleset.py ${ruleset_file} ${abs_path}${inst_dir}/ruleset_modification/iptables;
        scp -i TESTKEY.pem ${abs_path}${inst_dir}/ruleset_modification/iptables ec2-user@${image_addr}:
        ssh -i TESTKEY.pem ec2-user@${image_addr} "sudo mv iptables /etc/sysconfig/iptables"
        ssh -i TESTKEY.pem ec2-user@${image_addr} "sudo iptables-restore /etc/sysconfig/iptables";
    elif [ ${os_type} = "ubuntu_20" -o ${os_type} = "ubuntu_18" -o ${os_type} = "ubuntu_16" ]; then
        cp ${abs_path}${inst_dir}/ruleset_modification/iptables_template ${abs_path}${inst_dir}/ruleset_modification/iptables;
        python ${abs_path}${inst_dir}/ruleset_modification/append_ruleset.py ${ruleset_file} ${abs_path}${inst_dir}/ruleset_modification/iptables;
        scp -i TESTKEY.pem -o StrictHostKeyChecking=no ${abs_path}${inst_dir}/ruleset_modification/iptables ubuntu@${image_addr}:
        ssh -i TESTKEY.pem ubuntu@${image_addr} "sudo mv iptables /etc/iptables"
        ssh -i TESTKEY.pem ubuntu@${image_addr} "sudo iptables-restore /etc/iptables";
    fi
fi

echo "-- Firewall ruleset modification ended"
