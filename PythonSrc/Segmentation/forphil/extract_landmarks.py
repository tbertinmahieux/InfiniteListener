"""
Code to easily extract fingerprint features and save them in a
numpy array file.
Relies on Dan's code in matlab, and mlabwrap to access it.

Thierry Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import numpy as np
import audioio
# wrapper around Dan's fingerprinting code
# mlab imported there
from fingerprint import get_landmarks as LANDMARKS


def extract(mp3file,npyfile=''):
    """
    Get an mp3 file, reads it, extract fingerprints features,
    saves it to a given npyfile (if different than '')
    RETURN numpy array for debugging purposes
    """
    # read mp3 through MATLAB mp3 file
    x,fs,tmp = audioio.audioread(mp3file)
    x = np.average(x,axis=1)
    assert x.shape[0] > 2,'bad signal averaging'
    # get the fingerprint features
    L,S,T,maxes = LANDMARKS.find_landmarks(x,fs)
    # create the maxes matrix
    maxes = maxes - 1 # matlab starts at 0
    nfreq = 256
    assert np.max(maxes[1,:]) < nfreq,'max freq too high'
    nsamp = int(np.max(maxes[0,:]) + 1)
    data = np.zeros([nfreq,nsamp])
    # fill in data
    for m in range(maxes.shape[1]):
        data[maxes[1,m],maxes[0,m]] += 1
    # save to npy
    if npyfile != '':
        np.save(npyfile,data)
    # return data for debugging or ipython usage
    return data
