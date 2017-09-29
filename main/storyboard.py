class Storyboard:
    # Constants regarding the input file
    ## Host settings
    HOST_SETTINGS = "host_settings"
    ID = "id"
    MGMT_ADDR = "mgmt_addr"
    VIRBR_ADDR = "virbr_addr"
    ACCOUNT = "account"

    ## Guest settings
    FIREWALL_RULES = "firewall_rules"
    RULE = "rule"
    FULL_NAME = "full_name"

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
