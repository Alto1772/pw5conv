#!/usr/bin/env python3
import pw5conv
import matplotlib.pyplot as plt
import numpy as np
import sys

pw5hmap = pw5conv.load_pw5_map(sys.argv[1]) != ''
#pw5hmap = pw5hmap.transpose(1, 0, 2)

ax = plt.figure().add_subplot(projection='3d')
ax.voxels(pw5hmap, facecolors='red', edgecolors='k')
plt.show()
