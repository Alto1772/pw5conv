#!/usr/bin/env python3
import pw5conv as pconv

worldname = "pw5 map convert"
#pw5mapname = "Forest_City"

def main(pw5mapname):
    for x in (0, -1):
        for z in (0, -1):
            print("Overwriting {}/region/r.{}.{}.mca...".format(worldname, x, z))
            rr, lcc = pconv.get_mc_region(worldname, x, z)
            pw5b0, pw5b1 = pconv.get_pw5_region(pw5mapname, x, z)

            mclcc = pconv.pw5bb2mclcc(pw5b0, pw5b1, x < 0, z < 0)
            for a in lcc:
                lcc[a]['Level']['LightPopulated'].value = 0
                lcc[a]['Level']['Sections'] = mclcc[a]
                rr.write_chunk(a[0], a[1], lcc[a])

            rr.close()

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
