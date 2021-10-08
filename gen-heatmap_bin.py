#!/usr/bin/env python3
import pw5conv
import struct
import sys

def gen_heatmap_binary(pw5name, out=None):
    '''
    Generate Heatmap Info in a file
        * Binary Header (PW5HMAP\\t)
        * PW5 Map Size
        * Trimmed Ranges
        * Section Heatmap (untrimmed) in compressed bytes:
          * for each sections, if section contains data, output 1, otherwise 0
    '''
    pmap = pw5conv.load_pw5_map(pw5name)
    dsize, drange = pw5conv.get_pw5_info(pmap)
    packedbytes = pw5conv.pack_hmap(pw5conv.gen_heatmap(pmap))

    if out is None:
        if sys.stdout.isatty():
            print("Error! Stdout is a tty.\nPlease redirect output to file by typing:\n{} {} > [file]".format(sys.argv[0], sys.argv[1]))
            exit(2)
        fout = sys.stdout.buffer
    else:
        fout = open(out, 'wb')

    fout.write(b'PW5HMAP\t')
    fout.write(struct.pack('>3h', *dsize))
    fout.write(struct.pack('>6h', *[j for i in drange for j in i]))
    fout.write(packedbytes)
    fout.close()

if __name__ == '__main__':
    gen_heatmap_binary(sys.argv[1])
