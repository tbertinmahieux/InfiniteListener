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
    if os.path.isfile(tmpfilemat):
        os.remove(tmpfilemat)

    # first encode song with tzanetakis code from HackDay
    TZAN.filename_to_beatfeat_mat(songfile,savefile=tmpfilemat)
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
    del a,b,c,d,e,segstart,chromas,beatstart,barstart,duration
    print 'analysis retrieved from Echo Nest'

    # features from online (positive=False to compare with old school method)
    online_feats = features.get_features(analysis_dict,pSize=8,usebars=2,
                                         keyInv=True,songKeyInv=False,
                                         positive=False,do_resample=True,
                                         btchroma_barbts=None)
    online_feats = online_feats[np.nonzero(np.sum(online_feats,axis=1))]
    print 'features from online computed, shape =',online_feats.shape

    # retrieve feature using TZAN and compare to what we got
    print 'comparing features from upload and online'
    print 'reuploading songfile =',songfile
    a,b,c,d,e =  TZAN.get_en_feats(songfile)
    pitches, seg_start, beat_start, bar_start, duration = a,b,c,d,e
    print'number of segments (upload/online):',np.array(seg_start).shape,',',np.array(analysis_dict['segstart']).shape
    a = np.array(seg_start)
    b = np.array(analysis_dict['segstart'])
    assert a.shape == b.shape
    a - b
    assert np.abs(np.array(seg_start).flatten()-np.array(analysis_dict['segstart']).flatten()).max() < .001
    assert np.abs(np.array(beat_start).flatten()-np.array(analysis_dict['beatstart']).flatten()).max() < .001
    assert np.abs(np.array(bar_start).flatten()-np.array(analysis_dict['barstart']).flatten()).max() < .001
    assert duration == analysis_dict['duration']
    assert np.abs(pitches - analysis_dict['chromas']).max() < .02
    print 'got same feature by upload than by calling using track ID, max chroma distance:',np.abs(pitches - analysis_dict['chromas']).max()


    # analysis_dict2
    analysis_dict2 = {'segstart':seg_start,'chromas':pitches,
                      'beatstart':beat_start,'barstart':bar_start,
                      'duration':duration}
    tzan_feats = features.get_features(analysis_dict2,pSize=8,usebars=2,
                                       keyInv=True,songKeyInv=False,
                                       positive=False,do_resample=True,
                                       btchroma_barbts=None)
    tzan_feats = tzan_feats[np.nonzero(np.sum(tzan_feats,axis=1))]
    print 'features from tzan data computed, shape =',tzan_feats.shape
    
    # feature from matfile
    mat_feats = features.features_from_matfile(tmpfilemat,pSize=8,usebars=2,
                                               keyInv=True,songKeyInv=False,
                                               positive=False,do_resample=True)
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
    if mat_feats.shape != online_feats.shape:
        print 'wrong shape between online and mat feats...'

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
    # plot tzan features
    P.figure()
    plotall([x.reshape(12,tzan_feats.shape[1]/12) for x in tzan_feats[:3]],
            interpolation='nearest',aspect='auto',cmap=P.cm.gray_r,
            subplot=(1,3),colorbar=False)
    P.title('tzan feats')
    # plot matfile features old school
    P.figure()
    plotall([x.reshape(12,featsNorm.shape[1]/12) for x in featsNorm[:3]],
            interpolation='nearest',aspect='auto',cmap=P.cm.gray_r,
            subplot=(1,3),colorbar=False)
    P.title('mat feats old school')
    P.show()

    if (mat_feats[:min_len,:] - featsNorm[:min_len,:]).max() < .02:
        print 'GOOD, identical feats between old school and new mat feats'
    else:
        print 'PROBLEM, features differ between old school and new mat feats, max diff:',np.abs(mat_feats[:min_len,:] - featsNorm[:min_len,:]).max()


    # matfiles and online feats fit
    if np.abs(mat_feats[:min_len,:] - online_feats[:min_len,:]).max()< .02:
        print 'GOOD, identical features between mat and online feats'
    else:
        print 'PROBLEM, features differ between mat and online feats, max diff:',np.abs(mat_feats[:min_len,:] - online_feats[:min_len,:]).max()
