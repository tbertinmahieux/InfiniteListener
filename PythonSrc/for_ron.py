"""
Similar code from the BostonHackDay project

Simple code that Ron can launch on the NYU cluster.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import glob
import multiprocessing

import numpy as np
import scipy as sp
import scipy.io

import initializer
import trainer


def do_experiment(experiment_dir,beats=0,bars=0,nCodes=0,nIter=1e7,
                  partialbar=0,keyInv=False,songKeyInv=True,lrate=1e-3,
                  mat_dir=''):
    """
    Main function to run an experiment, train a model and save to dir.
    """

    # check if saved model exists
    alldirs = glob.glob(os.path.join(experiment_dir,'*'))
    alldirs = filter(lambda x: os.path.isdir(x), alldirs)
    alldirs = filter(lambda x: os.path.split(x)[-1][:4] == 'exp_',alldirs)
    continue_training = len(alldirs) > 0

    # continue from saved model
    if continue_training:
        # find most recent saved mdoel, and continue!
        savedmodel = np.sort(alldirs)[-1]
        trainer.train(savedmodel)

    # no prior saved model
    if not continue_training:
        #initialize and save codebook
        codebook = initializer.initialize(nCodes, pSize=beats, usebars=bars,
                                          keyInv=keyInv, songKeyInv=songKeyInv,
                                          positive=True, do_resample=True,
                                          partialbar=partialbar, nThreads=4,
                                          oracle='MAT', artistsdb='',
                                          matdir=mat_dir)
        codebook_fname = os.path.join(experiment_dir,'codebook.mat')
        scipy.io.savemat(codebook_fname,{'codebook':codebook})
        # train (from scratch)
        trainer.train(codebook_fname, expdir='', pSize=beats, usebars=bars,
                      keyInv=keyinv, songKeyInv=songKeyInv, positive=True,
                      do_resample=True, partialbar=partialbar, lrate=lrate,
                      nThreads=4, oracle='MAT', artistsdb='',
                      matdir=mat_dir, nIterations=nIter, useModel='VQ')



def do_experiment_wrapper(args,argsdict):
    """ launch experiments given params, either as list or dict """
    return do_experiment(*args,**argsdict)



def die_with_usage():
    """
    HELP MENU
    """
    print 'code to launch experiments on NYU cluster'
    sys.exit(0)



if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()
