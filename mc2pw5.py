#!/usr/bin/env python3
import pw5conv
import sys
import os
import numpy as np
import struct

def read_heatmap_bin(filename):
    f = open(filename, 'rb')
    if f.read(8) != b'PW5HMAP\t':
        raise Exception("Invalid Heatmap file")
    dsize = struct.unpack('>3h', f.read(6))
    drange = struct.unpack('>6h', f.read(12))
    hmap = pw5conv.unpack_hmap(f.read(), dsize)
    return dsize, np.array(drange).reshape(3,2), hmap

def get_pw5_info(pw5dir, trim=None):
    pw5map = pw5conv.load_pw5_map(pw5dir)
    hmap = pw5conv.gen_heatmap(pw5map)
    return pw5map.shape, pw5conv.ndrange_trim(pw5map) if not trim else trim, hmap

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: {} <mcdir> (<pw5dir> | <hmapbin> <pw5dir>)".format(sys.argv[0]))
        exit(1)
    mcdir = sys.argv[1]
    pw5dir = sys.argv[2]
    if not os.path.exists(pw5dir):
        raise FileNotFoundError("{} not found".format(pw5dir))
    elif os.path.isdir(pw5dir):
        pw5_info = get_pw5_info(pw5dir)
    else:
        pw5_info = read_heatmap_bin(pw5dir)
        pw5dir = sys.argv[3]

    pw5conv.print_ndrange(pw5_info[1], ('X','Y','Z'))
    npmcmap = pw5conv.load_mc_world(mcdir, *pw5_info)
    pw5conv.save_to_pw5_map(pw5dir, npmcmap)
