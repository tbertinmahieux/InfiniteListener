"""
T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu

More of a random test than a working program.
Tries to use our multi dictionaries to find a segmentation.
"""



import os
import sys
import numpy as np
import scipy
import scipy.io as SIO

try:
    import features as FEATURES
except ImportError:
    sys.path.append( os.path.abspath('..') )
    import features as FEATURES
import multidict_encode as ENCODE
import measures as MEASURES


def read_lab_file(fnIn):
    """
    Read a segmentation file, based on EN beats
    RETURN
    startbeats, stopbeats, labels
    """
    startbeats = []
    stopbeats = []
    labels = []
    # open file, iterate over lines, close file
    f = open(fnIn,'r')
    for line in f.readlines():
        if line == "" or line.strip() == "":
            continue
        line = line.strip()
        stubs = filter(lambda x: x != "", line.split('\t'))
        assert len(stubs) >= 3, 'weird line'
        startbeats.append( int (stubs[0]) )
        stopbeats.append( int (stubs[1]) )
        labels.append( stubs[2] )
    f.close()
    # done, return
    return startbeats, stopbeats, labels


def get_cuts(dictlib,dicts):
    """
    From an encoding, return the position where the song might
    be cut (0 and end excluded)
    """
    cuts = []
    beatidx = 0
    for k in range(len(dicts)):
        if k == len(dicts)-1:
            continue
        didx = int(dicts[k])
        beatidx += dictlib[didx].shape[1]/12
        cuts.append(beatidx)
    return cuts
        


def die_with_usage():
    """ HELP MENU. """
    print 'python multidict_segment.py -dictdir <dir> <song matfile> <OPT: max recursion'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 3:
        die_with_usage()

    # flags
    dictlib = None
    while True:
        if len(sys.argv) < 2:
            break
        if sys.argv[1] == '-dictdir':
            dictlib = ENCODE.load_dict_dir(sys.argv[2],dictlib=dictlib)
            sys.argv.pop(1)
        else:
            break
        sys.argv.pop(1)

    # print dictlib info
    print dictlib

    # load the matfile, get the beatchromas
    matfile = sys.argv[1]
    maxrecursion = np.inf
    if len(sys.argv) > 2:
        maxrecursion = int(sys.argv[2])
    mat = SIO.loadmat(matfile)
    btchroma = mat['btchroma']
    btchroma = FEATURES.keyinvariance(btchroma)

    # do a regular multiencoding, mainly for display purposes
    dicts,codes,score = ENCODE.encode(btchroma,dictlib,ENCODE.avg_square_eucl_dist)
    btchroma_encoded = ENCODE.build_encoding(dictlib,dicts,codes)

    # get the longest dictionary
    longest_p_len = dictlib[len(dictlib)-1].shape[1]/12

    # check if lab file exists for segmentation
    labfile = ''
    if os.path.exists(matfile + '.lab'):
        labfile = matfile + '.lab'

    # iterate with dictionaries of size 1,2,3 + larger size
    possible_cuts = set()
    count_cuts = np.zeros(btchroma.shape[1])
    cnt_iters = 0
    min_length = 2
    for k in range(longest_p_len,min_length,-1):
        # check max recursion
        cnt_iters += 1
        if cnt_iters > maxrecursion:
            break
        # get dict_lib subset
        dl = dictlib.subset(range(0,min_length)+[k-1])
        # encode
        dicts,codes,dist = ENCODE.encode(btchroma,dl,ENCODE.avg_square_eucl_dist)
        # get cuts
        cuts = get_cuts(dl,dicts)
        for c in cuts:
            count_cuts[c] += 1
        print 'for longest dict',k,', number of cuts =',len(cuts)
        # check possible remaining cuts
        if k == longest_p_len:
            possible_cuts = set(cuts)
        else:
            possible_cuts = possible_cuts.intersection(set(cuts))
        print 'number of remaining cuts:',len(possible_cuts)
        # get measures on segmentation
        if labfile != '':
            startbref, stopbref, labels = read_lab_file(labfile)
            startbcand = np.unique([0] + map(lambda x:x-1,possible_cuts))
            stopbcand = np.unique(list(possible_cuts) + [btchroma.shape[1]-1])
            prec,rec,fval = MEASURES.pairwise_prec_rec_f(startbref,stopbref,
                                                         startbcand,stopbcand)
            print 'prec =',prec,', rec =',rec,', fval =',fval
    # iteration done, print
    if len(possible_cuts) > 0:
        print 'remaining possible cuts:',possible_cuts

    # print
    import pylab as P
    pparams = {'interpolation':'nearest','origin':'lower','cmap':P.cm.gray_r,'aspect':'auto'}
    P.subplot(2,1,1)
    P.imshow(btchroma,**pparams)
    P.subplot(2,1,2)
    P.imshow(btchroma_encoded,**pparams)
    # add lines
    #for c in possible_cuts:
    #    P.axvline(x=c-.5,ymin=0,ymax=1,color='r')
    for k in range(len(count_cuts)):
        P.axvline(x=k-.5,ymin=0,ymax=1.*count_cuts[k]/np.max(count_cuts),color='r')
    P.show()
