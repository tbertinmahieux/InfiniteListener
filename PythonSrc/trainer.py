"""

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import time
import copy
import numpy as np


import oracle_en
import features



def train(expdir,pSize=8,usebars=2,keyInv=True,lrate=1e-5,
          savedmodel='',nThreads=4):
    """
    Performs training
    Grab track data from oracle
    Pass them to model that updates itself

    INPUT
      expdir        - experiment directory, where to save experiments
      pSize         - pattern size
      usebars       - how many bars per pattern
      keyInv        - perform 'key invariance' on patterns
      lrate         - learning rate
      savedmodel    - previously saved model directory, to restart it
      nThreads      - number of threads for the oracle, default=4

    Saves everything when done.
    """

    # start from saved model
    if savedmodel != '':
        raise NotImplementedError
    # intialize new model
    else:
        raise NotImplementedError

    # create oracle
    oracle = OracleEN(nThreads=nThreads)

    # starttime
    starttime = time.time()

    
    # main algorithm
    try:
        while True:
            # get data, dictionary of EchoNest analysis
            data = oracle.nest_track()
            # get features
            feats = features.get_features(data,pSize=pSize,
                                          usebars=usebars,keyInv=keyInv)
            if feats == None:
                continue
            # update model
            model.update(feats,lrate=lrate)

    except:
        print "ERROR:", sys.exc_info()[0]
        # save
        print 'saving to: '

        #quit
        return



def save_experiment(crash=False):
    """
    Saves everything, either by routine or because of a crash
    """
    raise NotImplementedError




def die_with_usage():
    """
    HELP MENU
    """
    print 'Train a model with EchoNest data'
    print 'usage:'
    print '   python trainer.py [flags] <expdir>'
    print '   python -O trainer.py [flags] <expdir>'
    print 'INPUT'
    print ' <expdir>    experiment directory, where to save experiments'
    sys.exit(0)



if __name__ == '__main__':

    if len(sys.argv) < 2:
        die_with_usage()

    # launch training
    train()
