#!/usr/bin/env python3
import pw5conv
import sys

overlay = False
overlay_pw5_after_mc = False
optlen = 0
for i in range(1, len(sys.argv)):
    if sys.argv[i-optlen] == '-o':
        overlay = True
        sys.argv.pop(i)
        optlen += 1
    elif sys.argv[i-optlen] == '-m':
        overlay = True
        overlay_pw5_after_mc = True
        sys.argv.pop(i)
        optlen += 1

pw5conv.save_to_mc_world(sys.argv[2], pw5conv.load_pw5_map(sys.argv[1]), overlay=overlay, overlay_pw5_after_mc=overlay_pw5_after_mc)
