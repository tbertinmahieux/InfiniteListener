"""
Set of functions to perform similary based on a similarity matrix.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import numpy as np

import dummy_segmenter as DUMMY

def euclidean_dist(a,b):
    """
    Typical euclidean distance. A and B must be row vectors!!!!
    """
    return np.sqrt(np.square(a-b).sum())


def build_simmat(data,winsize=1,overlap=0,dist=euclidean_dist):
    """
    Receives a data (#feats x #beats), 12xN in the case of chromas
    Build a similarity matrix based on distortion measure
    (euclidean by default)
    INPUTS:
      winsize    windowsize (default: 1)
      overlap    overlap between windows (default: 0)
      dist       distortion measures, takes two row vectors
    """
    assert data.shape[0]>0 and data.shape[1]>1,'useless data, check shape'
    assert overlap<winsize,'overlap >= window size'
    # compute final dimension of the similarity matrix
    nblocks = int((data.shape[1] - winsize) / (winsize - overlap)) + 1
    # create empty similarity matrix
    simmat = np.zeros([nblocks,nblocks])
    # fill it!!! slow..
    for l in range(nblocks):
        lblockstart = winsize + (l-1) * (winsize - overlap)
        for c in range(l,nblocks):
            cblockstart = winsize + (c-1) * (winsize - overlap)
            # compute distortion
            d = dist(data[:,lblockstart:lblockstart+winsize].flatten(),
                     data[:,cblockstart:cblockstart+winsize].flatten())
            # fill in
            simmat[l,c] = d
            simmat[c,l] = d
    # done, return similarity matrix
    return simmat


def plot_simmat(data,winsize=1,overlap=0,dist=euclidean_dist,labfile=''):
    """
    Similat to build_simmat, but plot it, and can add labfile information
    """
    # get simmat
    simmat = build_simmat(data,winsize=winsize,overlap=overlap,dist=dist)
    # PLOT IT
    import pylab as P
    P.figure()
    args2 = {'interpolation':'nearest','cmap':P.cm.gray,'aspect':'auto'}
    P.imshow(simmat,**args2)
    # we have labfile?
    if labfile != '':
        P.hold(True)
        startbeats,stopbeats,labels = DUMMY.read_lab_file(labfile)
        for sb in startbeats:
            pos = int((sb - winsize) / (winsize - overlap)) + 1
            assert pos <= simmat.shape[1],'wrong pos for lab data'
            point_size = 30
            P.scatter(pos,pos,s=point_size,c='r',marker='o')
            P.scatter(pos,0,s=point_size,c='r',marker='o')
            P.scatter(0,pos,s=point_size,c='r',marker='o')
        P.hold(False)
    P.show()
    # plot first derivative
    P.figure()
    simmat_diff = np.diff(simmat)
    simmat_diff = simmat_diff * simmat_diff
    P.imshow(simmat_diff,**args2)
    # we have labfile?
    if labfile != '':
        P.hold(True)
        startbeats,stopbeats,labels = DUMMY.read_lab_file(labfile)
        for sb in startbeats:
            pos = int((sb - winsize) / (winsize - overlap)) + 1 - 1
            assert pos <= simmat.shape[1],'wrong pos for lab data'
            point_size = 30
            P.scatter(pos,pos,s=point_size,c='r',marker='o')
            P.scatter(pos,0,s=point_size,c='r',marker='o')
            P.scatter(0,pos,s=point_size,c='r',marker='o')
        P.hold(False)
    P.show()
    # done, return simmat
    return simmat


def gaussian_segmenter(simmat,theta,threshold):
    """
    Segment a similarity matrix based on a gaussian like filter
    [+1 -1; -1 +1]
    theta controls the variance, threshold controls how to decide if
    it a new segment or not
    """
    import scipy.ndimage as IMAGE

    raise NotImplementedError
