#!/bin/bash

# $1: id of server
# $2: id of vm
# $3: third bit of vm
# $4: fourth bit of vm
# $5: name of base image
# $6: absolute path
HOST_ID=$(printf "%x" $1);
VM_ID=$2;
IMAGE_NAME=$3
ABSPATH=$4
BRIDGE_ID_STR=$5
ADDR_STR=$6

echo -e "\n* Enter VM cloning script 'vm_clone_xml.sh'"

# Create addr list for network interfaces
IFS="," read -r -a ADDR_LIST <<< "${ADDR_STR}"
# Create bridge_id for network interfaces
IFS="," read -r -a BRIDGE_ID_LIST <<< "${BRIDGE_ID_STR}"

# Remove the previous config file if it's still present
if [ -e ${ABSPATH}images/${VM_ID}_config.xml ];
then
    rm ${ABSPATH}images/${VM_ID}_config.xml;
fi

echo "** Create disk image '${VM_ID}_img' for the cloned VM"
# Create overlay image from base image
qemu-img create -b ${ABSPATH}${IMAGE_NAME} -f qcow2 ${ABSPATH}images/${VM_ID}_img
sudo chown libvirt-qemu: ${ABSPATH}images/${VM_ID}_img

echo "** Create XML config file '${VM_ID}_config.xml' for the cloned VM"
# Create XML config file for starting new VM
echo "<domain type='kvm'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <name>${VM_ID}</name>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <memory>1024000</memory>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <vcpu>1</vcpu>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <os>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <type arch='x86_64'>hvm</type>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <boot dev='hd'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  </os>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <features>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <acpi/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <apic/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <pae/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  </features>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <clock offset='utc'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <on_poweroff>destroy</on_poweroff>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <on_reboot>restart</on_reboot>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <on_crash>restart</on_crash>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  <devices>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <emulator>/usr/bin/kvm</emulator>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <disk type='file' device='disk'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <driver name='qemu' type='qcow2'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <source file='${ABSPATH}images/${VM_ID}_img'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <target dev='hda' bus='ide'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <address type='drive' controller='0' bus='0' unit='0'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    </disk>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <controller type='ide' index='0'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    </controller>" >> ${ABSPATH}images/${VM_ID}_config.xml;
# This inteface setup is for connecting one vm from one server to another vm in another server
for i in "${!ADDR_LIST[@]}"
do
    IFS="." read -r -a  BIT_LIST <<< "${ADDR_LIST[i]}"
    MAC_THIRDLAST_BIT=$(printf "%x" ${BIT_LIST[1]});
    MAC_SECONDLAST_BIT=$(printf "%x" ${BIT_LIST[2]});
    MAC_LAST_BIT=$(printf "%x" ${BIT_LIST[3]}); 
    echo "    <interface type='bridge'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
    echo "      <mac address='52:54:${HOST_ID}:${MAC_THIRDLAST_BIT}:${MAC_SECONDLAST_BIT}:${MAC_LAST_BIT}'/>" >> ${ABSPATH}images/${VM_ID}_config.xml; 
    echo "      <source bridge='br${BRIDGE_ID_LIST[i]}'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
    echo "    </interface>" >> ${ABSPATH}images/${VM_ID}_config.xml; 
done
echo "    <serial type='pty'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <target port='0'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    </serial>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <console type='pty'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <target type='serial' port='0'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    </console>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <input type='mouse' bus='ps2'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0' />" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <sound model='ich6'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    </sound>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <video>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <model type='cirrus' vram='9216' heads='1'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    </video>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    <memballoon model='virtio'>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "    </memballoon>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "  </devices>" >> ${ABSPATH}images/${VM_ID}_config.xml;
echo "</domain>" >> ${ABSPATH}images/${VM_ID}_config.xml;

echo "** Define the cloned VM using config file '${VM_ID}_config.xml'"
virsh define ${ABSPATH}images/${VM_ID}_config.xml

echo "** Start the cloned VM '${VM_ID}'"
sleep 1
virsh start ${VM_ID}

echo -e "* Exit VM cloning script 'vm_clone_xml.sh'\n"
