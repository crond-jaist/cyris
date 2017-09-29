# CyRIS: Cyber Range Instantiation System

CyRIS is a tool for facilitating cybersecurity training by automating the creation and management of the corresponding training environments (a.k.a, cyber ranges) based on a description provided in YAML format. CyRIS being developed by the Cyber Range Organization and Design (CROND) NEC-endowed chair at the Japan Advanced Institute of Science and Technology (JAIST).

An overview of the CyRIS workflow is provided below. Based on the input cyber range description, and a collection of virtual machine base images, CyRIS performs preparation, content installation and cloning in order to deploy the cyber range on a given server infrastructure.

![CyRIS workflow](https://github.com/crond-jaist/cyris/blob/master/cyris_workflow.png "CyRIS workflow")

CyRIS is written in Python, and has various features, including system configuration, tool installation, incident emulation, content management, and clone management. If interested, please download the latest release and let us know if you have any issues. A sample virtual machine base image is also provided for your convenience.

Next we provide brief information on the prerequisites for running CyRIS, as well as its setup and use. Please refer to the accompanying User Guide for details.

## Installation

The procedure for installing and configuring CyRIS is rather complex, therefore you should refer to the User Guide for details. In particular the following issues are to be considered:

* Hardware requirements: Hardware vrtualization support, Internet connection (optional) -- See Section 3.1 of the User Guide.
* Software installation: Host preparation, base image preparation, CyRIS configuration -- See Section 3.2 of the User Guide.

## Quick Start

This section provides some basic instructions on how to run a basic test in order to make sure CyRIS operates correctly. In what follows we assume that the installation procedure mentioned above was conducted successfully, and the current directory is the directory where CyRIS was installed.

### Items to check
Some key issues that must not be forgotten before proceeding to running CyRIS are:

* The configuration file `CONFIG` needs to reflect your actual CyRIS installation, in particular paying attention to the constants below:

  `cyris_path = ...`
  
  `cyber_range_dir = ...`

* The sample KVM base image must be present on the CyRIS host, and the content of the file `basevm_small.xml` must reflect the actual location of the base image:

  `<source file ='...'/>`

* The content of sample file `examples/basic.yml` should reflect the actual host properties, and the actual location of the file `basevm_small.xml` in the corresponding sections:

  `mgmt_addr: ...`

  `account: ...`

  `basevm_config_file: ...`


### Operation test
* Create a cyber range using the basic description edited above:

  `$ main/cyris.py examples/basic.yml CONFIG`

* Check the details regarding the created cyber range:

  `$ cat cyber_range/123/range_details-cr123.yml`

* Check the notification about how to login to the cyber range:

  `$ cat cyber_range/123/range_notification-cr123.txt`

* Try to login into the cyber range:

  `$ ssh trainee01@... -p ...`

* Destroy the cyber range:

  `$ main/range_cleanup.sh 123 CONFIG`

### Recovery from errors

In case you encounter errors due to mis-configurations, and the cleanup command above is insufficient to restore correct operation, you can also clean up the temporary files via a special cleanup script (two arguments are required):

  `$ ./destroy_all_cr.sh CYRIS_PATH CYBER_RANGE_PATH`

## Known issues

There are a number of limitations in the current CyRIS version, as
follows:

- Although we have already tested CyRIS in various scenarios, it is
  not considered yet to be production-ready. Issue reporting via
  GitHub is welcome.

- The tool `cpulimit` is currently used to control CPU utilization for
  dummy malware emulation. If you require this functionality, please
  copy the *source code* of `cpulimit` to the directory
  `cyris/instantiation/malware_creation/cpulimit`. `cpulimit` is
  available here: https://github.com/opsengine/cpulimit

- The noise addition feature for traffic capture file generation
  requires the presence of several pcap files in the directory
  `cyris/instantiation/logs_preparation`. If you require this
  functionality, please create the files by capturing traffic with
  various data rates and name the files `noise_low.pcap`,
  `noise_medium.pcap` and `noise_high.pcap`.

## References

For a research background about CyRIS, please consult the following paper:
* C. Pham, D. Tang, K. Chinen, R. Beuran, "CyRIS: A Cyber Range Instantiation System for Facilitating Security Training", International Symposium on Information and Communication Technology (SoICT 2016), Ho Chi Minh, Vietnam, December 8-9, 2016, pp. 251-258.
