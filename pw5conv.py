import numpy as np
import os
import time
from nbt import *

data_version = 1343 # MC 1.12.2

# TODO: move this into txt file
# NOTE: defblocks shall not have duplicates for now
defblocks = np.array([
    (0,    0), # 0:  None
    (2,    0), # 1:  Grass Block
    (3,    0), # 2:  Dirt
    (98,   0), # 3:  Stone Bricks
    (24,   0), # 4:  Sand (as Sandstone, due to Sand being a falling block)
    (35,   0), # 5:  White Wool
    (206,  0), # 6:  Sandstone brick??? (as End Brick)
    (25,   0), # 7:  Oak Wood Plank with Steel Casing??? (as Note Block)
    (20,   0), # 8:  Glass
    (18,   6), # 9:  Birch Leaves
    (48,   0), # 10: Mossy Stone (as Mossy Cobblestone)
    (98,   1), # 11: Mossy Stone Bricks
    (22,   0), # 12: Blue Tiles??? (as Lapis Lazuli Block)
    (47,   0), # 13: Bookshelf
    (5,    0), # 14: Oak Wood Plank
    (98,   3), # 15: Chiseled Stone Bricks???
    (45,   0), # 16: Bricks
    (17,   0), # 17: Oak Log
    (88,   0), # 18: ??? (i don't know what kind of block this is, assume this as Soul Sand)
    (35,   5), # 19: Lime Wool
    (35,   2), # 20: Magenta Wool
    (35,   3), # 21: Light Blue Wool
    (35,   1), # 22: Orange Wool
    (35,  13), # 23: Green Wool
    (35,   6), # 24: Pink Wool
    (35,   7), # 25: Gray Wool
    (35,  10), # 26: Purple Wool
    (35,   9), # 27: Cyan Wool
    (35,  14), # 28: Red Wool
    (35,  12), # 29: Brown Wool
    (35,   8), # 30: Light Gray Wool
    (35,  11), # 31: Blue Wool
    (42,   0), # 32: Iron Block
    (35,  15), # 33: Black Wool
    (35,   4), # 34: Yellow Wool
    (112,  0), # 35: Nether Brick
    (101,  0), # 36: Iron Bars Block (as a cross-sided block)
    (174,  0), # 37: Ice Block (as Packed Ice)
])

# "Static" Variables used for reverse_index
_len_defb = defblocks.shape[0]
_empty_block = np.full(_len_defb, False)
_empty_block[0] = True

#
#  Utilities
#

def printerr(*args, **kwargs):
    import sys
    print(*args, file=sys.stderr, **kwargs)

def offsethalf(offset, length):
    return offset - length // 2

def rangehalf(length):
    qu, rm = divmod(length, 2)
    minim = -qu     if rm == 1 else qu
    maxim =  qu + 1 if rm == 1 else qu
    return range(minim, maxim)

def print_ndrange(ndrange, dimnames=("X","Y","Z","W")):
    print("  Trim Ranges:")
    print("    Start   End")
    for ii, i in enumerate(ndrange):
        print(' {:s}  {:3d}   {:4d}'.format(dimnames[ii], *i))

def ndrange_trim(ndarr):
    nz = np.asarray(np.nonzero(ndarr))
    return np.asarray((nz.min(axis=1), np.array(ndarr.shape) - nz.max(axis=1) - 1)).T

def trim_ndarray(ndarr):
    ndrange = ndrange_trim(ndarr)
    return ndrange, ndarr[tuple(slice(a[0], -a[1]) for a in ndrange)]

def untrim_ndarray(ndarr, ndrange, value=0):
    return np.pad(ndarr, ndrange, 'constant', constant_values=value)

def reverse_index(picked):
    '''
    Convert data blocks into index from defblocks.
    Some blocks that are not specified in defblocks are replaced with 0.
    '''
    #assert picked.shape[1] == 2
    sp = picked.shape[0]
    rd = np.repeat(defblocks, sp, 0).reshape(-1, sp, 2)
    rp = np.tile(picked, (_len_defb, 1, 1))

    c = (rd == rp).all(2).T
    c[np.where(~c.any(1))] = _empty_block
    r = np.where(c)[1]

    # duplicates in defblocks might be the problem if the statement below fails
    assert r.size == sp
    return r

def encode_chunk(npchunk):
    '''
    Encodes a chunk by RLE compression, outputs a string
    '''
    assert npchunk.shape == (16, 16, 16)
    #assert npchunk.dtype == np.dtype('>i2')
    c = npchunk.ravel()

    #  https://stackoverflow.com/a/32681075
    y = ~np.isclose(c[1:], c[:-1])
    i = np.append(np.where(y), 4096 - 1)
    z = np.diff(np.append(-1, i))

    rlchunk = np.asarray((z, c[i])).T
    return ''.join(chr(v) for v in rlchunk.ravel())

def decode_chunk(chunkstr):
    '''
    Decodes a chunk by RLE decompression, outputs a numpy array
    '''
    assert isinstance(chunkstr, str)
    assert len(chunkstr) % 2 == 0
    rlchunk = np.fromiter((ord(v) for v in chunkstr), '>i2')
    assert np.sum(rlchunk[::2]) == 4096
    return rlchunk[1::2].repeat(rlchunk[::2]).reshape(16, 16, 16)

_pslice = slice(None, None, 1)
_nslice = slice(None, None, -1)

def invert_nd(*coords):
    return tuple(_nslice if v < 0 else _pslice for v in coords)

def gen_heatmap(npmap):
    '''
    Generates pw5 heatmap from np.array
    '''
    return (npmap != '').astype('uint8')  # heatmap

def get_pw5_info(npmap):
    ndsize = npmap.shape
    trimrange = ndrange_trim(npmap)
    return ndsize, trimrange

def pack_hmap(heatmap):
    return bytearray(np.packbits(heatmap.reshape(-1, 8), bitorder='big'))

def unpack_hmap(packed_hmap, shape=(10,10,10)):
    return np.unpackbits(bytearray(packed_hmap), bitorder='big').reshape(*shape)

class IncompatibleWorldVersion(Exception):
    def __init__(self, datver=data_version):
        self.datver = datver
    def __str__(self):
        return "MC Data Version {} is not compatible with this program.".format(self.datver)
#
#  Pw5 Map Reading Functions
#

def load_pw5_region(name, x, y, z):
    #  NOTE: temporary xz-inverted (needs some clear understanding)
    reg = os.path.join(name, '{},{},{},.region'.format(z, y, x))
    if os.path.exists(reg):
        with open(reg, 'r', encoding='utf8', newline='') as f:
            arr = np.array(f.read().replace('\x00','\ufffe').split('\uffff')).reshape(10,10,10)
        return arr[invert_nd(x, y, z)]
    else:
        return None

def load_pw5_map(name):
    if not os.path.exists(name):
        raise FileNotFoundError("PW5 Map \"{}\" does not exist".format(name))
    rx = []
    for x in range(-2, 2):
        rz = []
        for z in range(-2, 2):
            ry = []
            for y in (-1, 0):
                arr = load_pw5_region(name, x, y, z)
                if arr is None:
                    ry.append(np.full((10,10,10), ''))
                else: ry.append(arr)
            rz.append(np.concatenate(ry, 1))
        rx.append(np.concatenate(rz, 2))
    ret = np.concatenate(rx, 0)
    if (ret == '').all():
        raise Exception("The PW5 Map Folder \"{}\" is empty".format(name))
    return ret

#
#  MC Map Editing Functions
#

def overlay_section(y, mcsect, strchunk, withlight=False, overlay_pw5_after_mc=False):
    '''
    Overlays pw5 chunk to MC chunk section
    '''
    assert strchunk != ''
    npchunk = decode_chunk(strchunk.replace('\ufffe', '\x00'))
    npchunk = npchunk.transpose(1, 2, 0) # ZYX into YZX
    sect = nbt.TAG_Compound()
    sect['Y'] = nbt.TAG_Byte(y)
    
    convblocks = defblocks[npchunk.ravel()]
    mcnpbb = np.array(mcsect['Blocks'].value, dtype='uint8')
    mcnpbd = np.array(mcsect['Data'].value, dtype='uint8')
    mcnpbd = np.stack((mcnpbd & 0xf, mcnpbd >> 4)).T.ravel()
    mcblocks = np.stack((mcnpbb, mcnpbd)).T
    if overlay_pw5_after_mc:
        npmask = np.logical_and(mcblocks[:, 0] == 0, convblocks[:, 0] != 0)
        ovblocks = np.where(np.repeat(npmask, 2).reshape(-1, 2), convblocks, mcblocks)
    else:
        npmask = np.logical_and(mcblocks[:, 0] != 0, convblocks[:, 0] == 0)
        ovblocks = np.where(np.repeat(npmask, 2).reshape(-1, 2), mcblocks, convblocks)
    
    bs = nbt.TAG_Byte_Array()
    bl = nbt.TAG_Byte_Array()
    if withlight:
        mcnpbs = np.array(mcsect['SkyLight'].value, dtype='uint8')
        mcnpbs = np.stack((mcnpbs & 0xf, mcnpbs >> 4)).T.ravel()
        cobs = np.where(npmask, mcnpbs, 15)
        bs.value = (cobs[::2] | cobs[1::2] << 4).astype('uint8')
        mcnpbl = np.array(mcsect['BlockLight'].value, dtype='uint8')
        mcnpbl = np.stack((mcnpbl & 0xf, mcnpbl >> 4)).T.ravel()
        cobl = np.where(npmask, mcnpbl, 0)
        bl.value = (cobl[::2] | cobl[1::2] << 4).astype('uint8')
    else:
        bs.value = np.full(2048, -1, 'int8')
        bl.value = np.full(2048, 0, 'int8')
    sect['SkyLight'] = bs
    sect['BlockLight'] = bl

    bb = nbt.TAG_Byte_Array()
    bb.value = ovblocks[:, 0].astype('uint8')
    sect['Blocks'] = bb
    bd = nbt.TAG_Byte_Array()
    bd.value = (ovblocks[::2, 1] | ovblocks[1::2, 1] << 4).astype('uint8')
    sect['Data'] = bd

    return sect

def make_section(y, strchunk):
    '''
    Creates one chunk section (16x16x16 blocks) from strchunk
    '''
    assert strchunk != ''
    npchunk = decode_chunk(strchunk.replace('\ufffe', '\x00'))
    npchunk = npchunk.transpose(1, 2, 0) # ZYX into YZX

    sect = nbt.TAG_Compound()
    sect['Y'] = nbt.TAG_Byte(y)
    bs = nbt.TAG_Byte_Array()
    bs.value = np.full(2048, -1, 'int8')
    sect['SkyLight'] = bs
    bl = nbt.TAG_Byte_Array()
    bl.value = np.full(2048, 0, 'int8')
    sect['BlockLight'] = bl

    convblocks = defblocks[npchunk.ravel()]
    bb = nbt.TAG_Byte_Array()
    bb.value = convblocks[:, 0].astype('uint8')
    sect['Blocks'] = bb
    bd = nbt.TAG_Byte_Array()
    bd.value = (convblocks[::2, 1] | convblocks[1::2, 1] << 4).astype('uint8')
    sect['Data'] = bd
    return sect

def make_chunk(nptower):
    '''
    Creates one chunk (16x256x16 blocks)
    '''
    nbtsections = nbt.TAG_List(nbt.TAG_Compound)
    sections = {}
    bsects = nptower != ''        # if any of y sections contains something
    assert bsects.ndim == 1

    for (y, ), cond in np.ndenumerate(bsects):
        if cond:
            sections[y] = make_section(y, nptower[y])
    nbtsections.tags = list(sections.values())
    return nbtsections

def make_mc_chunk(x, z, nptower):
    '''
    Creates MC 1.12 MCRegion chunk

    Note: NBT data derived from generated void world using MC client version 1.12.2
    '''

    nbtroot = nbt.NBTFile()
    nbtroot['DataVersion'] = nbt.TAG_Int(data_version)

    nbtchunk = nbt.TAG_Compound()
    nbtchunk['xPos'] = nbt.TAG_Int(x)
    nbtchunk['zPos'] = nbt.TAG_Int(z)
    nbtchunk['LightPopulated'] = nbt.TAG_Byte(0)
    nbtchunk['TerrainPopulated'] = nbt.TAG_Byte(1)
    nbtchunk['InhabitedTime'] = nbt.TAG_Long(0)
    nbtchunk['LastUpdate'] = nbt.TAG_Long(0)
    nbtchunk['Entities'] = nbt.TAG_List(nbt._TAG_End)
    nbtchunk['TileEntities'] = nbt.TAG_List(nbt._TAG_End)

    nbtbiomes = nbt.TAG_Byte_Array()
    nbtbiomes.value = np.full(256, -1, 'int8')
    nbtchunk['Biomes'] = nbtbiomes
    nbthmap = nbt.TAG_Int_Array()
    nbthmap.value = np.full(256, 0, 'uint32')
    nbtchunk['HeightMap'] = nbthmap

    nbtsections = make_chunk(nptower)
    nbtchunk['Sections'] = nbtsections

    nbtroot['Level'] = nbtchunk
    return nbtroot


def put_pw5_to_mc_chunk(nbtroot, nptower, overlay=False, withlight=False, **ovkwargs):
    '''
    Overwrites MC 1.12 chunk sections if any of the pw5 chunks have data
    if overlay is true, it will overlay pw5 map to mc world
    '''

    if nbtroot['DataVersion'].value != data_version:
        raise IncompatibleWorldVersion(nbtroot['DataVersion'].value)
    #    nbtroot['DataVersion'].value = data_version
    light_popul = 0
    nbtchunk = nbtroot['Level']
    nbtchunk['TerrainPopulated'] = nbt.TAG_Byte(1)
    nbtsections = nbtchunk['Sections']
    boolsects = nptower != ''        # if any of y sections contains something
    assert boolsects.ndim == 1

    if len(nbtsections) == 0:
        nbtsections = nbt.TAG_List(nbt.TAG_Compound)
        nbtchunk['Sections'] = nbtsections
        sections = {}
    else:
        sections = {v['Y'].value: v for v in nbtsections}

    for (y, ), cond in np.ndenumerate(boolsects):
        if cond:
            if overlay and sections.get(y):
                sections[y] = overlay_section(y, sections[y], nptower[y], withlight, **ovkwargs)
                if withlight: light_popul = 1
            else:
                sections[y] = make_section(y, nptower[y])

    nbtsections.tags = list(sections.values())
    nbtchunk['LightPopulated'] = nbt.TAG_Byte(light_popul)
    return nbtroot

def mc_get_chunk(mcworld, x, z):
    rx, cx = divmod(x, 32)
    rz, cz = divmod(z, 32)
    if (rx, rz) in mcworld.regionfiles:
        rr = mcworld.get_region(rx, rz)
        try:
            return rr.get_nbt(cx, cz)
        except region.InconceivedChunk: pass
    return None

#  nbt.world module doesn't have set_nbt, so i made one so that if the region file does not exist create new blank data
#  TODO: create a fork for the nbt module and put this in
def mc_save_chunk(mcworld, x, z, nbt):
    rx, cx = divmod(x, 32)
    rz, cz = divmod(z, 32)
    if (rx, rz) in mcworld.regionfiles:
        rr = mcworld.get_region(rx, rz)
        rr.write_chunk(cx, cz, nbt)
    else:
        rfname = os.path.join(mcworld.worldfolder, "region", "r.{:d}.{:d}.{:s}".format(rx, rz, mcworld.extension))
        rr = region.RegionFile(fileobj=open(rfname, 'w+b'))
        rr.loc = region.Location(x=rx, z=rz)  # is this optional?
        rr._closefile = True  # private, needs to be set manually
        rr.write_chunk(cx, cz, nbt)
        mcworld.regions[(rx, rz)] = rr
        mcworld.regionfiles[(rx, rz)] = rfname

def save_to_mc_world(name, npmap, trim=None, **params):
    mcldb = os.path.join(name, 'level.dat')
    if not os.path.exists(name):
        raise FileNotFoundError("MC World Folder \"{}\" does not exist".format(name))
    elif not os.path.exists(mcldb):
        raise Exception("Folder \"{}\" is not MC World".format(name))

    mcworld = world.WorldFolder(name)
    nbtldb = nbt.NBTFile(mcldb)
    nbtdat = nbtldb['Data']
    if nbtdat['DataVersion'].value != data_version:
        raise IncompatibleWorldVersion(nbtdat['DataVersion'].value)

    npmap = npmap.transpose(1, 0, 2)   # change into chunk towers
    if trim is None:
        ndrange, npmap = trim_ndarray(npmap)
        print_ndrange(ndrange, ('Y','X','Z'))
    else:
        npmap = npmap[trim]
    assert npmap.shape[0] <= 16      #  y <= 16

    booltowers = (npmap != '').any(axis=0)  # if any of (x, z) chunk towers contains something
    pwnx, pwnz = booltowers.shape

    for (pwx, pwz), cond in np.ndenumerate(booltowers):
        if cond:
            pwhx, pwhz = offsethalf(pwx, pwnx), offsethalf(pwz, pwnz)
            nbtroot = mc_get_chunk(mcworld, pwhx, pwhz)
            if nbtroot is None:
                nbtroot = make_mc_chunk(pwhx, pwhz, npmap[:, pwx, pwz])
            else:
                nbtroot = put_pw5_to_mc_chunk(nbtroot, npmap[:, pwx, pwz], **params)
            mc_save_chunk(mcworld, pwhx, pwhz, nbtroot)

    nbtdat['LastPlayed'].value = int(time.time()*1000)
    nbtldb.write_file()

#
#  MC World Reading Functions
#

def get_nbt_section(nbtsect):
    bb = np.array(nbtsect['Blocks'].value)
    bd = np.array(nbtsect['Data'].value)
    bd = np.asarray((bd & 0xf, bd >> 4)).T.ravel()
    assert bb.size == 4096 and bd.size == 4096

    mcblocks = np.stack((bb, bd)).T
    convblocks = reverse_index(mcblocks).reshape(16,16,16)
    convblocks = convblocks.transpose(1, 2, 0)
    encstr = encode_chunk(convblocks).replace('\x00','\ufffe')
    return encstr

def get_nbt_chunk(nbtroot, booltower):
    assert booltower.ndim == 1
    if nbtroot['DataVersion'].value != data_version:
        raise IncompatibleWorldVersion(nbtroot['DataVersion'].value)

    nbtchunk = nbtroot['Level']
    nbtsections = nbtchunk['Sections']
    if len(nbtsections) == 0:
        sections = {}
    else:
        sections = {v['Y'].value: v for v in nbtsections}

    pw5sects = []
    for (y, ), cond in np.ndenumerate(booltower):
        if cond:
            if sections.get(y):
                pw5sects.append(get_nbt_section(sections[y]))
            else:
                pw5sects.append('\u1000\ufffe')
        else:
            pw5sects.append('')

    return pw5sects

def load_mc_world(name, dsize, drange, heatmap):
    np.set_printoptions(threshold=np.inf, linewidth=np.inf)   # TODO: for debug print only, remove this
    assert dsize == heatmap.shape
    trim_heatmap = heatmap[tuple(slice(a[0], -a[1]) for a in drange)].transpose(1, 2, 0)

    mcldb = os.path.join(name, 'level.dat')
    if not os.path.exists(name):
        raise FileNotFoundError("MC World Folder \"{}\" does not exist".format(name))
    elif not os.path.exists(mcldb):
        raise Exception("Folder \"{}\" is not MC World".format(name))

    mcworld = world.WorldFolder(name)
    nbtldb = nbt.NBTFile(mcldb)
    nbtdat = nbtldb['Data']
    if nbtdat['DataVersion'].value != data_version:
        raise IncompatibleWorldVersion(nbtdat['DataVersion'].value)

    assert trim_heatmap.shape[0] <= 16      #  y <= 16
    booltowers = trim_heatmap.any(axis=0)
    emptytower = ['']*trim_heatmap.shape[0]
    pwnx, pwnz = booltowers.shape

    cc = []
    for (pwz, pwx), cond in np.ndenumerate(booltowers):
        if cond:
            pwhx, pwhz = offsethalf(pwx, pwnx), offsethalf(pwz, pwnz)
            nbtroot = mc_get_chunk(mcworld, pwhx, pwhz)
            if nbtroot is None:
                print('Chunk ({:d}, {:d}) not found'.format(pwhx, pwhz))
                cc.append(emptytower)
            else:
                cc.append(get_nbt_chunk(nbtroot, trim_heatmap[:, pwx, pwz]))
        else:
            cc.append(emptytower)

    cc = np.array(cc)
    cc = cc.reshape(pwnz, pwnx, trim_heatmap.shape[0])
    cc = cc.transpose(0, 2, 1)
    cc = untrim_ndarray(cc, drange, '')
    assert cc.shape == dsize
    return cc

def save_to_pw5_map(name, npmap):
    if not os.path.isdir(name):
        os.mkdir(name)
    lx = np.split(npmap, 4, 0)
    nx = len(lx)
    for x, rrx in enumerate(lx):
        lz = np.split(rrx, 4, 2)
        nz = len(lz)
        for z, rrz in enumerate(lz):
            ly = np.split(rrz, 2, 1)
            ny = len(ly)
            for y, rry in enumerate(ly):
                hx, hy, hz=offsethalf(x, nx), offsethalf(y, ny), offsethalf(z, nz)
                reg = os.path.join(name, '{},{},{},.region'.format(hz, hy, hx))
                if os.path.exists(reg):
                    os.unlink(reg)
                if (rry!='').any():
                    rry = rry[invert_nd(hx, hy, hz)].ravel()
                    with open(reg, 'w', encoding='utf8', newline='') as f:
                        f.write('\uffff'.join(rry).replace('\ufffe','\x00'))
