#!/usr/bin/env python

import sys

RULESET_FILE = sys.argv[1]
IPCONFIGS_TEMP = sys.argv[2]

class AppendRuleset():
    def readRuleset(self):
        list_rules = []
        f = open(RULESET_FILE, "r")
        if not f:
            print("Cannot open firewall ruleset file '{}' => abort ruleset append".format(RULESET_FILE));
            return None
        for line in f:
            list_rules.append(line)
        return list_rules

    def appendRuleset(self):
        list_rules = self.readRuleset()

        if list_rules:
            with open(IPCONFIGS_TEMP, "a") as f:
                for rule in list_rules:
                    f.write(rule)
                f.write("COMMIT\n")

appendRuleset = AppendRuleset()
appendRuleset.appendRuleset()
