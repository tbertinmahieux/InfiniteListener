"""
Function to perform an online experiment, i.e. train a model by
gathering online music analysis data.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import time
import copy
import pickle
import numpy as np
import scipy.io

import oracle_en
import features



def train(expdir,pSize=8,usebars=2,keyInv=True,songKeyInv=False,
          positive=True,do_resample=True
          lrate=1e-5,savedmodel='',nThreads=4):
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

    # creates a dctionary with all parameters
    params = {'expdir':expdir,'pSize':pSize8,'usebars':usebars,
              'keyInv':keyInv,'songKeyInv':songKeyInv,
              'positive':positive,'do_resample':do_resample,
              'lrate':lrate,'savedmodel':savedmodel,
              'nThreads':nThreads}

    # creates the experiment folder
    if not os.path.isdir(expdir):
        print 'creating experiment directory:',expdir
        os.mkdir(expdir)

    # create the StatLog object
    statlog = StatLog()

    # start from saved model
    if savedmodel != '':
        raise NotImplementedError
    # intialize new model
    else:
        raise NotImplementedError

    # create oracle
    oracle = OracleEN(params)

    # starttime
    starttime = time.time()

    # main algorithm
    try:
        while True:
            # get features from the oracle
            feats = oracle.next_track()
            if feats == None:
                continue
            # stats
            statlog.patternsSeen(feats.shape[0])
            # update model
            model.update(feats,lrate=lrate)

    except:
        print "ERROR:", sys.exc_info()[0]
        # save
        savedir = save_experiment(model,starttime,statlog,params,crash=True)
        print 'saving to: ',savedir
        #quit
        return




class StatLog():
    """
    Simple class to keep track of different stats of the trainer
    """
    def __init__(self):
        """ Creates counters """
        self.nTrackUsed = 0
        self.nPatternUsed = 0
    def trackSeen(self):
        self.nTrackUsed += 1
    def patternsSeen(self,n):
        self.nPatternUsed += n


def get_savedir_name(expdir):
    """
    Creates a directory name based on time, in the expdir directory.
    Gives something like:
       'expdir/exp_2010_03_27_AT_22h50m03s'
    """
    foldername = os.path.join(expdir,'exp_')
    foldername += time.strftime("%Y_%m_%d_AT_%Hh%Mm%Ss", time.localtime())
    return foldername


def save_experiment(model,starttime,statlog,params,crash=False):
    """
    Saves everything, either by routine or because of a crash
    Return directory name
    """
    savedir = get_savedir_name(expdir):
    os.mkdir(savedir)
    # save codebook as matfile
    fname = os.path.join(savedir,'codebook.mat'))
    scipy.io.savemat(fname,{'codebook':model._codebook})
    # save model
    f = open(os.path.join(savedir,'model.p')),'w')
    picle.dump(model,f)
    f.close()
    # save stats
    f = open(os.path.join(savedir,'stats.p')),'w')
    picle.dump(statlog,f)
    f.close()
    # save params
    f = open(os.path.join(savedir,'params.p')),'w')
    picle.dump(params,f)
    f.close()
    # save starttime
    fname = 'starttime_'
    fname += time.strftime("%Y_%m_%d_AT_%Hh%Mm%Ss", time.localtime(starttime))
    fname += '.txt'
    f = open(os.path.join(savedir,fname),'w')
    f.close()
    # done, return name of the directory
    return savedir




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
