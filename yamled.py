#!/bin/env python

import sys
import ruamel.yaml as ryaml


yaml=ryaml.YAML()
yaml.indent(mapping=4)
data=yaml.load(sys.stdin)
yaml.dump(data,sys.stdout)