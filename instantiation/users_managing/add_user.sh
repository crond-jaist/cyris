#!/bin/bash

username=$1
passwd=$2
root_privilege=$3
full_name=${@:4:99}

# add new user with passwd
if id -u "$username" >/dev/null 2>&1; then
	echo "user exists";
	exit 1;
else
	useradd -s /bin/bash -p $(echo $passwd | openssl passwd -1 -stdin) $username;
fi

# provide root privilege to that user
if [[ "${root_privilege}" == "yes" ]]
then
    bash -c 'echo -e "'$username'\tALL=(ALL:ALL)\tALL" | (EDITOR="tee -a" visudo)'
else
    :
fi

if [[ ! -z $full_name ]]; then
  chfn -f "$full_name" $username
fi
