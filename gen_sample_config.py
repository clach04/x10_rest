#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""Generate demo config YAML for Home Assistant REST Switch
Python 2 or Python 3

See https://www.home-assistant.io/integrations/switch.rest
"""

import os
import sys

def gen_sample_config(house_code='A'):
    # So dumb, no templating used
    print('# Sample entries for configuration.yaml')
    print('''
switch:''')
    for unit_num in range(1, 16+1):
        print('  - platform: rest')
        print('    resource: http://localhost:1234/x10/%s/%d' % (house_code, unit_num))
        print('    name: "%s%d Switch"' % (house_code, unit_num))


def main(argv=None):
    if argv is None:
        argv = sys.argv

    gen_sample_config()

    return 0


if __name__ == "__main__":
    sys.exit(main())

