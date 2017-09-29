#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo 'Please specify locations of abs_path and cr_path'
    echo 'Example: ./destroy_all_cr.sh /home/cyuser/cyris/ /home/cyuser/cyris/cyber_range/'
    exit 0
fi

abs_path=${1}
cr_path=${2}

for dir in ${cr_path}*; do
    if [[ -d "$dir" && ! -L "$dir" ]]; then
        echo "* INFO: destroy_all_cr: Destroying cyber range in ${dir}..."
        for script in ${dir}/*.sh; do
            if [[ "${script}" == *whole-controlled* ]]; then
                ${script}
            fi
        done
    rm -rf ${dir}
    fi
done

echo "* INFO: destroy_all_cr: Deleting ALL temporary cyber range setting files..."
rm ${abs_path}settings/*.txt
