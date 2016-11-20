'''
masterless.enc

External Node Classifier
'''

#
# FIXME:
# Move logging setup to fabric common init? (where is that?)
#

import logging
import logging.handlers
import sys
import yaml

def cli():
    fqdn = sys.argv[1]

    logger = logging.getLogger(__name__)
    logger.addHandler(logging.handlers.SysLogHandler(address='/var/run/syslog', facility='local1'))

    logger.error("Calling ENC for {0}".format(fqdn))

    if fqdn == "dst.aws.disasterarea.ninja":
        print yaml.dump({
            "classes": ["role::dontstarve"],
            "parameters": {"role": "dontstarve"},
            }, default_flow_style=False, explicit_start=True)

    return 0



