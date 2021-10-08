#!/usr/bin/env python3
import pw5conv
from nbt import nbt
import numpy as np
import sys

def gen_heatmap_schematic(name, out=None):
    '''
    Generates pw5 heatmap in schematic format, untrimmed
    '''
    schem = nbt.NBTFile()
    schem.name = 'Schematic'
    schem['Materials'] = nbt.TAG_String('Alpha')
    schem['TileEntities'] = nbt.TAG_List(nbt.TAG_Compound)

    blocks = pw5conv.gen_heatmap(pw5conv.load_pw5_map(name))
    blocks = blocks.transpose(1, 0, 2) # ZYX into YXZ
    datas = np.zeros_like(blocks)

    schem['Height'], schem['Width'], schem['Length'] = tuple(nbt.TAG_Short(a) for a in blocks.shape)

    sblocks = nbt.TAG_Byte_Array()
    sblocks.value = blocks.ravel()
    schem['Blocks'] = sblocks

    sdatas = nbt.TAG_Byte_Array()
    sdatas.value = datas.ravel()
    schem['Data'] = sdatas

    if out is None:
        if sys.stdout.isatty():
            print("Error! Stdout is a tty.\nPlease redirect output to file by typing:\n{} {} > [file]".format(sys.argv[0], sys.argv[1]))
            exit(2)
        schem.write_file(fileobj=sys.stdout.buffer)
    else:
        schem.write_file(out)

if __name__ == '__main__':
    gen_heatmap_schematic(sys.argv[1])
