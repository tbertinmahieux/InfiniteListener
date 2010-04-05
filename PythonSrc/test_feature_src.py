"""
Simple code to test that we get exactly the same patterns
if we take them form matfiles (BostonHackDay project) or
directly from the EchoNest

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import numpy as np
import string
import tempfile
import features
import tzanetakis_utils as TZAN
import en_extras as EXTRAS
import pylab as P
from plottools import *
# echonest stuff
from pyechonest import config
from pyechonest import track as trackEN
try:
    config.ECHO_NEST_API_KEY = os.environ['ECHONEST_API_KEY']
except:
    config.ECHO_NEST_API_KEY = os.environ['ECHO_NEST_API_KEY']






def die_with_usage():
    """
    HELP MENU
    """
    print 'python test_feature_src.py song.mp3 tmpfilemat'
    sys.exit(0)
    

if __name__ == '__main__':

    if len(sys.argv) < 3:
        die_with_usage()


    # songfile
    songfile = os.path.abspath(sys.argv[1])
    tmpfilemat = os.path.abspath(sys.argv[2])
    if tmpfilemat[-4:] != '.mat':
        tmpfilemat += '.mat'

    # first encode song with tzanetakis code from HackDay
    TZAN.filename_to_beatfeat_mat(songfile,tmpfilemat)
    print 'song encoded to matfile'

    # then retrieve stuff from EchoNest
    track = trackEN.upload(songfile)
    identifier = string.split(track.identifier,'/')[-1]
    print 'EN identifier =',identifier
    a,b,c,d,e = EXTRAS.get_our_analysis(identifier)
    segstart, chromas, beatstart, barstart, duration = a,b,c,d,e
    analysis_dict = {'segstart':segstart,'chromas':chromas,
                     'beatstart':beatstart,'barstart':barstart,
                     'duration':duration}
    print 'analysis retrieved from Echo Nest'

    # features from online
    online_feats = features.get_features(analysis_dict,pSize=8,usebars=2,
                                         keyInv=True,songKeyInv=False,
                                         positive=True,do_resample=True,
                                         btchroma_barbts=None)
    online_feats = online_feats[np.nonzero(np.sum(online_feats,axis=1))]
    print 'features from online computed, shape =',online_feats.shape

    # retrieve feature using TZAN and compare to what we got
    """
    print 'comparing features from upload and online'
    a,b,c,d,e =  TZAN.get_en_feats(songfile)
    pitches, seg_start, beat_start, bar_start, duration = a,b,c,d,e
    print'number of segments (upload/online):',np.array(seg_start).shape,',',np.array(analysis_dict['segstart']).shape
    a = np.array(seg_start)
    b = np.array(analysis_dict['segstart'])
    assert a.shape == b.shape
    a - b
    assert np.max(np.array(seg_start).flatten()-np.array(analysis_dict['segstart']).flatten()) < .01
    assert np.max(np.array(beat_start).flatten()-np.array(analysis_dict['beatstart']).flatten()) < .01
    assert np.max(np.array(bar_start).flatten()-np.array(analysis_dict['barstart']).flatten()) < .01
    assert duration == analysis_dict['duration']
    assert pitches == analysis_dict['chromas']
    print 'got same feature by upload than by calling using track ID'
    """

    
    # feature from matfile
    mat_feats = features.features_from_matfile(tmpfilemat,pSize=8,usebars=2,
                                               keyInv=True,songKeyInv=False,
                                               positive=True,do_resample=True)
    mat_feats = mat_feats[np.nonzero(np.sum(mat_feats,axis=1))]
    print 'features from matfile computed, shape =',mat_feats.shape

    # features from matfile old school
    import data_iterator
    import feats_utils as FU
    data_iter = data_iterator.DataIterator()
    data_iter.setMatfiles([tmpfilemat])
    data_iter.useBars(2)
    data_iter.stopAfterOnePass(True)
    featsNorm = [FU.normalize_pattern_maxenergy(p,8,True,False).flatten() for p in data_iter]
    featsNorm = np.array(featsNorm)
    res = [np.sum(r) > 0 for r in featsNorm]
    res2 = np.where(res)
    featsNorm = featsNorm[res2]
    print 'features from matfile (old school) computed, shape =',featsNorm.shape
    
    # compare
    min_len = min(mat_feats.shape[0],online_feats.shape[0],featsNorm.shape[0])
    if mat_feats.shape != online_feats:
        print 'wrong shape...'

    # plot matfile features
    P.figure()
    plotall([x.reshape(12,mat_feats.shape[1]/12) for x in mat_feats[:3]],
            interpolation='nearest',aspect='auto',cmap=P.cm.gray_r,
            subplot=(1,3),colorbar=False)
    P.title('mat feats')
    # plot online features
    P.figure()
    plotall([x.reshape(12,online_feats.shape[1]/12) for x in online_feats[:3]],
            interpolation='nearest',aspect='auto',cmap=P.cm.gray_r,
            subplot=(1,3),colorbar=False)
    P.title('online feats')
    # plot matfile features old school
    P.figure()
    plotall([x.reshape(12,featsNorm.shape[1]/12) for x in featsNorm[:3]],
            interpolation='nearest',aspect='auto',cmap=P.cm.gray_r,
            subplot=(1,3),colorbar=False)
    P.title('mat feats old school')
    P.show()

    if (mat_feats[:min_len,:] == featsNorm[:min_len,:]).all():
        print 'ALL GOOD, identical feats between old school and new mat feats'
    else:
        print 'PROBLEM, features differ'


    # matfiles and online feats fit
    if (mat_feats[:min_len,:] == online_feats[:min_len,:]).all():
        print 'ALL GOOD, identical features between mat and online feats'
    else:
        print 'PROBLEM, features differ'