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




def train(expdir,savedmodel='',nThreads=4):
    """
    Performs training
    Grab track data from oracle
    Pass them to model that updates itself

    INPUT
      expdir        - experiment directory, where to save experiments
      savedmodel    - previously saved model directory, to restart it
      nThreads      - number of threads for the oracle, default=4
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
            pass




    except:
        print "ERROR:", sys.exc_info()[0]
        # save
        print 'saving to: '

        #quit
        return





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
