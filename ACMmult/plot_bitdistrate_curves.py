"""
Code to analyze a set of experiments and automatically plot the
curves, and saves the data
"""

import os
import sys
import glob
import pickle
import numpy as np

import oracle_matfiles as ORACLE
import analyze_saved_model as ANALYZE
import model as MODEL
import for_ron as RON


def same_bitrate_curve(psize1,ncodes1,psize2,ncodes2):
    """
    Returns True or false, decides if two bit rates are the same or not.
    Meaning: when the psize is double, ncodes is squared. So, one of the
    psize is a multiple of a power of two of the other (2->4, 2->8,4->256,...)
    and the data is squared that many times (2->4 => ncordes*ncodes)
    """
    # trivial case
    if psize1 == psize2:
        if ncodes1 == ncodes2:
            return True
        return False
    # make sure psize1 is smaller: psize1 < psize2
    if psize1 > psize2:
        psize2,psize1 = psize1,psize2
        ncodes2,ncodes1 = ncodes1,ncodes2
    # other trivial case
    if ncodes2 < ncodes1:
        return False
    # REAL JOB STARTS HERE
    exponent = np.log(psize2) / np.log(psize1)
    if abs(exponent - np.round(exponent)) > 1e-14:
        return False
    exponent = int(np.round(exponent))
    # psize fits, now ncodes
    n1 = ncodes1
    for k in range(exponent-1):
        n1 = n1 * n1
    if n1 == ncodes2:
        return True
    return False



def analyze_one_exp_dir(expdir,validdir,testdir):
    """
    Analyze one experiment dir.
    This directory contains many subdirectory, for all the saved models.
    Check every saved model with validdata (numpy array), and test the
    best one on the test data.
    Returns numbers: patternsize, codebook size, distortion error, best saved model
    """
    # get all subdirs
    alldirs = glob.glob(os.path.join(experiment_dir,'*'))
    if len(alldirs) > 0:
        alldirs = filter(lambda x: os.path.isdir(x), alldirs)
        alldirs = filter(lambda x: os.path.split(x)[-1][:4] == 'exp_',alldirs)
        # trim badly saved models
        alldirs = filter(lambda x: RON.check_saved_model_full(x,False), alldirs)
    if len(alldirs) == 0:
        print 'no saved model found in:',expdir
        return None,None,None,None
    
    # get params
    savedmodel = np.sort(alldirs)[-1]
    params = unpickle(os.path.join(savedmodel,'params.p'))

    # load valid data
    oracle = ORACLE.OracleMatfiles(params,validdir,oneFullIter=True)
    validdata = [x for x in oracle]
    validdata = filter(lambda x: x != None, validdata)
    validdata = np.concatenate(validdata)
    assert validdata.shape[1] > 0,'no valid data??'
    
    # load test data
    oracle = ORACLE.OracleMatfiles(params,testdir,oneFullIter=True)
    testdata = [x for x in oracle]
    testdata = filter(lambda x: x != None, testdata)
    testdata = np.concatenate(testdata)
    assert testdata.shape[1] > 0,'no valid data??'

    # test all subdirs with valid data, keep the best
    best_model = ''
    best_dist = np.inf
    for sm in alldirs:
        model = ANALYZE.unpickle(os.path.join(sm,'model.p'))
        avg_dist = model.predicts(validdata)
        if avg_dist < best_dist:
            best_model = sm
    assert best_model != '','no data found???'
    
    # test with test data
    model = ANALYZE.unpickle(os.path.join(best_model,'model.p'))
    avg_dist = model.predicts(testdata)

    # return patternsize, codebook size, distortion errror, best saved model
    return testdata.shape[1], model._codebook.shape[1], avg_dist, best_model






def die_with_usage():
    """
    HELP MENU
    """
    print 'usage:'
    print 'python plot_bitdistrate_curves.py <valid dir> <test dir> <output> <exp1> .... <expN>'
    print 'PARAMS:'
    print ' <valid dir>    contains matfiles of validation set'
    print '  <test dir>    contains matfiles of test set'
    print '    <output>    filename to text file, something like results.txt'
    print '     <exp..>    path to experiment folder, "set2exp12" for instance'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 5:
        die_with_usage()

    # flags


    # params
    validdir = sys.argv[1]
    testdir = sys.argv[2]
    output = sys.argv[3]
    expdirs = []
    for k in range(4,len(sys.argv)):
        expdirs.append( sys.argv[k] )
    print 'experiment dirs:', expdirs

    # analyze each experiment dir
    results = []
    for d in expdirs:
        print 'doing exp dir:',d
        res = analyze_one_exp_dir(d,validdir,testdir)
        if res != None,None,None,None:
            results.append(res)

    # print to file, debug
    f = open(output,'w')
    f.write(str(results) + '\n')

    # organize the results
    bitrates = []
    while len(results) == 0:
        # get one res
        res = results.pop()
        # check if it belongs to one set
        belongs = False
        for bitrate in bitrates:
            ref = bitrate[0]
            if same_bitrate_curve(res[0],res[1],ref[0],ref[1]):
                bitrate.append(res)
                belongs = True
                break
        # does not belong to existing set? create new one
        if not belongs:
            bitrates.append( [res] )
    print 'bitrates found, we have',len(bitrates),'of them.'

    # print to file
    for bitrate in bitrates:
        f.write('********* ONE BITRATE **********\n')
        for res in bitrate:
            fwrite('psize='+str(res[0]))
            fwrite(', ncodes='+str(res[1]))
            fwrite(', dist='+str(res[2]))
            fwrite(', model='+res[3])
            fwrite('\n')

    # done with file, close output
    f.close()

    ########################## PLOT #############################

    # import, create figure
    import pylab as P
    P.figure()
    P.hold(True)



    # done, release, show
    P.hold(False)
    P.show()
