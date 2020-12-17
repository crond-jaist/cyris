#!/bin/bash

# this script is for copying content from outside to cyber range

src=$1
dst=$2
image_addr=$3
basevm_type=$4
os_type=$5

# Check whether the specified source file or directory exists
if [ ! -f "${src}" -a ! -d "${src}" ]; then
    echo
    echo "copy_content.sh: File or directory '${src}' doesn't exist => abort copy"
    exit 1
fi

if [ ${basevm_type} = "kvm" ]; then
    # check if the dst directory exists
    if (ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${image_addr} "[ -d ${dst} ]")
    then
        :
    else
        ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${image_addr} "mkdir -p ${dst}"
    fi
    # copy content from src to dst
    scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r ${src} root@${image_addr}:${dst}
elif [ ${basevm_type} = "aws" ]; then
    if [ ${os_type} = "red_hat" -o ${os_type} = "amazon_linux" -o ${os_type} = "amazon_linux2" ]; then
        if (ssh -i TESTKEY.pem -o StrictHostKeyChecking=no ec2-user@${image_addr} "[ -d ${dst} ]")
        then
            :
        else
            ssh -i TESTKEY.pem -o StrictHostKeyChecking=no ec2-user@${image_addr} "sudo mkdir -p ${dst}"
        fi
        scp -r -i TESTKEY.pem -o StrictHostKeyChecking=no ${src} ec2-user@${image_addr}:
        # Special syntax for ${src} to preserve the last part of the name (after /) for the local 'mv'
        ssh -i TESTKEY.pem -o StrictHostKeyChecking=no ec2-user@${image_addr} "sudo mv ${src##*/} ${dst}"
    elif [ ${os_type} = "ubuntu_20" -o ${os_type} = "ubuntu_18" -o ${os_type} = "ubuntu_16" ]; then
        if (ssh -i TESTKEY.pem -o StrictHostKeyChecking=no ubuntu@${image_addr} "[ -d ${dst} ]")
        then
            :
        else
            ssh -i TESTKEY.pem -o StrictHostKeyChecking=no ubuntu@${image_addr} "sudo mkdir -p ${dst}"
        fi
        scp -r -i TESTKEY.pem -o StrictHostKeyChecking=no ${src} ubuntu@${image_addr}:
        # Special syntax for ${src} to preserve the last part of the name (after /) for the local 'mv'
        ssh -i TESTKEY.pem -o StrictHostKeyChecking=no ubuntu@${image_addr} "sudo mv ${src##*/} ${dst}"
    fi
fi
