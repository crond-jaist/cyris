#!/bin/bash

old_account=$1
new_account=$2
new_passwd=$3

# edit new user with passwd
if id -u "$old_account" >/dev/null 2>&1; then
    if [[ "${new_account}" == "null" ]]
    then
        echo "${old_account}:${new_passwd}" | chpasswd;
    elif [[ "${new_passwd}" == "null" ]]
    then
        pkill -u ${old_account} pid;
        pkill -9 -u ${old_account};
        usermod -l ${new_account} ${old_account};
        ls -ld /home/${old_account};
        usermod -d /home/${new_account} -m ${new_account};
    fi
else
    echo "account does not exist";
    exit 1;
fi
