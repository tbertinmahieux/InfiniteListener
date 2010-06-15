"""
Interface to Dan's fingerprinting code in MATLAB
Get the landmarks (i.e. points of interest) of a signal

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import numpy as np

from mlabwrap import mlab
import scikits.audiolab as AUDIOLAB

# makes sure we have the right matlab files
# save their absolute path
_code_dir = os.path.dirname(__file__)
_find_landmarks_path = os.path.join(os.path.abspath(_code_dir),'find_landmarks.m')
if not os.path.exists(_find_landmarks_path):
    print "can't find find_lanmarks.m, not same place as get_landmarks?"
    print "get_landmarks.py dir:",_code_dir
    raise ImportError
mlab.addpath(_code_dir)

def wavread(path):
    """
    Wrapper around scikits functions
    Returns: wavdata, sample rate, encoding type
    See pyaudiolab or scikits.audiolab for more information
    """
    return AUDIOLAB.wavread(path)


def find_landmarks_from_wav(wavpath):
    """
    utility function, open wav, calls find_landmarks
    """
    wav = wavread(wavpath)
    return find_landmarks(wav[0],wav[1])

def find_landmarks(wav,samplerate):
    """
    call the find_landmarks.m matlab function
    Returns 4 stuff: L,S,T,maxes
    """
    L,S,T,maxes = mlab.find_landmarks(wav,samplerate,nout=4)
    return L,S,T,maxes

