"""
Try to do segmentation based on a similarity matrix and
fingerprint features (maximums)

T. Bertin-Mahieux (2010) Columbia Uniersity
tb2332@columbia.edu
"""

import os
import sys
import scipy.io as sio
import numpy as np

import dummy_segmenter as DUMMY
import simmatrix as SIMMAT
from fingerprint import get_landmarks as LANDMARKS

_enfeats_dir = os.path.abspath('~/Columbia/InfiniteListener/beatles_enfeats')
_audio_dir = os.path.abspath('~/Columbia/InfiniteListener/beatles_audio')


def maxes_beattimes_segs_from_audiofile(wavfile):
    """
    Utility function
    From a given eavfile:
    - computes the fingerprint maxes
    - gets the corresponding en beat times
    - gets the corresponding annotated segments
    RETURN:
    maxes, beatstarts, duration, segstarts, segstops, labels
    """
    # fingerprint it
    L,S,T,maxes = LANDMARKS.get_landmarks.find_landmarks_from_wav(wavfile)
    # find the EN matfile
    relwavfile = os.path.relpath(wavfile,_audio_dir)
    enmatfile = os.path.join([_enfeats_dir,relwavfile,'.mat'])
    assert os.path.exists(enmatfile),'can not find matfile %s' % enmatfile
    mat = sio.loadmat(enmatfile)
    btstart = mat['btstart']
    duration = mat['duration']
    # get the segments
    labfile = os.path.join(enmatfile,'.lab')
    assert os.path.exists(labfile),'can not find labfile %s' % labfile
    segstarts, segstops, labels = DUMMY.read_lab_file(labfile)
    # done, return
    return maxes, btstart, duration, segstarts, segstops, labels











def die_with_usage():
    """ HELP MENU """
    print 'functions to do segmentation with fingerprint features'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # DEBUGGING
    maxes_beattimes_segs_from_audiofile(sys.argv[1])

