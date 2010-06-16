"""
Try to do segmentation based on a similarity matrix and
fingerprint features (maximums)

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import scipy.io as sio
import numpy as np

import dummy_segmenter as DUMMY
import simmatrix as SIMMAT
from fingerprint import get_landmarks as LANDMARKS

_enfeats_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_enbeatfeats')
_audio_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_audio')


def maxes_beattimes_segs_from_audiofile(wavfile):
    """
    Utility function
    From a given eavfile:
    - computes the fingerprint maxes
    - gets the corresponding en beat times
    - gets the corresponding annotated segments
    RETURN:
    signal, sampling rate, maxes, beatstarts, duration, segstarts, labels
    """
    # fingerprint it
    wav = LANDMARKS.AUDIOLAB.wavread(wavfile)
    L,S,T,maxes = LANDMARKS.find_landmarks(wav[0],wav[1])
    # find the EN matfile
    relwavfile = os.path.relpath(wavfile,start=_audio_dir)
    enmatfile = os.path.join(_enfeats_dir,relwavfile+'.mat')
    assert os.path.exists(enmatfile),'can not find matfile %s' % enmatfile
    mat = sio.loadmat(enmatfile)
    btstart = mat['btstart']
    try:
        duration = mat['duration'][0][0] # must be some bug in encoding
    except TypeError:
        duration = mat['duration']
    # get the segments
    labfile = enmatfile+'.lab'
    assert os.path.exists(labfile),'can not find labfile %s' % labfile
    segstarts, segstops, labels = DUMMY.read_lab_file(labfile)
    # done, return
    return wav[0], wav[1], maxes, btstart, duration, segstarts, labels


def get_actual_times(maxes):
    """
    we transform the first row of the maxes into actual seconds,
    knowing we used a 64ms window with 32ms hop time to create them
    """
    fft_ms = 64 # see lines 82 and 83 of matlab code
    fft_hop = 32
    # convert
    diff_ms = fft_ms - fft_hop
    ms = map(lambda x: (x-1) * diff_ms + fft_ms / 2, maxes[0,:])
    secs = map(lambda x: x / 1000., ms)
    # done, return seconds
    return secs


def get_fingerprint_feats_per_beat(btstart,duration,maxes,maxessecs):
    """
    Compute a set of features per beat
    btstart is a 1xN numpy array
    maxes is the usual two rwo matrix
    maxessecs is the seconds of the different max points
    RETURN:
      array of one numpy array per beat
      each of these numpy array contains seconds (row 0) and freq (row 1)
    """
    res = []
    for k in range(btstart.shape[1]):
        # beat start and stop
        bstart = btstart[0,k]
        try:
            bstop = btstart[0,k+1]
        except IndexError:
            bstop = duration
        # find all maxes that fit in there
        m_idxs = filter(lambda x: maxessecs[x] >= bstart and maxessecs[x] < bstop, range(len(maxessecs)))
        m_idxs = np.array(m_idxs)
        # none found?
        if m_idxs.shape[0] == 0:
            res.append(np.zeros([2,0]))
            continue
        # create subsets, with seconds instead of beats
        submaxes = maxes[:,m_idxs]
        submaxes[0,:] = np.array(maxessecs)[m_idxs] - bstart
        res.append(submaxes)
    # done, return res
    assert len(res) == btstart.shape[1],'wrong number of feats per beat'
    return res





def die_with_usage():
    """ HELP MENU """
    print 'functions to do segmentation with fingerprint features'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # DEBUGGING
    sig,sr,maxes,btstart,dur,segstart,labels = maxes_beattimes_segs_from_audiofile(sys.argv[1])
    print 'sig shape:',sig.shape
    print 'sr:',sr
    print 'maxes shape:',maxes.shape
    print 'maxes max row 0:',np.max(maxes[0,:])
    print 'maxes max row 1:',np.max(maxes[1,:])
    print 'duration:',dur
    print 'last max in secs:',get_actual_times(maxes)[-1]

    # create feats per beats
    maxessecs = get_actual_times(maxes)
    feats_per_beat = get_fingerprint_feats_per_beat(btstart,dur,maxes,maxessecs)    
