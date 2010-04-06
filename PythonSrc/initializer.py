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

import oracle_en
import oracle_matfiles



def initialize(nCodes,pSize=8,usebars=2,keyInv=True,songKeyInv=False,
               positive=True,do_resample=True,nThreads=4,oracle='EN',
               artistsdb='',matdir=''):
    """
    Function to initialize a codebook, return the codebook as numpy array.
    """

    # creates a dictionary with all parameters
    params = {'nCodes':nCodes, 'pSize':pSize,
              'usebars':usebars, 'keyInv':keyInv,
              'songKeyInv':songKeyInv, 'positive':positive,
              'do_resample':do_resample, 'nThreads':nThreads,
              'oracle':oracle, 'artistsdb':artistsdb,
              'matdir':matdir}


    # create codebook
    assert nCodes > 0,'nCodes inferior to 1? come on... codebook size!'
    codebook = np.zeros([nCodes,12*pSize])
    cbidx = 0 # which code are we initializing


    # create oracle
    if oracle == 'EN':
        oracle = oracle_en.OracleEN(params,artistsdb)
    elif oracle == 'MAT':
        oracle = oracle_matfiles.OracleMatfiles(params,matdir)
    else:
        assert False, 'wrong oracle codename: %s.'%oracle

    # find the N codes
    while True:
        # done?
        if cbidx >= codebook.shape[0]:
            break
        # get features from next track / song
        feats = oracle.next_track()
        if feats == None:
            continue
        # remove empty patterns
        feats = feats[np.nonzero(np.sum(feats,axis=1))]
        # not enough features? don't take a chance
        if feats.shape[0] < 20:
            continue
        # select random feature, add it
        rand_feat_idx = np.random.randint(feats.shape[0])
        codebook[cbidx,:] = feats[rand_feat_idx,:]
        cbidx += 1
        # verbose
        if cbidx == np.round(nCodes * .25): print '25% done'
        elif cbidx == np.round(nCodes * .50): print '50% done'
        elif cbidx == np.round(nCodes * .75): print '75% done'

    # done, return codebook
    return codebook



def die_with_usage():
    """
    HELP MENU
    """
    print 'trainer.py by T. Bertin-Maheux (2010) Columbia University'
    print 'tb2332@columbia.edu'
    print ''
    print 'Initialize a model with EchoNest data or saved data'
    print 'usage:'
    print '   python -O initializer.py [flags] <nCodes> <mat filename>'
    print 'PARAMS'
    print ' <nCodes>          codebook size, number of codewords'
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
    pSize = 8
    usebars = 2
    keyInv = True
    songKeyInv = False
    positive = True
    do_resample = True
    nThreads = 4
    oracle = 'EN'
    artistsdb = ''
    matdir = ''
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
        elif sys.argv[1] == '-nThreads':
            nThreads = int(sys.argv[2])
            sys.argv.pop(1)
            print 'nThreads =', nThreads
        elif sys.argv[1] == '-artistsdb':
            artistsdb = sys.argv[2]
            sys.argv.pop(1)
            print 'artistsdb =', artistsdb
        elif sys.argv[1] == '-oraclemat':
            oracle = 'MAT'
            matdir = sys.argv[2]
            sys.argv.pop(1)
            print 'oracle =',oracle,', matfiles dir =',matdir
        else:
            break
        sys.argv.pop(1)
    

    # params
    nCodes = int(sys.argv[1])
    filename = os.path.abspath(sys.argv[2])

    # launch initialization
    codebook = initialize(nCodes,pSize=pSize,usebars=usebars,keyInv=keyInv,
                          songKeyInv=songKeyInv,positive=positive,
                          do_resample=do_resample,nThreads=nThreads,
                          oracle=oracle,artistsdb=artistsdb,matdir=matdir)

    # save codebook
    scipy.io.savemat(filename,{'codebook':codebook})
