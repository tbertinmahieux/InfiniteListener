"""
Simple code to take a dictionary, encode a song, plot the two,
report distortion.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import numpy as np
import scipy.io
import features as FEATS






def die_with_usage():
    """ HELP MENU """
    print 'python encode_song.py [flags] <song mat> <codebook>'
    print 'FLAGS:'
    print ' -pSize n          final pattern size is 12 x n'
    print ' -usebars n        n number of bars per pattern, or 0'
    print ' -noKeyInv         do not perform key inveriance on patterns'
    print ' -songKeyInv       perform key invariance on song level'
    print ' -notpositive      do not replace negative values by zero'
    print ' -dont_resample    pad or crop instead'
    print ''
    print 'typical command:'
    print 'python encode_song.py -pSize 8 -usebars 2 song.mat codebook.mat'
    sys.exit(0)

    # help menu
    if len(sys.argv) < 3:
        die_with_usage()


    # flags
    pSize = 8
    usebars = 2
    keyInv = True
    songKeyInv = False
    positive = True
    do_resample = True
    while True:
        if sys.argv[1] == '-pSize':
            pSize = int(sys.argv[2])
            sys.argv.pop(1)
            print 'pSize =',pSize
        elif sys.argv[1] == '-usebars':
            usebars = int(sys.argv[2])
            sys.argv.pop(1)
            print 'usebars =',usebars
        elif sys.argv[1] == '-noKeyInv':
            keyInv = False
            print 'keyInv =', keyInv
        elif sys.argv[1] == '-songKeyInv':
            songKeyInv = True
            print 'songKeyInv', songKeyInv
        elif sys.argv[1] == '-notpositive':
            positive = False
            print 'positive =', positive
        elif sys.argv[1] == '-dont_resample':
            do_resample = False
            print 'do_resample =', do_resample
        else:
            break
        sys.argv.pop(1)
