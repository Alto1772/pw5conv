#!/usr/bin/env python3
import pw5conv
import sys

overlay = False
for i in range(1, len(sys.argv)):
    if sys.argv[i] == '-o':
        overlay = True
        sys.argv.pop(i)

pw5conv.save_to_mc_world(sys.argv[2], pw5conv.load_pw5_map(sys.argv[1]), overlay=overlay)
