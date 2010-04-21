"""
Very similar to test_trained_model
but assumes one of the model used filtering, and go get
the actual number of features seen

Actually, extension of plot_filt_vs_nonfilt.py
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




def plot_from_file(filename):
    """
    Plot the learning curves from data saved to file.
    Data must be between '#PLOTSTART' and '#PLOTEND'
    Data is 3 lines: patterns, dists, comment
    """
    # import pylab
    import pylab as P

    # PARSE FILE
    f = open(filename,'r')
    # find beginning of data
    line = f.next()
    while line[:len('#PLOTSTART')] != '#PLOTSTART':
        line = f.next()
    curves = []
    curve = []
    # iterate over lines
    while True:
        line = f.next()
        print 'line=',line
        if line[:len('#PLOTEND')] == '#PLOTEND':
            if len(curve) > 0:
                curves.append( curve )
            break
        if line[:len('#PLOT')] == '#PLOT':
            if len(curve) > 0:
                curves.append( curve )
            curve = []
            continue
        curve.append(eval(line))     # nSamples
        curve.append(eval(f.next())) # dists
        curve.append(f.next())       # comment
    # close file
    f.close()

    # plotting symbols
    psymbs = ['-','--','-.',':','x-','o-','s-','+-','<-','>-']

    # create figure
    P.figure()
    P.hold(True)

    # iterate over bitrates
    idx = -1
    for curve in curves:
        idx += 1
        # plot
        P.plot(curve[0],curve[1],psymbs[idx],label=curve[2])
        
    # legend
    P.legend()
    # done, release, show
    P.hold(False)
    P.show()


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



def analyze_one_batch_of_models(savedmodel, matfilesdir, output, filt=False):
    """
    Main job, from a saved model, find other saved model in same dir,
    test them all, return plotting info (nSamples and dist)
    """
    # GET SAVED MODELS
    parentdir,tmp = os.path.split(savedmodel)
    # traceback
    tb = ANALYZE.traceback(savedmodel)
    # find everything in parent folder, then just folders
    all_in_folder = glob.glob(os.path.join(parentdir,'*'))
    all_in_folder = filter(lambda x: os.path.isdir(x), all_in_folder)
    # keep those that have same origin
    leaves = filter(lambda x: ANALYZE.traceback(x)[0]==tb[0],all_in_folder)
    # everything to test, matfile at the end
    all_to_test = set()
    for f in tb:
        if os.path.isdir(f):
            all_to_test.add(f)
    for f in leaves:
        all_to_test.add(f)
    all_to_test = list(all_to_test)
    # GET PARAMS / LOAD DATA
    params = ANALYZE.unpickle(os.path.join(savedmodel,'params.p'))
    oracle = ORACLE.OracleMatfiles(params,matfilesdir,oneFullIter=True)
    data = [x for x in oracle]
    data = filter(lambda x: x != None, data)
    data = np.concatenate(data)
    data = data[np.where(np.sum(data,axis=1)>0)]
    if data.shape[0] == 0:
        print_write('No patterns loaded, quit.',output)
        sys.exit(0)
    # PREDICT ON EVERY MODEL
    dists = []
    patterns = []
    for f in all_to_test:
        a,b,c,d = test_saved_model_folder(f,data,output,filt=filt)
        dist,nPatterns,nIters,totalTime = a,b,c,d
        dists.append(dist)
        patterns.append(nPatterns)
    # delete data before plotting
    del data
    # plot data
    dists = np.array(dists)
    patterns = np.array(patterns)
    order = np.argsort(patterns)
    # return 2 lists: nPatterns,dists and filt   ordered by increasing patterns
    return patterns[order],dists[order]


def die_with_usage():
    """
    HELP MENU
    """
    print 'Test a set of saved model with a given dataset.'
    print 'Usage:'
    print '   python plot_filt_vs_nonfilt.py [flags] <matfilesdir> <output.txt> <-plotfilt savedmodelFILT (comment)> <-plot savedmodel (comment)> <-plot...'
    print '(you can have as many -plot and -plotfilt as needed)'
    print '(comment optional)'
    sys.exit(0)



if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 4:
        die_with_usage()

    
    # flags
    while True:
        if sys.argv[1] == 'NOFLAGYET':
            pass
        else:
            break
        sys.argv.pop(1)

    # params
    matfilesdir = os.path.abspath(sys.argv[1])
    output = os.path.abspath(sys.argv[2])
    sys.argv.pop(1)
    sys.argv.pop(1)

    # init output
    f = open(output,'w')
    f.close()

    plotdata = []
    # iterate over -plot and -plotfilt
    while True:
        if len(sys.argv) < 3:
            break
        filt = False
        comment = ' '
        if sys.argv[1] == '-plot':
            pass
        elif sys.argv[1] == '-plotfilt':
            filt = True
        else:
            print 'bad command:',sys.argv[1]
            break
        savedmodel = sys.argv[2]
        print 'savedmodel = ', savedmodel
        sys.argv.pop(1)
        sys.argv.pop(1)
        if len(sys.argv) > 1 and sys.argv[1][:len('-plot')] != '-plot':
            comment = sys.argv[1]
            sys.argv.pop(1)
        res = analyze_one_batch_of_models(savedmodel, matfilesdir, output, filt=filt)
        res = list(res)
        res.append(comment)
        plotdata.append(res)

    # plot the data to file
    print_write('#PLOTSTART',output)
    for res in plotdata:
        print_write('#PLOT',output)
        # nPatterns, dist, comment
        print_write(str(res[0].tolist()),output)
        print_write(str(res[1].tolist()),output)
        print_write(str(res[2]),output)
    print_write('#PLOTEND',output)

    # print from file
    plot_from_file(output)
