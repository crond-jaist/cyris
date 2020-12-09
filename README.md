
# CyRIS: Cyber Range Instantiation System

CyRIS is a tool for facilitating cybersecurity training by automating
the creation and management of the corresponding training environments
(a.k.a., cyber ranges) based on a description in YAML format. CyRIS is
being developed by the Cyber Range Organization and Design (CROND)
NEC-endowed chair at the Japan Advanced Institute of Science and
Technology (JAIST).

An overview of the CyRIS workflow is provided below. Based on the
input cyber range description, and a collection of virtual machine
base images, CyRIS performs preparation, content installation and
cloning in order to deploy the cyber range on a given server
infrastructure.

![CyRIS workflow](https://github.com/crond-jaist/cyris/blob/master/cyris_workflow.png "CyRIS workflow")

CyRIS is written in Python, and has various features, including system
configuration, tool installation, incident emulation, content
management, and clone management. If interested, please download the
[latest release](https://github.com/crond-jaist/cyris/releases/) and
let us know if you have any issues; a sample virtual machine base
image and a user guide are also provided for your convenience.

The procedure for installing and configuring CyRIS is rather complex,
therefore you should refer to the User Guide. In particular, the
following issues are to be considered:

* _Hardware requirements_: Hardware vrtualization support, Internet
  connection (optional) -- See Section 3.1 of the User Guide.
* _Software installation_: Host preparation, base image preparation,
  CyRIS configuration -- See Section 3.2 of the User Guide.


## Quick Start

This section provides some basic instructions on how to run a basic
test in order to make sure CyRIS operates correctly. In what follows
we assume that the installation procedure mentioned above was
conducted successfully, and the current directory is the directory
where CyRIS was installed. Please refer to the accompanying User Guide
for details.

### Preliminary checks

Some key issues that must not be forgotten before proceeding to
running CyRIS are:

* The configuration file `CONFIG` needs to reflect your actual CyRIS
  installation, in particular paying attention to the constants below:

  `cyris_path = ...`
  
  `cyber_range_dir = ...`

* The sample KVM base image must be present on the CyRIS host, and the
  content of the file `basevm_small.xml` must reflect the actual
  location of the base image:

  `<source file ='...'/>`

* The content of sample file `examples/basic.yml` should reflect the
  actual host properties, and the actual location of the file
  `basevm_small.xml` in the corresponding sections:

  `mgmt_addr: ...`

  `account: ...`

  `basevm_config_file: ...`

### Basic operation

A typical sequence of operations is as follows:

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

Ocasionally an error such as `No route to host` appears. We are
currently investigating its exact cause, but for the moment you should
just destroy the partially created cyber range and repeat the creation
process.

In case you encounter subsequent errors due to mis-configurations, and
the range cleanup command above is insufficient to restore correct
operation, you can also clean up the temporary files via a special
cleanup script (two arguments are required):

  `$ ./destroy_all_cr.sh CYRIS_PATH CYBER_RANGE_PATH`


## References

For a research background about CyRIS, please consult the following
paper:

* R. Beuran, C. Pham, D. Tang, K. Chinen, Y. Tan, Y. Shinoda,
  "Cybersecurity Education and Training Support System: CyRIS", IEICE
  Transactions on Information and Systems, vol. E101-D, no. 3, March
  2018, pp. 740-749.

For the list of contributors, please check the file CONTRIBUTORS.
