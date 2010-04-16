"""
Very similar to test_trained_model
but assumes one of the model used filtering, and go get
the actual number of features seen
"""

import os
import sys
import glob
import time
import copy
import numpy as np

from trainer import StatLog
import model as MODEL
import oracle_matfiles as ORACLE
import analyze_saved_model as ANALYZE




def print_write(s,fname,mode='a'):
    """
    Prints something and write it to file
    """
    print s
    f = open(fname,mode)
    f.write(s)
    f.write('\n')
    f.close()
    

def test_saved_model_folder(dirname,feats,output,filt=False):
    """
    Test a saved model by loading it and applying to features.
    Output is the output file, used with print_write()
    RETURN
      avgerage dist
      nPatterns
      nIters
      totaltime
    """
    print_write('*** MODEL SAVED IN: '+dirname+' ***',output)
    if filt:
        print_write('model uses FILTERING',output)
    # load model
    model = ANALYZE.unpickle(os.path.join(dirname,'model.p'))
    print_write('model loaded',output)
    # find nIters (#tracks), nPatterns, totaltime
    nIters, nPatterns, totalTime = ANALYZE.traceback_stats(dirname)
    if filt:
        nPatterns = model._nPatternUsed
    print_write('nIters (=nTracks): '+str(nIters),output)
    print_write('nPatterns: '+str(nPatterns),output)
    print_write('total time ran: '+str(totalTime),output)
    # predict
    best_code_per_p, dists = model.predicts(feats)
    print_write('prediction done, avg. dist: '+str(np.average(dists)),output)
    # return
    return np.average(dists),nPatterns,nIters,totalTime



def die_with_usage():
    """
    HELP MENU
    """
    print 'Test a set of saved model with a given dataset.'
    print 'Usage:'
    print 'python plot_filt_vs_nonfilt.py [flags] <savedmodelFILT> <savedmodelNONFILT> <matfilesdir> <output.txt>'
    print 'PARAMS:'
    print '  <savedmodelFILT>    directory where an online FILT model is saved'
    print '  <savedmodelNONFILT> directory where an online regular model is saved'
    print '  <matfilesdir>  '
    print '  <output.txt>   '
    print 'FLAGS:'
    print '  -plot          plot dist in function of patterns seen'
    print ''
    print 'T. Bertin-Mahieux (2010) Columbia University'
    print 'tb2332@columbia.edu'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 4:
        die_with_usage()

    
    # flags
    doplot = True
    while True:
        if sys.argv[1] == '-plot':
            doplot = True
        else:
            break
        sys.argv.pop(1)


    # params
    savedmodelFILT = os.path.abspath(sys.argv[1])
    savedmodelNONFILT = os.path.abspath(sys.argv[2])
    matfilesdir = os.path.abspath(sys.argv[3])
    output = os.path.abspath(sys.argv[4])
    print_write('saved model FILT= '+ savedmodelFILT,output)
    print_write('saved model NONFILT= '+ savedmodelNONFILT,output)
    print_write('matfiles dir = '+ matfilesdir,output)
    print_write('output = '+output,output)

    # GET SAVED MODELS FILT
    parentdir,tmp = os.path.split(savedmodelFILT)
    # traceback
    tb = ANALYZE.traceback(savedmodelFILT)
    # find everything in parent folder, then just folders
    all_in_folder = glob.glob(os.path.join(parentdir,'*'))
    all_in_folder = filter(lambda x: os.path.isdir(x), all_in_folder)
    # keep those that have same origin
    leaves = filter(lambda x: ANALYZE.traceback(x)[0]==tb[0],all_in_folder)
    # everything to test, matfile at the end
    all_to_testFILT = set()
    for f in tb:
        if os.path.isdir(f):
            all_to_testFILT.add(f)
    for f in leaves:
        all_to_testFILT.add(f)
    all_to_testFILT = list(all_to_testFILT)
    # GET SAVED MODELS NON FILT
    parentdir,tmp = os.path.split(savedmodelNONFILT)
    # traceback
    tb = ANALYZE.traceback(savedmodelNONFILT)
    # find everything in parent folder, then just folders
    all_in_folder = glob.glob(os.path.join(parentdir,'*'))
    all_in_folder = filter(lambda x: os.path.isdir(x), all_in_folder)
    # keep those that have same origin
    leaves = filter(lambda x: ANALYZE.traceback(x)[0]==tb[0],all_in_folder)
    # everything to test, matfile at the end
    all_to_testNONFILT = set()
    for f in tb:
        if os.path.isdir(f):
            all_to_testNONFILT.add(f)
    for f in leaves:
        all_to_testNONFILT.add(f)
    all_to_testNONFILT = list(all_to_testNONFILT)

    
    # GET PARAMS / LOAD DATA
    params = ANALYZE.unpickle(os.path.join(savedmodelFILT,'params.p'))
    oracle = ORACLE.OracleMatfiles(params,matfilesdir,oneFullIter=True)
    data = [x for x in oracle]
    data = filter(lambda x: x != None, data)
    data = np.concatenate(data)
    data = data[np.where(np.sum(data,axis=1)>0)]
    if data.shape[0] == 0:
        print_write('No patterns loaded, quit.',output)
        sys.exit(0)

    # PREDICT ON EVERY MODEL FILT
    distsFILT = []
    patternsFILT = []
    for f in all_to_test:
        a,b,c,d = test_saved_model_folder(f,data,output,filt=True)
        dist,nPatterns,nIters,totalTime = a,b,c,d
        distsFILT.append(dist)
        patternsFILT.append(nPatterns)
    # PREDICT ON EVERY MODEL NON FILT
    distsNONFILT = []
    patternsNONFILT = []
    for f in all_to_test:
        a,b,c,d = test_saved_model_folder(f,data,output,filt=False)
        dist,nPatterns,nIters,totalTime = a,b,c,d
        distsNONFILT.append(dist)
        patternsNONFILT.append(nPatterns)

    # plot
    if doplot:
        import pylab as P
        P.figure()
        P.hold(True)
        # NON FILT
        dists = np.array(distsNONFILT)
        patterns = np.array(patternsNONFILT)
        order = np.argsort(patterns)
        dists = P.plot(patterns[order],dists[order])
        # FILT
        dists = np.array(distsFILT)
        patterns = np.array(patternsFILT)
        order = np.argsort(patterns)
        dists = P.plot(patterns[order],dists[order])
        # done, release, show
        P.title('FILT / NON FILT')
        P.hold(False)
        P.show()
