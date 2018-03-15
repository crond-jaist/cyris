class Storyboard:
    # Constants regarding the input file
    ## Host settings
    HOST_SETTINGS = "host_settings"
    ID = "id"
    MGMT_ADDR = "mgmt_addr"
    VIRBR_ADDR = "virbr_addr"
    ACCOUNT = "account"
    NOT_AVAIL = "N/A"

    ## Guest settings
    GUEST_SETTINGS = "guest_settings"
    ID4GUEST = "id"
    IP_ADDR = "ip_addr"
    BASEVM_HOST = "basevm_host"
    BASEVM_CONFIG_FILE = "basevm_config_file"
    BASEVM_TYPE = "basevm_type"
    TASKS = "tasks"

    ADD_ACCOUNT = "add_account"
    ACCOUNT = "account"
    PASSWD = "passwd"
    FULL_NAME = "full_name"
    MODIFY_ACCOUNT = "modify_account"
    NEW_ACCOUNT = "new_account"
    NEW_PASSWD = "new_passwd"

    INSTALL_PACKAGE = "install_package"
    PACKAGE_MANAGER = "package_manager"
    NAME4PACKAGE = "name"
    VERSION = "version"

    EMULATE_ATTACK = "emulate_attack"
    ATTACK_TYPE ="attack_type"
    TARGET_ACCOUNT = "target_account"
    ATTEMPT_NUMBER = "attempt_number"
    ATTACK_TIME = "attack_time"

    EMULATE_TRAFFIC_CAPTURE_FILE = "emulate_traffic_capture_file"
    FORMAT = "format"
    FILE_NAME = "file_name"
    ATTACK_TYPE = "attack_type"
    SSH_ATTACK = "ssh_attack"
    DOS_ATTACK = "dos_attack"
    DDOS_ATTACK = "ddos_attack"
    ATTACK_SOURCE = "attack_source"
    NOISE_LEVEL = "noise_level"

    EMULATE_MALWARE = "emulate_malware"
    NAME4MALWARE = "name"
    MODE = "mode"
    DUMMY_CALCULATION = "dummy_calculation"
    PORT_LISTENING = "port_listening"
    CPU_UTILIZATION ="cpu_utilization"
    PORT = "port"

    COPY_CONTENT = "copy_content"
    SRC = "src"
    DST = "dst"

    EXECUTE_PROGRAM = "execute_program"
    PROGRAM = "program"
    ARGS ="args"
    INTERPRETER = "interpreter"
    EXECUTE_TIME = "execute_time"

    FIREWALL_RULES = "firewall_rules"
    RULE = "rule"

    ## Clone settings
    CLONE_SETTINGS = "clone_settings"
    RANGE_ID = "range_id"
    HOSTS = "hosts"
    HOST_ID = "host_id"
    INSTANCE_NUMBER = "instance_number"
    GUESTS = "guests"
    GUEST_ID = "guest_id"
    NUMBER = "number"
    ENTRY_POINT = "entry_point"
    FORWARDING_RULES = "forwarding_rules"
    #RULE = "rule" # Also defined in guests...
    TOPOLOGY = "topology"
    TYPE = "type"
    NETWORKS = "networks"
    NAME = "name"
    MEMBERS = "members"
    GATEWAY = "gateway"

    # Constants regarding the output range details file
    # (values that appear identically above are not repeated)

    #RANGE_ID = "range_id"
    #HOSTS = "hosts"
    #HOST_ID = "host_id"
    INSTANCE_COUNT = "instance_count"
    INSTANCES = "instances"
    INSTANCE_INDEX = "instance_index"
    #GUESTS = "guests"
    #GUEST_ID = "guest_id"
    KVM_DOMAIN = "kvm_domain"
    IP_ADDRS = "ip_addrs"
    GATEWAYS = "gateways"
    FIREWALL_RULE = "firewall_rule"
    NETWORK_MEMBERSHIP = "networks"

    # Constants regarding the configuration file
    SECTION_NAME = "config"
    CYRIS_PATH = "cyris_path"
    CYBER_RANGE_DIR = "cyber_range_dir"
    GW_MODE = "gw_mode"
    GW_ACCOUNT = "gw_account"
    GW_MGMT_ADDR = "gw_mgmt_addr"
    GW_INSIDE_ADDR = "gw_inside_addr"
    USER_EMAIL = "user_email"
