"""
Code to test a model trained by online learning.
Look at all the saved folders, and apply every save to the
given testset (load into memory).

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import glob
import time
import copy
import numpy as np

import model as MODEL
import oracle_matfiles as ORACLE


def die_with_usage():
    """
    HELP MENU
    """
    print 'Test a set of saved model with a given dataset.'
    print 'Usage:'
    print 'python test_trained_models.py [FLAGS] <savedmodel> <matfilesdir> <output.txt>'
    print 'PARAMS:'
    print '  <savedmodel>   directory where an online model is saved'
    print '  <matfilesdir>  '
    print '  <output.txt>   '
    print 'FLAGS:'
    print '  -testone       test only the given saved model'
    print ''
    print 'T. Bertin-Mahieux (2010) Columbia University'
    print 'tb2332@columbia.edu'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 4:
        die_with_usage()

    # flags
    testone = False
    while True:
        if sys.argv[1] == '-testone':
            testone = True
        else:
            break
        sys.argv.pop(1)

    # params
    savedmodel = sys.argv[1]
    matfilesdir = sys.argv[2]
    output = sys.argv[3]

    # gather in a set all models to try
    # also gather the number of iterations associated with each model


    # load data into memory


    # predict on every model


    # write everything to file
