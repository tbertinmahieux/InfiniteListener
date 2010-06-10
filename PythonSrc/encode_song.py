"""
Simple code to take a dictionary, encode a song, plot the two,
report distortion.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import numpy as np
import scipy.io
import features as FEATS
import model as MODEL



def die_with_usage():
    """ HELP MENU """
    print 'python encode_song.py [flags] <song mat> <codebook>'
    print 'INPUT'
    print ' <song mat>        EN features for one song'
    print ' <codebook>        codebook.mt from initializer or trainer'
    print 'FLAGS:'
    print ' -pSize n          final pattern size is 12 x n'
    print ' -usebars n        n number of bars per pattern, or 0'
    print ' -noKeyInv         do not perform key inveriance on patterns'
    print ' -songKeyInv       perform key invariance on song level'
    print ' -notpositive      do not replace negative values by zero'
    print ' -dont_resample    pad or crop instead'
    print ''
    print 'typical command:'
    print 'python encode_song.py -pSize 8 -usebars 2 song.mat codebook.mat'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 3:
        die_with_usage()


    # flags
    pSize = 8
    usebars = 2
    keyInv = True
    songKeyInv = False
    positive = True
    do_resample = True
    while True:
        if sys.argv[1] == '-pSize':
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
        else:
            break
        sys.argv.pop(1)


    # load song
    songpath = sys.argv[1]
    print 'song file:',songpath
    dictpath = sys.argv[2]
    print 'codebook file:',dictpath

    # feats
    feats =  FEATS.features_from_matfile(songpath,pSize=pSize,
                                         usebars=usebars,keyInv=keyInv,
                                         songKeyInv=songKeyInv,
                                         positive=positive,
                                         do_resample=do_resample)
    # model
    mat = scipy.io.loadmat(dictpath)
    codebook = mat['codebook']
    model = MODEL.Model(codebook)

    # predict
    best_code_per_pattern, avg_dist = model.predicts(feats)

    # report distortion (per... pixel? patch point?)
    print 'average distortion:', np.average(avg_dist)

    # build original and encoding
    patch_len = codebook.shape[1]/12
    btchroma = np.concatenate([c.reshape(12,patch_len) for c in feats],axis=1)
    btchroma_encoded = np.concatenate([codebook[int(k)].reshape(12,patch_len) for k in best_code_per_pattern],
                                      axis=1)

    # plot
    import pylab as P
    pparams = {'interpolation':'nearest','origin':'lower','cmap':P.cm.gray_r,'aspect':'auto'}
    P.subplot(2,1,1)
    P.imshow(btchroma,**pparams)
    P.subplot(2,1,2)
    P.imshow(btchroma_encoded,**pparams)
    # add lines
    for k in range(patch_len,btchroma.shape[1],patch_len):
        P.axvline(x=k-.5,ymin=0,ymax=1,color='r')
    P.show()

