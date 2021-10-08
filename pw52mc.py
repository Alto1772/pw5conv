#!/usr/bin/env python3
import pw5conv
import sys

pw5conv.save_to_mc_world(sys.argv[2], pw5conv.load_pw5_map(sys.argv[1]))
