"""
Library to handle EchoNest features.
Mainly, to get patterns.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import time
import glob
import scipy as sp
import numpy as np



def create_beat_synchro_chromagram(analysis_dict):
    """
    - Takes the analysis obtained from the EchoNest oracle
    - Transform the analysis per segment in analysis per beat
    RETURN
       btchroma     chroma synchronized per beat
                    if N beats, btchroma.shape==(12,N)
       barbts       beggining of bars as a beat index
    """
    # Echo Nest "segment" synchronous chroma
    # 12 values per line (one segment per line)
    # result for track: 'TR0002Q11C3FA8332D'
    #    segchroma.shape = (12, 708)
    segchroma = analysis_dict['chromas']

    # get the series of starts for segments, beats, and bars
    # result for track: 'TR0002Q11C3FA8332D'
    #    segstart.shape = (708,)
    #    btstart.shape = (304,)
    #    barstart.shape = (98,)
    segstart = analysis_dict['segstart']
    btstart = np.array(analysis_dict['beatstart'])
    barstart = np.array(analysis_dict['barstart'])

    # get duration
    duration = analysis_dict['duration']

    # CHROMA PER BEAT
    # Move segment chromagram onto a regular grid
    # result for track: 'TR0002Q11C3FA8332D'
    #    warpmat.shape = (304, 708)
    #    btchroma.shape = (304, 12)
    warpmat = get_time_warp_matrix(segstart, btstart, duration)
    btchroma = np.dot(warpmat, segchroma)

    # Renormalize.
    btchroma = (btchroma.T / btchroma.max(axis=1)).T

    # get the bars in number of beats, do I need that?
    barbts = np.zeros(barstart.shape)
    # get the first (only?) beat the starts at the same time as the bar
    for n, x in enumerate(barstart):
        barbts[n] = np.nonzero((btstart - x) == 0)[0][0]

    # done, return chroma per beat
    return btchroma, barbts
