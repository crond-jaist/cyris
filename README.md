# CyRIS: Cyber Range Instantiation System

CyRIS is a tool for facilitating cybersecurity training by automating the creation and management of the corresponding training environments (a.k.a, cyber ranges) based on a description provided in YAML format. CyRIS being developed by the Cyber Range Organization and Design (CROND) NEC-endowed chair at the Japan Advanced Institute of Science and Technology (JAIST).

An overview of the processing flow of CyRIS is provided below. Based on the input cyber range description, and a collection of virtual machine base images, CyRIS performs preparation, content installation and cloning in order to deploy the cyber range on a given server infrastructure.

![CyRIS processing flow.](https://github.com/crond-jaist/cyris/blob/master/CyRIS_flow.png "CyRIS processing flow.")

CyRIS is written in Python, and has various features, including system configuration, tool installation, incident emulation, content management, and clone management. If interested, please download the latest release and let us know if you have any issues. A sample virtual machine base image is also provided for your convenience.

Next we provide brief information on the prerequisites for running CyRIS, as well as its setup and use. Please refer to the accompanying User Guide for details.

## Prerequisites

To run CyRIS, please make sure to check the following regarding your
physical host:

- Ubuntu OS has to be installed. In addition, because CyRIS constructs
  virtual cyber range environments using KVM virtualization platform,
  your physical machine is required to have a processor that supports
  hardware virtualization. To verify this, please follow instructions
  at
  [KVM/Installation](https://help.ubuntu.com/community/KVM/Installation)
  (section *Check that your CPU supports hardware virtualization*).

- Root permission (sudo) must be available for the account used to run
  CyRIS. Moreover, it is also required for the account to be able to
  execute commands via sudo without the need to enter a password.

- SSH public & private keys must be present. For more information
  about how to set up SSH keys, please refer to [Set Up SSH
  Keys](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2).

- It is recommended to have an Internet connection in your physical
  machine, so that CyRIS can connect to Linux repositories to download
  and install tools during the cyber range creation process. If your
  machine does not have an Internet connection, please make sure to
  have a local repository that CyRIS can refer to.
## Quick Start

This first section provides some basic instructions on how to set up
CyRIS and run a basic test in order to make sure it operates
correctly. Please make sure to refer to the rest of the file for an
in-depth description, and in case of troubles.

### Installation

Follow the steps below to install CyRIS to an Ubuntu host:

- Uncompress the CyRIS archive that you downloaded

- Run a script to prepare the host for CyRIS operation

  $ ./HOST-PREPARE.sh

- Update the `CONFIG` file to reflect your CyRIS installation, in
  particular paying attention to the constants below:

  ABS_PATH = ...

  CYBER_RANGE_DIR = ...

### Base image setup

For your convenience we also provide a sample KVM base image. Follow
the steps below to set it up:

- Uncompress the sample KVM base image archive to the same Ubuntu host
  where CyRIS is installed

- Edit the file `basevm_desktop.xml` to reflect the location of the
  base image: `<source file ='...'/>`

### Operation test

Follow the steps below to run a basic test to verify that CyRIS is
installed correctly. The commands are provided assuming that the
current directory is `cyris/`.

- Edit the file `cr_desc_samples/basic_desc.yml` to reflect the host
  IP address and the location of the file `basevm_desktop.xml`

  mgmt_addr: ...

  account: ...

  basevm_config_file: ...

- Create a cyber range using the basic description edited above

  $ main/cyris.py cr_desc_samples/basic_desc.yml CONFIG

- Check the details about the created cyber range

  $ cat cyber_range/123/range_details-cr123.yml

- Check the notification about how to login to the cyber range

  $ cat cyber_range/123/range_notification-cr123.txt

- Try to login to the cyber range

  $ ssh trainee...@... -p ...

- Destroy the cyber range

  $ cyber_range/123/whole-controlled-destruction.sh

### Recovery from errors

In case you encounter errors due to mis-configuration it is
recommended that you cleanup the temporary files as follows:

- Run the cleanup script (two arguments are required)

  $ ./destroy_all_cr.sh CYRIS_PATH CYBER_RANGE_PATH

## Deployment

Below are detailed instructions about how to deploy and run CyRIS on a
physical host.

### Download CyRIS source code and base images

CyRIS source code and a sample base images can be obtained from the
GitHub. Please download and extract them somewhere in your machine
(e.g., `/home/cyuser/`). You can setup everything in two
sub-directories, `cyris/` and `images/`; the first one will contain
the CyRIS source code, and the second one your base images.

If you want to create your own base images, the following steps are
necessary in order to make automatic IP assignments work with your
virtual machines:

- Copy the content of the directory
  `cyris/cyber_instantiation/vm_clone/initif/` to
  `/bin/cyberrange/initif` inside the virtual machine

- Add to `/etc/rc.local` in the virtual machine the following line at
  the end of the file:

  /bin/cyberrange/initif/initif /bin/cyberrange/initif/initif.conf

### Install necessary tools on physical machine

In order to be able to use CyRIS, a few tools need to be installed in
the physical host. For automating this task, the bash script
`HOST-PREPARE.sh` is given (located under `cyris/` directory). Please
make sure to execute this script successfully before running CyRIS.

### Configure CyRIS constants

There are a few constants that need to specify for CyRIS to use. These
constants are specified in the file `cyris/CONFIG`, including:

- `ABS_PATH`: The absolute path of the directory of CyRIS
  (e.g., `/home/cyuser/cyris`).

- `CYBER_RANGE_DIR`: The absolute path of the directory where CyRIS
  stores base images and other scripts that are related to the being
  created cyber range.

- `GW_MODE`: This is for describing the network topology that the
  physical machine is in. If there is a gateway machine that stands
  between the physical machine and the outside network, then the
  constant `GW_MODE` should be set to "True". In contrast, if the
  physical machine connects directly to the outside network, the
  constant `GW_MODE` will be set to "False".

- `GW_ACCOUNT`: The user account on the gateway machine.

- `GW_MGMT_ADDR`: The management address of the gateway machine.

- `GW_INSIDE_ADDR`: The internal address of the gateway machine.

Note that if the `GW_MODE = False`, then the `GW_ACCOUNT`,
`GW_MGMT_ADDR`, `GW_INSIDE_ADDR` are not needed to set.


## Running CyRIS

Below are the detailed steps to follow in order to run CyRIS.

### Create the cyber range description file

The first thing needed to do is describe the desired cyber range
environment that you want CyRIS to create (i.e. how many machines you
want in the cyber range, tools and settings on each machine, the
network topology, etc.). The place for doing it is a cyber range
description file , which is written under the YAML format for the
readability purpose. A full example of this file is provided in
`cyris/CYBER-RANGE-DEF-EXAMPLE.yml`, in that it contains all the
details corresponding to each setting. Please refer to it for more
information.

### Run CyRIS

If you put CyRIS source code in the directory `/home/cyuser/cyris/`,
and your cyber range description is in
`/home/cyuser/cyris/cyber_range_def.yml`, then the command to run
CyRIS should be:

$ /home/cyuser/cyris/main/cyris.py /home/cyuser/cyris/cyber_range_def.yml /home/cyuser/cyris/CONFIG

### Check the output

CyRIS records logs of a cyber range creation process into the file
`cyris/cyber_range/<range_id>/creation.log`. Please take a look at the
file if you want to verify yourself if the cyber range is created is
successful.

If CyRIS execution finishes successfully, two files will be created in
the created cyber range directory `CYBER_RANGE_DIR/<range_id>/`, as
follows:

- `range_notification-cr<range_id>.txt`: Information about how to
  login to the cyber range.

- `range_details-cr<range_id>.yml`: Details about the created cyber
  range.

Please consult these files before accessing the cyber range. Note that
only the login information needs to be provided to trainees, the
details are meant for the training organizer.

### Destroy the cyber range

After creating a cyber range, CyRIS produces a script, named
`cyris/cyber_range/<range_id>/whole-controlled-destruction.sh`, for
destroying the cyber range. Please execute this script if you want to
destroy a cyber range.

In some cases, the cyber range is partially created and the process
crashes in the middle. For these situations, please execute the script
`cyris/destroy_all_cr.sh`, with two arguments which are the absolute
path of CyRIS, and the `CYBER_RANGE_DIR` that you specified in the
CONFIG file. This script will look for existing cyber ranges and
destroy them all, alongside cleaning up the directory.


## Known issues

There are a number of limitations in the current CyRIS version, as
follows:

- Although we have already tested CyRIS in various scenarios, it is
  not considered yet to be production-ready. Issue reporting via
  GitHub is welcome.

- The tool `cpulimit` is currently used to control CPU utilization for
  dummy malware emulation. If you require this functionality, please
  copy the *source code* of `cpulimit` to the directory
  `cyris/cyber_instantiation/malware_creation/cpulimit`. `cpulimit` is
  available here: https://github.com/opsengine/cpulimit

- The noise addition feature for traffic capture file generation
  requires the presence of several pcap files in the directory
  `cyris/cyber_instantiation/logs_preparation`. If you require this
  functionality, please create the files by capturing traffic with
  various data rates and name the files `noise_low.pcap`,
  `noise_medium.pcap` and `noise_high.pcap`.

## References

For a research background please consult the following paper:
* C. Pham, D. Tang, K. Chinen, R. Beuran, "CyRIS: A Cyber Range Instantiation System for Facilitating Security Training", International Symposium on Information and Communication Technology (SoICT 2016), Ho Chi Minh, Vietnam, December 8-9, 2016, pp. 251-258.
