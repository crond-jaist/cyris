# This script is to create new virtual machines from the image base by running scripts in xml folder.

HOST_ID=$1
VM_ID=$2
BASE_IMG_NAME=$3
CYRIS_ABSPATH=$4
CYBERRANGE_ABSPATH=$5
BRIDGE_ID_STR=$6
ADDR_STR=$7

inst_dir="instantiation"

${CYRIS_ABSPATH}${inst_dir}/vm_clone/vm_clone_xml.sh ${HOST_ID} ${VM_ID} ${BASE_IMG_NAME} ${CYBERRANGE_ABSPATH} ${BRIDGE_ID_STR} ${ADDR_STR};

