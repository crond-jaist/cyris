#!/bin/sh

id="cr${1}_"
dir=${2}

virsh list --all | awk '{
    if($0 ~ /'${id}'/ ) {
        destroy_cmd = "virsh shutdown " $2;
        echo system(destroy_cmd);
        undefine_cmd = "virsh undefine " $2;
        echo system(undefine_cmd);
    }
}'
ps auxwww | grep diff_${id} | awk '{system("sudo kill -9 " $2)}'


#sudo rm ${dir}images/desktop${id}*.xml
#sudo rm ${dir}images/desktop_diff_${id}*
#sudo rm ${dir}images/webserver${id}*.xml
#sudo rm ${dir}images/webserver_diff_${id}*
