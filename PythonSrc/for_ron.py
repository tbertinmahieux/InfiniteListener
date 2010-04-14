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



featsDir = os.path.expanduser('~/projects/ismir10-patterns/beatFeats')
#testFeatsDir = os.path.expanduser('~/projects/ismir10-patterns/uspop_mat')
#outputDir = os.path.expanduser('~/projects/ismir10-patterns/experiments')
outputDir = ''
assert outputDir != '','SET OUTPUT DIR TO SOMETHING!!!!'


def do_experiment(experiment_dir,beats=0,bars=0,nCodes=0,nIter=1e7,
                  partialbar=0,keyInv=False,songKeyInv=True,lrate=1e-3,
                  mat_dir=''):
    """
    Main function to run an experiment, train a model and save to dir.
    """

    # check for 'done' file
    if os.path.exists(os.path.join(experiment_dir,'DONE.txt')):
        return

    # if experiment folder does not exist, create it
    if not os.path.exists(experiment_dir):
        print 'creating experiment dir:',experiment_dir
        os.mkdir(experiment_dir)

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
        print 'after initialization, codebook saved to:',codebook_fname

        # train (from scratch)
        trainer.train(codebook_fname, expdir=experiment_dir, pSize=beats,
                      usebars=bars, keyInv=keyInv, songKeyInv=songKeyInv,
                      positive=True, do_resample=True, partialbar=partialbar,
                      lrate=lrate, nThreads=4, oracle='MAT', artistsdb='',
                      matdir=mat_dir, nIterations=nIter, useModel='VQ')

    # write done file
    f = open(os.path.join(experiment_dir,'DONE.txt'),'w')
    f.write('experiment appear to be done\n')
    f.close()


def do_experiment_wrapper(args):
    """
    launch experiments given params
    Receives a pair: args and argsdict!
    """
    args,argsdict = args
    return do_experiment(*args,**argsdict)



experiment_args = []
# experiment set 1
args1 = [os.path.join(outputDir,'set1exp1')]
argsd1 = {'mat_dir':featsDir,'beats':4,'bars':1,'nCodes':100}
experiment_args.append( [(args1,argsd1),] )



def die_with_usage():
    """
    HELP MENU
    """
    print 'code to launch experiments on NYU cluster'
    print 'usage:'
    print '  python for_ron.py -go <num proc> <exp set> <sub exp (opt)>'
    sys.exit(0)



if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 4:
        die_with_usage()

    # setup
    nprocesses = int(sys.argv[2])
    pool = multiprocessing.Pool(processes=nprocesses)
    # Python indexes from 0, the argument indexes from 1.
    experiment_set_number = int(sys.argv[3]) - 1
    args = experiment_args[experiment_set_number]
    try:
        args = [args[int(sys.argv[4]) - 1]] # subset exp? nice ;)
    except IndexError:
        pass

    # launch experiments
    pool.map(do_experiment_wrapper, args)
