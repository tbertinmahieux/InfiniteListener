"""
Simple method to perform song segmentation using Ron's method and
Echo Nest chroma features.

Also, can use codebook encoding.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import glob
import numpy as np
import scipy.io as sio

rondir = 'ronwsiplca'
from ronwsiplca import segmenter as SEGMENTER
from mlabwrap import mlab
mlab.addpath(os.path.abspath(rondir))
mlab.addpath(os.path.abspath('.'))

# beatles directories on my machines (TBM)
_enfeats_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_enbeatfeats')
_audio_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_audio')
_seglab_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_seglab')



def siplca_btchroma(btchroma,rank=4,win=60,plotiter=0,printiter=10,niter=200,alphaZ=0):
    """
    Main method, takes a beat chroma matrix, segments it using Ron's SIPLCA
    RETURN
     - labels, one number per frame
    """
    np.random.seed(123)
    labels, W, Z, H, segfun, norm= SEGMENTER.segment_song(btchroma, rank=rank,win=win,
                                                          plotiter=plotiter,
                                                          printiter=printiter,
                                                          niter=niter,alphaZ=alphaZ)
    return labels, W, Z, H, segfun, norm


def evaluate_segmentation(labels, gtlabels, Z):
    """
    Wrapper around Ron's function, get labels from siplca_btchroma function
    RETURN
     - a dictionary containing name-value pairs of the form 'metric name': value.
    """
    res = SEGMENTER.evaluate_segmentation(labels,gtlabels,Z)
    return res


def labfile_to_framewise_label(labfile,beattimes):
    """
    Convert a labfile:
      t1 t2 verse
      t1 t2 chorus
      ...
    to a set of numerical values, one per beattime: [0 0 0 1 1 2 1 1 ...]
    """
    beattimes = beattimes.reshape(1,beattimes.size)
    framelabs =  mlab.seglabfile_to_framelabs(labfile,beattimes)
    # make sure beattimes was formatted correctly, and so is the result
    assert beattimes.size == framelabs.size, 'wrong format, size problem'
    assert beattimes.shape == framelabs.shape, 'wrong format, shape problem'
    # done
    return framelabs

def encode_and_eval_one_beatle_song(wavfile,rank=16,win=40,plotiter=0,printiter=50,
                                    niter=200,alphaZ=-0.005):
    """
    Does the work for one song:
     - find the EN chroma
     - segment it using SIPLCA and params
     - (encode)
     - evaluate result
    """
    # find EN beat chroma for the song
    wavfile = os.path.abspath( wavfile )
    beatfile = os.path.relpath( wavfile, _audio_dir )
    beatfile = os.path.join( _enfeats_dir, beatfile + '.mat')
    assert os.path.exists(beatfile),'missing beat file'
    # find labfile for that song
    labfile = os.path.relpath( wavfile, _audio_dir )
    labfile = os.path.join( _seglab_dir, labfile )
    labfile = labfile[:-len('.wav')] + '.lab'
    assert os.path.exists(labfile),'missing lab file'
    # encode
    mat = sio.loadmat(beatfile)
    btchroma = mat['btchroma']
    bttimes = mat['btstart']
    labels, W, Z, H, segfun, norm = siplca_btchroma(btchroma,rank=rank,win=win,
                                                    plotiter=plotiter,
                                                    printiter=printiter,niter=niter,
                                                    alphaZ=alphaZ)
    # test result
    gtlabels = labfile_to_framewise_label(labfile,bttimes)
    results = evaluate_segmentation(labels,gtlabels,Z)
    print results



def encode_and_eval_all_beatles_songs(beatlesdir='',rank=16,win=40,plotiter=0,printiter=50,
                                      niter=200,alphaZ=-0.005):
    """
    Perform experiment on the whole beatle collection
    """
    if beatlesdir == '':
        beatlesdir = _audio_dir
    # get all wav files
