"""
Code to initialize a codebook, usually by selecting random samples
from an oracle.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import time
import copy
import numpy as np
import scipy as sp
import scipy.io















def die_with_usage():
    """
    HELP MENU
    """
    print 'trainer.py by T. Bertin-Maheux (2010) Columbia University'
    print 'tb2332@columbia.edu'
    print ''
    print 'Initialize a model with EchoNest data or saved data'
    print 'usage:'
    print '   python -O initializer.py [flags] <mat filename>'
    print 'PARAMS'
    print ' <mat filename>    where to save the codebook (matfile)'
    print 'FLAGS'
    print ' -pSize n          final pattern size is 12 x n'
    print ' -usebars n        n number of bars per pattern, or 0'
    print ' -noKeyInv         do not perform key inveriance on patterns'
    print ' -songKeyInv       perform key invariance on song level'
    print ' -notpositive      do not replace negative values by zero'
    print ' -dont_resample    pad or crop instead'
    print ' -nThreads n       launch n threads for the EchoNest oracle'
    print ' -artistsdb db     SQLlite database containing artist names'
    print '                   used by EchoNest oracle'
    print ' -oraclemat d      matfiles oracle, d: matfiles dir'
    print ''
    print 'typical command to initialize from codebook:'
    print '  python -O initializer.py -pSize 8 -usebars 2 -artistsdb artists28March.db ~/experiment_dir/newexp/codebook.mat'
    sys.exit(0)







if __name__ == '__main__' :


    # help menu
    if len(sys.argv) < 3:
        die_with_usage()


    # flags


    
