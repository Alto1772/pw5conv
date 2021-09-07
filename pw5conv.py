import nbt

defblocks = [
    (0,   0), # 0:  None (as Air)
    (2,   0), # 1:  Grass Block
    (3,   0), # 2:  Dirt
    (98,  0), # 3:  Stone Bricks
    (24,  0), # 4:  Sand (as Sandstone, due to Sand being a falling block)
    (35,  0), # 5:  White Wool
    (206, 0), # 6:  Sandstone brick??? (as End Brick)
    (25,  0), # 7:  Oak Wood Plank with Steel Casing??? (as Note Block)
    (20,  0), # 8:  Glass
    (18,  6), # 9:  Birch Leaves
    (98,  1), # 10: Mossy Stone
    (98,  1), # 11: Mossy Stone Bricks
    (22,  0), # 12: Blue Tiles??? (as Lapis Lazuli Block)
    (47,  0), # 13: Bookshelf
    (5,   0), # 14: Oak Wood Plank
    (98,  3), # 15: Chiseled Stone Bricks???
    (45,  0), # 16: Bricks
    (17,  0), # 17: Oak Log
    (88,  0), # 18: ??? (i don't know what kind of block this is, assume this as Soul Sand)
    (35,  5), # 19: Lime Wool
    (35,  2), # 20: Magenta Wool
    (35,  3), # 21: Light Blue Wool
    (35,  1), # 22: Orange Wool
    (35, 13), # 23: Green Wool
    (35,  6), # 24: Pink Wool
    (35,  7), # 25: Gray Wool
    (35, 10), # 26: Purple Wool
    (35,  9), # 27: Cyan Wool
    (35, 14), # 28: Red Wool
    (35, 12), # 29: Brown Wool
    (35,  8), # 30: Light Gray Wool
    (35, 11), # 31: Blue Wool
    (42,  0), # 32: Iron Block
    (35, 15), # 33: Black Wool
    (35,  4), # 34: Yellow Wool
    (112, 0), # 35: Nether Brick
    (101, 0), # 36: Iron Bars Block (as a non-full block)
    (174, 0), # 37: Ice Block (as Packed Ice)
]

ten_range = lambda: range(10)
inverted_ten_range = lambda limit=31: range(limit, limit-10, -1)

coord_range = lambda inverted=False: inverted_ten_range() if inverted else ten_range()
coord_negate = lambda c, inverted=False, limit=31: limit - c if inverted else c

def rledecchunk(chunk):
    ret = bytearray()
    for n, i in zip(chunk[::2], chunk[1::2]):
         for _ in range(ord(n)):
             ret.append(ord(i))
    return ret

def rleencchunk(chunk):
    ret = []
    if len(chunk) == 0:
        return ''

    count = 1
    for i, ichr in enumerate(chunk):
        if i == 0:
            continue
        elif ichr == chunk[i - 1]:
            count += 1
        else:
            ret.append(chr(count) + chunk[i - 1])
            count = 1
    ret.append(chr(count) + chunk[len(chunk) - 1])

    return ''.join(ret)

def mksection(y, blocks, datas):
    assert len(blocks) == 4096
    assert len(datas) == 4096

    sect = nbt.nbt.TAG_Compound()
    bs = nbt.nbt.TAG_Byte_Array()
    bs.value = [255 for _ in range(2048)]
    bl = nbt.nbt.TAG_Byte_Array()
    bl.value = [0 for _ in range(2048)]
    bb = nbt.nbt.TAG_Byte_Array()
    bb.value = blocks
    bd = nbt.nbt.TAG_Byte_Array()
    bd.value = [(datas[i+1] << 4) | datas[i] for i in range(0, 4096, 2)]
    sect['BlockLight'] = bl
    sect['SkyLight'] = bs
    sect['Blocks'] = bb
    sect['Data'] = bd
    sect['Y'] = nbt.nbt.TAG_Byte(y)

    return sect

def mkblanksection(y):
    return mksection(y, [0 for _ in range(4096)], [0 for _ in range(4096)])

def pw5bb2mclcc(bb0, bb1, x_invert=False, z_invert=False):
    _pw5lcc = {}
    for x in coord_range(x_invert):
        for y in range(9):
            for z in coord_range(z_invert):
                # Note: X and Z coord in PW5 is inverted to MC
                if y < 4:
                    _pw5cc = bb0[coord_negate(x, x_invert) * 100 + y * 10 + coord_negate(z, z_invert)]
                    if _pw5cc:
                        _temp = rledecchunk(_pw5cc)
                        _temp = [[[_temp[x*256 + y*16 + z] for z in range(16)] for y in range(16)] for x in range(16)]
                        _pw5lcc[x, 3 - y, z] = _temp
                else:
                    _pw5cc = bb1[coord_negate(x, x_invert) * 100 + (y - 4) * 10 + coord_negate(z, z_invert)]
                    if _pw5cc:
                        _temp = rledecchunk(_pw5cc)
                        _temp = [[[_temp[x*256 + y*16 + z] for z in range(16)] for y in range(16)] for x in range(16)]
                        _pw5lcc[x, y, z] = _temp

    _mclcc = {}
    for z in coord_range(z_invert):
        for x in coord_range(x_invert):
            _sections = {}
            for y in range(9):
                _temp = _pw5lcc.get((x, y, z))
                if _temp:
                    _blocks = [defblocks[_temp[bx][by][bz]][0] for by in range(16) for bz in range(16) for bx in range(16)]
                    _datas = [defblocks[_temp[bx][by][bz]][1] for by in range(16) for bz in range(16) for bx in range(16)]
                    _sections[y] = [_blocks, _datas]
            _mclcc[x, z] = _sections

    mclcc = {}
    for a in _mclcc:
        _sections = nbt.nbt.TAG_List(nbt.nbt.TAG_Compound)
        for y in range(9):
            _sect = _mclcc[a].get(y)
            if _sect:
                _sections.append(mksection(y, _sect[0], _sect[1]))
            else:
                _sections.append(mkblanksection(y))
        mclcc[a] = _sections

    return mclcc

def extractsection(sect):
    assert len(sect['Blocks']) == 4096
    assert len(sect['Data']) == 2048
    bb = sect['Blocks']
    bd = [b for a in sect['Data'] for b in (a&0xf,a>>4)]

    return list(zip(bb, bd))

def mcb2pw5b(block, data):
    try:
        return defblocks.index((block, data))
    except ValueError:
        if block == 18:
            # FIXME: consider leaf variants as one
            return 9
        else:
            # Air is the default
            return 0

def mkpw5region(pw5lcc, y_above=True):
    pw5bb = [''] * 1000

    for z in range(10):
        for y in range(5 if y_above else 4):
            for x in range(10):
                pw5bb[z * 100 + y * 10 + x] = pw5lcc[x, y, z]

    return pw5bb

def mclcc2pw5bb(mclcc, x_invert=False, z_invert=False):
    _mclcc = {}
    for a in mclcc:
        _sections = [extractsection(y) for y in sorted(mclcc[a], key=lambda x: x['Y'].value)]
        _mclcc[a] = _sections

    _pw5lcc = {}
    for x, z in _mclcc:
        _sections = _mclcc[x, z]
        for y in range(9):
            _pw5lcc[x, y, z] = [mcb2pw5b(*_sections[y][by*256 + bz*16 + bx]) for bx in range(16) for by in range(16) for bz in range(16)]

    _pw5bb0 = {}
    _pw5bb1 = {}
    pw5bb0 = []
    pw5bb1 = []
    for x, y, z in _pw5lcc:
        if y < 4:
            _pw5bb0[coord_negate(z, z_invert), 3 - y, coord_negate(x, x_invert)] = rleencchunk(''.join(chr(a) for a in _pw5lcc[x, y, z]))
        else:
            _pw5bb1[coord_negate(z, z_invert), y - 4, coord_negate(x, x_invert)] = rleencchunk(''.join(chr(a) for a in _pw5lcc[x, y, z]))

    pw5bb0 = mkpw5region(_pw5bb0, False)
    pw5bb1 = mkpw5region(_pw5bb1, True)

    return pw5bb0, pw5bb1

def write_pw5_region(pw5mapname, x, z, pw5b0b, pw5b1b):
    with open(pw5mapname + '/{:d},-1,{:d},.region'.format(z, x),'w',newline='') as f:
        f.write('\uffff'.join(pw5b0b))

    with open(pw5mapname + '/{:d},0,{:d},.region'.format(z, x),'w',newline='') as f:
        f.write('\uffff'.join(pw5b1b))

def get_pw5_region(pw5mapname, x, z):
    with open(pw5mapname + '/{:d},-1,{:d},.region'.format(z, x),'r',newline='') as f:
        pw5b0 = f.read()
    pw5b0b = pw5b0.split('\uffff')

    with open(pw5mapname + '/{:d},0,{:d},.region'.format(z, x),'r',newline='') as f:
        pw5b1 = f.read()
    pw5b1b = pw5b1.split('\uffff')

    return pw5b0b, pw5b1b

def get_mc_region(mcmapname, x, z):
    wf = nbt.world.WorldFolder(mcmapname)
    rr = wf.get_region(x, z)

    lcc = {}
    for zz in coord_range(z < 0):
        for xx in coord_range(x < 0):
            #print(xx, zz)
            lcc[xx, zz] = rr.get_nbt(xx, zz)

    return rr, lcc
