#!/usr/bin/python

import ConfigParser
import logging
import os.path

from storyboard import Storyboard

##################################################################
# Function for parsing parameters provided in CONFIG file
##################################################################

def parse_config(config_file):

    abs_path = None
    cr_dir = None
    gw_mode = False
    gw_account = None
    gw_mgmt_addr = None
    gw_inside_addr = None
    user_email = None

    if os.path.exists(config_file):

        # Create object and read config file
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        # Process the options
        for option in config.options(Storyboard.SECTION_NAME):
            value = config.get(Storyboard.SECTION_NAME, option)
            logging.debug("Option '{0}' => {1}".format(option, value))
            if option == Storyboard.CYRIS_PATH:
                abs_path = value
            elif option == Storyboard.CYBER_RANGE_DIR:
                cr_dir = value
            elif option == Storyboard.GW_MODE:
                # gw_mode is a boolean, so we get again the value as boolean
                gw_mode = config.getboolean(Storyboard.SECTION_NAME, option)
            elif option == Storyboard.GW_ACCOUNT:
                gw_account = value
            elif option == Storyboard.GW_MGMT_ADDR:
                gw_mgmt_addr = value
            elif option == Storyboard.GW_INSIDE_ADDR:
                gw_inside_addr = value
            elif option == Storyboard.USER_EMAIL:
                user_email = value
            else:
                logging.warning("Unknown configuration option: " + option)

    else:
        logging.error("Configuration file not found: " + config_file)
        return [False] * 7

    return abs_path, cr_dir, gw_mode, gw_account, gw_mgmt_addr, gw_inside_addr, user_email
