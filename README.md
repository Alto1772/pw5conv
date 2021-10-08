# pw5conv (Faster Version)
Converts Pixel Warfare 5 Maps to Minecraft Java Edition World by overwriting existing chunks. Only 1.12.2 version works right now.

## Dependencies
- Python 3.9
- numpy
- nbt

## Commands
```
./pw52mc.py <pw5mapdir> <mcworlddir>
 - converts PW5 Map to MC World

./mc2pw5.py <mcworlddir> <pw5mapdir|hmapbin> [pw5mapdir]
 - converts MC World to PW5 Map

./gen-heatmap_bin.py <pw5mapdir> > hmap.bin
 - generates pw5 heatmap of non-empty chunks

./gen-heatmap_schem.py <pw5mapdir> > hmap.schematic
 - generates pw5 heatmap as a minecraft schematic file

./gen-heatmap_mcworld.py <pw5mapdir> <mcworlddir>
 - generates pw5 heatmap and writes onto the minecraft world for making maps using minecraft and export using mc2pw5.py
```

**Note**: It doesn't include stretched blocks yet.
