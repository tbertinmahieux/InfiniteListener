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
import traceback
import numpy as np
import scipy as sp
import scipy.io
from collections import deque
# oracle_en uses library unknown to python 2.4 (I know, 2.4, pfff)
try:
    import oracle_en
except:
    'cannot import oracle_en, are you on hog? can only use oracle_matfiles'

import oracle_matfiles
import features
import model as MODEL
import analyze_saved_model as ANALYZE




def train(savedmodel, expdir='', pSize=8, usebars=2, keyInv=True,
          songKeyInv=False, positive=True, do_resample=True, partialbar=0,
          lrate=1e-5, nThreads=4, oracle='EN', artistsdb='', matdir='',
          nIterations=1e7, useModel='VQ'):
    """
    Performs training
    Grab track data from oracle
    Pass them to model that updates itself

    INPUT
      savedmodel    - previously saved model directory, to restart it
                      or matlab file, to start from a codebook
      expdir        - experiment directory, where to save experiments
      pSize         - pattern size
      usebars       - how many bars per pattern
      keyInv        - perform 'key invariance' on patterns
      positive      - replace negative values by 0
      do_resample   - if false, crop
      partialbar    - actual size, divides pSize
      lrate         - learning rate
      nThreads      - number of threads for the oracle, default=4
      oracle        - EN (EchoNest) or MAT (matfiles)
      artistdb      - SQLlite database containing artist names
      matdir        - matfiles directory, for oracle MAT
      nIterations   - maximum number of iterations
      useModel      - which model to use: 'VQ', 'VQFILT'

    Saves everything when done.
    """

    # create the StatLog object
    statlog = StatLog()

    # count iteration
    #       main   - iteration since this instance started
    #     global   - iteration adding those from the savedmodel
    # last_printed - for verbose purposes
    main_iterations = 0
    global_iterations = 0
    last_printed_iter = 1

    # start from saved model
    if os.path.isdir(savedmodel):
        # load model
        assert os.path.exists(os.path.join(savedmodel,'model.p')),'loading saved model, model.p does not exist? %s' % (os.path.join(savedmodel,'model.p'),)
        f = open(os.path.join(savedmodel,'model.p'),'r')
        model_unp = pickle.Unpickler(f)
        model = model_unp.load()
        f.close()
        # load params, savedmodel will be modified
        assert os.path.exists(os.path.join(savedmodel,'params.p')),'loading saved model, params.p does not exist? %s' % (os.path.join(savedmodel,'params.p'),)
        f = open(os.path.join(savedmodel,'params.p'),'r')
        param_unp = pickle.Unpickler(f)
        oldparams = param_unp.load()
        f.close()
        for k in oldparams.keys():
            if k == 'savedmodel': # special case
                continue
            exec_str = k + ' = oldparams["'+k+'"]'
            exec( exec_str )
            print 'from saved model,',k,'=',eval(k)
        # get global_iterations
        global_iterations,tmp1,tmp2 = ANALYZE.traceback_stats(savedmodel)
        
    # initialized model from codebook
    elif os.path.isfile(savedmodel):
        codebook = load_codebook(savedmodel)
        assert codebook != None,'Could not load codebook in: %s.'%savedmodel
        if useModel == 'VQ':
            model = MODEL.Model(codebook)
        elif useModel == 'VQFILT':
            model = MODEL.ModelFilter(codebook)
        else:
            assert False, 'wrong model codename: %s.'%useModel
        statlog.startFromScratch()
    # problem
    else:
        assert False,'saved model does not exist: %s.'%savedmodel

    # creates a dictionary with all parameters
    params = {'savedmodel':savedmodel, 'expdir':expdir,
              'pSize':pSize, 'usebars':usebars,
              'keyInv':keyInv, 'songKeyInv':songKeyInv,
              'positive':positive, 'do_resample':do_resample,
              'partialbar':partialbar, 'lrate':lrate,
              'nThreads':nThreads, 'oracle':oracle,
              'artistsdb':artistsdb, 'matdir':matdir,
              'nIterations':nIterations, 'useModel':useModel}

    # creates the experiment folder
    if not os.path.isdir(expdir):
        print 'creating experiment directory:',expdir
        os.mkdir(expdir)

    # create oracle
    if oracle == 'EN':
        oracle = oracle_en.OracleEN(params,artistsdb)
    elif oracle == 'MAT':
        oracle = oracle_matfiles.OracleMatfiles(params,matdir)
    else:
        assert False, 'wrong oracle codename: %s.'%oracle

    # starttime and save time
    starttime = time.time()
    last_save = starttime

    # for estimate of distance
    dist_estimate = deque()
    dist_estimate_len = 2000
    
    # main algorithm
    try:
        while True:
            # increment iterations
            main_iterations += 1
            global_iterations += 1
            if main_iterations == int(np.ceil(last_printed_iter * 1.1)):
                print main_iterations,'/',global_iterations,'iterations (local/global), approx. avg dist:',np.average(dist_estimate)
                last_printed_iter = main_iterations
            statlog.iteration()
            if global_iterations > nIterations:
                raise StopIteration
            # get features from the oracle
            feats = oracle.next_track()
            if feats == None:
                continue
            # remove empty pattenrns
            feats = feats[np.nonzero(np.sum(feats,axis=1))]
            if feats.shape[0] == 0:
                continue
            assert not np.isnan(feats).any(),'features have NaN???'
            # stats
            statlog.patternsSeen(feats.shape[0])
            # update model
            avg_dist = model.update(feats,lrate=lrate)
            assert not np.isnan(avg_dist)
            # add to dist_estimate
            dist_estimate.append(avg_dist)
            if len(dist_estimate) > dist_estimate_len:
                dist_estimate.popleft()
            # save
            if should_save(starttime,last_save):
                savedir = save_experiment(expdir,model,starttime,statlog,params)
                last_save = time.time()

    # error, save and quit
    except:
        print ''
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # normal stop or not? normal = StopIteration
        exit_code = 1
        if str(exc_type) == "<type 'exceptions.StopIteration'>":
            exit_code = 0 # normal exit
        print "ERROR:", exc_type
        if str(exc_type) != "<type 'exceptions.KeyboardInterrupt'>":
            print '********** DEBUGGING INFO *******************'
            formatted_lines = traceback.format_exc().splitlines()
            if len(formatted_lines) > 2:
                print formatted_lines[-3]
            if len(formatted_lines) > 1:
                print formatted_lines[-2]
            print formatted_lines[-1]
            print '*********************************************'
            print 'Stoping after', main_iterations - 1, 'iterations.'
        # EN oracle, try to stop/slow down threads
        oracle_en._en_queue_size = 0
        # save
        print 'saving...'
        savedir = save_experiment(expdir,model,starttime,statlog,params,
                                  crash=True)
        print 'saved to: ',savedir
        #quit
        return exit_code




class StatLog:
    """
    Simple class to keep track of different stats of the trainer
    """
    def __init__(self):
        """ Creates counters """
        self.nIterations = 0       # count iterations
        self.nPatternUsed = 0      # count patterns seen
        self.fromscratch = False   # whether we started from a saved model
    def patternsSeen(self,n):
        self.nPatternUsed += n
    def iteration(self):
        self.nIterations += 1
    def startFromScratch(self):
        self.fromscratch = True


def get_savedir_name(expdir):
    """
    Creates a directory name based on time, in the expdir directory.
    Gives something like:
       'expdir/exp_2010_03_27_AT_22h50m03s'
    """
    foldername = os.path.join(expdir,'exp_')
    foldername += time.strftime("%Y_%m_%d_AT_%Hh%Mm%Ss", time.localtime())
    return foldername


def should_save(starttime,last_save):
    """
    A set of simple rules to regularly save the model. Often at the
    beginning, once a day after a week.
    """
    # simple constants
    mins = 60.
    hours = 3600.
    days = 86400.
    # current time
    currtime = time.time()
    # first time after a minute
    if starttime == last_save:
        if (currtime - last_save) / mins > 1:
            return True
        else:
            return False
    # less than one hour, every 10 minutes
    elif (currtime - starttime) / hours < 1:
        if (currtime - last_save) / mins > 10:
            return True
        else:
            return False
    # less than one day, every hour
    elif (currtime - starttime) / days < 1:
        if (currtime - last_save) / hours > 1:
            return True
        else:
            return False
    # less than one week, every 6 hours
    elif (currtime - starttime) / days < 7:
        if (currtime - last_save) / hours > 6:
            return True
        else:
            return False
    # more than a week, once a day
    else:
        if (currtime - last_save) / days > 1:
            return True
        else:
            return False  



def save_experiment(expdir,model,starttime,statlog,params,crash=False):
    """
    Saves everything, either by routine or because of a crash
    Return directory name
    """
    savedir = get_savedir_name(expdir)
    os.mkdir(savedir)
    # save codebook as matfile
    if hasattr(model,'_codebook'):
        fname = os.path.join(savedir,'codebook.mat')
        scipy.io.savemat(fname,{'codebook':model._codebook})
    # save model
    f = open(os.path.join(savedir,'model.p'),'w')
    pickle.dump(model,f)
    f.close()
    # save stats
    f = open(os.path.join(savedir,'stats.p'),'w')
    pickle.dump(statlog,f)
    f.close()
    # save params
    f = open(os.path.join(savedir,'params.p'),'w')
    pickle.dump(params,f)
    f.close()
    # save starttime
    fname = 'starttime_'
    fname += time.strftime("%Y_%m_%d_AT_%Hh%Mm%Ss", time.localtime(starttime))
    fname += '.txt'
    f = open(os.path.join(savedir,fname),'w')
    f.close()
    # crash
    if crash:
        f = open(os.path.join(savedir,'crash.txt'),'w')
        formatted_lines = traceback.format_exc().splitlines()
        formatted_lines = map(lambda x: x+'\n', formatted_lines)
        f.writelines(formatted_lines)
        f.close()
    # done, return name of the directory
    return savedir


def load_codebook(matfile,cbkey='codebook'):
    """
    Load a codebook saved in matfile.
    Assumes codebook s saved under <cbkey>
    Returns codebook, or None if key does not exists
    """
    if not os.path.isfile(matfile):
        return None
    if sys.version_info[1] == 5:
        mat = sp.io.loadmat(matfile)
    else:
        mat = sp.io.loadmat(matfile, struct_as_record=True)
    if not mat.has_key(cbkey):
        return None
    return mat[cbkey]


def die_with_usage():
    """
    HELP MENU
    """
    print 'trainer.py by T. Bertin-Maheux (2010) Columbia University'
    print 'tb2332@columbia.edu'
    print ''
    print 'Train a model with EchoNest data or with saved data.'
    print 'usage:'
    print '   python -O trainer.py [flags] <savedmodel>'
    print 'PARAMS'
    print ' <savedmodel> directory or codebook saved as matfile'
    print 'FLAGS'
    print ' -expdir d         directory to save model, when initializing'
    print ' -pSize n          final pattern size is 12 x n'
    print ' -usebars n        n number of bars per pattern, or 0'
    print ' -noKeyInv         do not perform key inveriance on patterns'
    print ' -songKeyInv       perform key invariance on song level'
    print ' -notpositive      do not replace negative values by zero'
    print ' -dont_resample    pad or crop instead'
    print ' -partialbar n     size of the partial, divides pSize'
    print ' -lrate r          learning rate for the algorithm'
    print ' -nThreads n       launch n threads for the EchoNest oracle'
    print ' -artistsdb db     SQLlite database containing artist names'
    print '                   used by EchoNest oracle'
    print ' -oraclemat d      matfiles oracle, d: matfiles dir'
    print ' -nIters n         maximum number of iterations'
    print ' -useModel N       model name, VQ (default), VQFILT'
    print ' -profile f        use profiler, output to f, limits iters to 100'
    print ''
    print 'typical command to initialize from codebook:'
    print '  python -O trainer.py -pSize 8 -usebars 2 -lrate 1e-5 -artistsdb artists28March.db -expdir ~/experiment_dir codebook.mat'
    print 'typical command to initialize to continue:'
    print '  python -O trainer.py ~/experiment_dir/expBLABLA'
    sys.exit(0)



if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # flags
    expdir = ''
    pSize = 8
    usebars = 2
    keyInv = True
    songKeyInv = False
    positive = True
    do_resample = True
    partialbar = 0
    lrate = 1e-5
    nThreads = 4
    oracle = 'EN'
    artistsdb = ''
    matdir = ''
    nIterations = 1e7
    useModel = 'VQ'
    profile = ''
    while True:
        if sys.argv[1] == '-expdir':
            expdir = os.path.abspath(sys.argv[2])
            sys.argv.pop(1)
            print 'experiment dir =', expdir
        elif sys.argv[1] == '-pSize':
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
        elif sys.argv[1] == '-partialbar':
            partialbar = int(sys.argv[2])
            sys.argv.pop(1)
            print 'partialbar =', partialbar
        elif sys.argv[1] == '-lrate':
            lrate = float(sys.argv[2])
            sys.argv.pop(1)
            print 'lrate =', lrate
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
        elif sys.argv[1] == '-nIters':
            nIterations = int(sys.argv[2])
            sys.argv.pop(1)
            print 'max number of iterations =', nIterations
        elif sys.argv[1] == '-useModel':
            useModel = sys.argv[2]
            sys.argv.pop(1)
            print 'use model =', useModel
        elif sys.argv[1] == '-profile':
            profile = sys.argv[2]
            nIterations = 100
            import pstats
            sys.argv.pop(1)
            print 'use profiler, save result to:',profile
            print 'nIterations =', nIterations
            
        else:
            break
        sys.argv.pop(1)

    # saved model, directory or matfile
    savedmodel = os.path.abspath(sys.argv[1])
    print 'starting from model =', savedmodel


    # launch training
    if profile == '':
        train(savedmodel, expdir=expdir, pSize=pSize,usebars=usebars,
              keyInv=keyInv,songKeyInv=songKeyInv, positive=positive,
              do_resample=do_resample, partialbar=partialbar, lrate=lrate,
              nThreads=nThreads, oracle=oracle, artistsdb=artistsdb,
              matdir=matdir, nIterations=nIterations, useModel=useModel)

    else:
        import cProfile
        cProfile.run(\
            'train(savedmodel, expdir=expdir, pSize=pSize,usebars=usebars, keyInv=keyInv,songKeyInv=songKeyInv, positive=positive, do_resample=do_resample, partialbar=partialbar, lrate=lrate, nThreads=nThreads, oracle=oracle, artistsdb=artistsdb, matdir=matdir, nIterations=nIterations, useModel=useModel)',
            filename=profile)
        # load and print stats
        stats = pstats.Stats(profile)
        print 'top 20 lengthiest functions:'
        stats.strip_dirs().sort_stats('time').print_stats(20)

