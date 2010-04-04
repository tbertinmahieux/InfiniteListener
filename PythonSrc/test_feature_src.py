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
    tmpfilemat = os.path.abspath(sys.argv[1])
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
    
    # feature from matfile
    mat_feats = features.features_from_matfile(tmpfilemat,pSize=8,usebars=2,
                                               keyInv=True,songKeyInv=False,
                                               positive=True,do_resample=True)
    mat_feats = mat_feats[np.nonzero(np.sum(mat_feats,axis=1))]
    print 'features from matfile computed, shape =',mat_feats.shape

    # compare
    min_len = min(mat_feats.shape[0],online_feats.shape[0])
    if mat_feats.shape != online_feats:
        print 'wrong shape...'
    if (mat_feats[:min_len,:] == online_feats[:min_len,:]).all():
        print 'ALL GOOD, identical features'
    else:
        print 'PROBLEM, features differ'
