#!/usr/bin/env python3
import pw5conv as pconv

def main(worldname, pw5mapname):
    for x in (0, -1):
        for z in (0, -1):
            print("Overwriting {}/{},*,{},.region".format(pw5mapname, z, x))
            rr, lcc = pconv.get_mc_region(worldname, x, z)
            mclcc = dict((a, lcc[a]['Level']['Sections']) for a in lcc)

            pconv.write_pw5_region(pw5mapname, x, z, *pconv.mclcc2pw5bb(mclcc, x < 0, z < 0))
            rr.close()

if __name__ == '__main__':
    import sys, os
    if not os.path.isdir(sys.argv[2]):
        print("pw5 map name not found or is not a directory.")
        exit(2)
    main(sys.argv[1], sys.argv[2])
