#!/usr/bin/env python3
import pw5conv
import numpy as np
import sys

_slice16s4 = slice(0,16,8)
_diag16_step4 = (_slice16s4,)*3
def gen_borderchunk():
    ret = np.zeros((16,16,16), 'i1')
    #line = np.zeros((16, 16), 'i1')
    #line[np.diag_indices(16)] = 1
    ret[:,0,0] = 28
    ret[0,:,0] = 19
    ret[0,0,:] = 21
    ret[0,0,0] = 16

    #ret[np.diag_indices(16, 3)] = 16
    #ret[_diag16_step4] = 16
    #ret[:,    0,    :] = np.where(line, 34, 0)
    #ret[:,   -1, ::-1] = np.where(line, 19, 0)
    #ret[0,    :,    :] = np.where(line, 20, 0)
    #ret[-1,::-1,    :] = np.where(line, 23, 0)
    #ret[:,    :,    0] = np.where(line, 27, 0)
    #ret[:, ::-1,   -1] = np.where(line, 28, 0)
    return pw5conv.encode_chunk(ret).replace('\x00','\ufffe')

def gen_active_chunks(pw5dirmap):
    pw5map = pw5conv.load_pw5_map(pw5dirmap)
    return pw5map != ''

if __name__ == '__main__':
    npmap = gen_active_chunks(sys.argv[1])
    npmap = np.where(npmap, gen_borderchunk(), '')
    pw5conv.save_to_mc_world(sys.argv[2], npmap)
