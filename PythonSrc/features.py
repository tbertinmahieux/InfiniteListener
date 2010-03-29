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




def get_features(analysis_dict,pSize=8,usebars=2,keyInv=True,songKeyInv=False,
                 positive=True,do_resample=True):
    """
    Main function, similar to those in demos.py for BostonHackDay
    Receives a dictionary containing:
         - segstart
         - chromas
         - beatstart
         - barstart
         - duration
    Returns a set of patterns, one per row, with the given pSize,
    bars, key invariance... or None if there is a problem

    This function works on the song level, so we can do invariance over songs
    if we want, etc.

    INPUT:
      analysis_dict      dictionary contanng the analysis, see above
      pSize              final size of a pattern (12 x pSize)
      usebars            patterns based on 'usebars' bars, not on beats
      keyInv             performs invariance over pattern (not songs)
      songKeyInv         same as keyInv, but over songs
      positive           negative numbers (due to rescaling) set to 0
      do_resample        if True resample, otherwise pad with zeros or crop

    RETURN:
      feats              features, one pattern per row, or None if problem
    """
    # param stuff
    if songKeyInv:
        keyInv = False # no ambiguity
    
    # get chroma per beat
    btchroma, barbts = create_beat_synchro_chromagram(analysis_dict)

    # song invariance
    if songKeyInv:
        btchroma = keyinvariance(btchroma)

    # case where no bar is used
    nBeats = btchroma.shape[0]
    if usebars == 0:
        barbts = np.array(range(0,nBeats-nBeats%pSize,pSize))
        usebars = 1

    # allocate space for anser
    nFeats = int(len(barbts)/2)
    feats = np.zeros([12,nFeats])

    # iterate on patterns
    for k in range(nFeats):
        # beginning of the bar
        bt1 = barbts[k]
        # end of the bar
        if k + usebars < nFeats:
            bt2 = barbts[k+usebars]
        else:
            bt2 = nBeats
        # pattern before resize and invariance
        pattern = btchroma[:,bt1:bt2]
        # resize by resampling on pad/crop
        if do_resample:
            pattern = resample(pattern,pSize)
        else:
            pattern = pad_crop(pattern,pSize)
        # key invariance
        if keyInv:
            pattern = keyinvariance(pattern)
        # add it to feats
        feats[k,:] = pattern.flatten()

    # remove negative numbers
    if positive:
        feats[np.where(feats<0)] = 0

    # done, return features
    return feats


def create_beat_synchro_chromagram(analysis_dict):
    """
    - Takes the analysis obtained from the EchoNest oracle
    - Transform the analysis per segment in analysis per beat
    INPUT
       dictionary containing:
         - segstart
         - chromas
         - beatstart
         - barstart
         - duration
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


def get_time_warp_matrix(segstart, btstart, duration):
    """
    Used by create_beat_synchro_chromagram
    Returns a matrix (#beats,#segs)
    #segs should be larger than #beats, i.e. many events or segs
    happen in one beat.
    """

    # length of beats and segments in seconds
    # result for track: 'TR0002Q11C3FA8332D'
    #    seglen.shape = (708,)
    #    btlen.shape = (304,)
    #    duration = 238.91546    meaning approx. 3min59s
    try:
        seglen = np.concatenate((segstart[1:], [duration])) - segstart
    except TypeError:
        raise NoSegError
    btlen = np.concatenate((btstart[1:], [duration])) - btstart

    warpmat = np.zeros((len(segstart), len(btstart)))
    # iterate over beats (columns of warpmat)
    for n in xrange(len(btstart)):
        # beat start time and end time in seconds
        start = btstart[n]
        end = start + btlen[n]
        # np.nonzero returns index of nonzero elems
        # find first segment that starts after beat starts - 1
        try:
            start_idx = np.nonzero((segstart - start) >= 0)[0][0] - 1
        except IndexError:
            # no segment start after that beats, can happen close
            # to the end, simply ignore, maybe even break?
            continue
        # find first segment that starts after beat ends
        try:
            end_idx = np.nonzero((segstart - end) >= 0)[0][0]
        except IndexError:
            end_idx = start_idx
        # fill col of warpmat with 1 for the elem in between
        # (including start_idx, excluding end_idx)
        warpmat[start_idx:end_idx, n] = 1
        
        # if the beat started after the segment, keep the proportion
        # of the segment that is inside the beat
        warpmat[start_idx, n] = 1. - ((start - segstart[start_idx])
                                 / seglen[start_idx])
        # if the segment ended after the beat ended, keep the proportion
        # of the segment that is inside the beat
        if end_idx - 1 > start_idx:
            warpmat[end_idx-1,n] = ((end - segstart[end_idx-1])
                                    / seglen[end_idx-1])
        # normalize so the 'energy' for one beat is one
        warpmat[:,n] /= np.sum(warpmat[:,n])

    # return the transpose, meaning (#beats , #segs)
    return warpmat.T



def pad_crop(data, newsize):
    """ set the data to the right size, columnwise, by either
    padding with zeros or cropping """
    if data.shape[1] == newsize:
        return data
    # data too small
    if data.shape[1] < newsize:
        res = np.zeros([12,newsize])
        res[:,:data.shape[1]] = data
        return res
    # data too big
    else:
        return data[:,:newsize]
        

def resample(data, newsize):
    """ resample the data, columnwise """
    if newsize > 1:
        return SP.signal.resample(data, newsize, axis=1)
    # special case, newsize == 1
    if newsize == 1 and data.shape[1] == 1:
        return data
    return np.mean(data,axis=1).reshape(data.shape[0],1)


def keyinvariance(pattern,retRoll=False):
    """
    Perform 'key invariance' per pattern.
    Important feature: the relative pitch of the events must be
    unchanged.
    We compute the row with the max energy, and we rotate so it
    row 0.
    If retRoll == True, we also return the roll. To get back
    the original pattern, apply -roll on axis=0
    """
    # find max row
    max_r = np.argmax(np.sum(pattern,axis=1))
    # roll
    if not retRoll:
        return np.roll(pattern,pattern.shape[0]-max_r,axis=0)
    roll = pattern.shape[0]-max_r
    return np.roll(pattern,roll,axis=0),roll
