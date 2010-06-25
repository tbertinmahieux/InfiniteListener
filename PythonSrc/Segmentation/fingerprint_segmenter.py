"""
Try to do segmentation based on a similarity matrix and
fingerprint features (maximums)

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import copy
import scipy.io as sio
import numpy as np
import math

import dummy_segmenter as DUMMY
from fingerprint import get_landmarks as LANDMARKS
rondir = 'ronwsiplca'
from ronwsiplca import segmenter as SEGMENTER
mlab = LANDMARKS.mlab
mlab.addpath(os.path.abspath(rondir))
assert os.path.exists(os.path.join(rondir,'coversongs')),'coversongs directory not found'
mlab.addpath( os.path.abspath(os.path.join(rondir, 'coversongs/') ))
import measures as MEASURES

_enfeats_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_enbeatfeats')
_audio_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_audio')
_seglab_dir = os.path.expanduser('~/Columbia/InfiniteListener/beatles_seglab')

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
        submaxes[0,:] = np.array(maxessecs)[m_idxs] - ((bstop + bstart) * .5)
        res.append(submaxes)
    # done, return res
    assert len(res) == btstart.shape[1],'wrong number of feats per beat'
    return res


def dist_avg_closest_pair(feats1,feats2,alpha=10):
    """
    Distance measure between two sets of fingerprint maxes
    feats is a 2xN matrix
    first row - time in seconds, usually starting from the beat
    second row - frequency, usually a row index
    Computes euclidean distance between feats1 and their closest
    point in feats2, samething reverse, average
    alpha is a multiplier of the seconds
    """
    # special cases with no maxes
    if feats1.shape[1] == 0 and feats2.shape[1] == 0:
        return 0
    if feats1.shape[1] == 0 and feats2.shape[1] > 0:
        return np.inf # we'll find better
        #return 250. / 100 * feats2.shape[1]
    if feats1.shape[1] > 0 and feats2.shape[1] == 0:
        return np.inf # we'll find better
        #return 250. / 100 * feats1.shape[1]
    # compute distance from each of the points in a N x M matrix
    distmat = np.zeros([feats1.shape[1],feats2.shape[1]])
    for l in range(distmat.shape[0]):
        for c in range(distmat.shape[1]):
            distmat[l,c] = math.hypot(alpha*(feats1[0,l]-feats2[0,c]),
                                      feats1[1,l]-feats2[1,c])
    # measure closest ones
    shortest_from_feats1 = map(lambda x: np.min(distmat[x,:]),range(feats1.shape[1]))
    shortest_from_feats2 = map(lambda x: np.min(distmat[:,x]),range(feats2.shape[1]))
    # return average of both
    return np.min([np.average(shortest_from_feats1),
                   np.average(shortest_from_feats2)])



def build_simmat(beatfeats,dist=dist_avg_closest_pair):
    """
    build a similarity matrix based on fingerprint features per beat
    """
    nbeats = len(beatfeats)
    simmat = np.zeros([nbeats,nbeats])
    # fill it
    for k1 in range(nbeats):
        for k2 in range(k1,nbeats):
            simmat[k1,k2] = dist(beatfeats[k1],beatfeats[k2])
            simmat[k2,k1] = simmat[k1,k2]
    # remove infinites, replace them by max value non infinite we have
    allvals_noninf = filter(lambda x: x < np.inf, simmat.flatten())
    maxval = np.max(allvals_noninf)
    for k1 in range(nbeats):
        for k2 in range(k1,nbeats):
            if np.isinf(simmat[k1,k2]):
                simmat[k1,k2] = maxval
                simmat[k2,k1] = maxval
    # done, return simmatrix
    return simmat


def plot_simmat(simmat,labfile=''):
    """
    Plot a similarity matrix
    """
    # postprocess simmat
    simmat2 = copy.deepcopy(simmat)
    if False:
        allvals = np.sort(simmat2.flatten())
        medianval = allvals[int(allvals.shape[0]/2)]
        simmat2[np.where(simmat2>medianval)] = medianval
    # plot
    import pylab as P
    P.figure()
    args2 = {'interpolation':'nearest','cmap':P.cm.gray,'aspect':'auto'}
    P.imshow(simmat2,**args2)
    P.colorbar()
    P.hold(True)
    # we have labfile?
    if labfile != '':
        startbeats,stopbeats,labels = DUMMY.read_lab_file(labfile)
        for sb in startbeats:
            pos = sb
            assert pos <= simmat.shape[1],'wrong pos for lab data'
            point_size = 30
            P.scatter(pos,pos,s=point_size,c='r',marker='o')
            P.scatter(pos,0,s=point_size,c='r',marker='o')
            P.scatter(0,pos,s=point_size,c='r',marker='o')
    P.hold(False)
    # diff
    simmat_diff = np.diff(simmat2)
    P.figure()
    args2 = {'interpolation':'nearest','cmap':P.cm.gray,'aspect':'auto'}
    P.imshow(simmat_diff,**args2)
    P.colorbar()
    P.hold(True)
    # we have labfile?
    if labfile != '':
        startbeats,stopbeats,labels = DUMMY.read_lab_file(labfile)
        for sb in startbeats:
            pos = sb - 1
            assert pos <= simmat.shape[1],'wrong pos for lab data'
            point_size = 30
            P.scatter(pos,pos,s=point_size,c='r',marker='o')
            P.scatter(pos,0,s=point_size,c='r',marker='o')
            P.scatter(0,pos,s=point_size,c='r',marker='o')
    P.hold(False)
    # show
    P.show()


def plot_nearby_diff(beatfeats,labfile='',dist=dist_avg_closest_pair):
    """
    plot difference between nearby beats
    """
    dists = map(lambda k: dist(beatfeats[k-1],beatfeats[k+1]),range(1,len(beatfeats)-1))
    # plot
    import pylab as P
    P.plot(dists)
    P.hold(True)
    if labfile != '':
        startbeats,stopbeats,labels = DUMMY.read_lab_file(labfile)
        for sb in startbeats:
            pos = sb 
            point_size = 30
            P.scatter(pos,0,s=point_size,c='r',marker='o')
    P.hold(False)
    P.show()

def plot_maxes_beats_segs(maxes,maxessecs,btstart,labfile=''):
    """
    Plot the maxes for the whole songs, indicates beats and segs
    """
    import pylab as P
    P.figure()
    P.hold(True)
    P.scatter(maxessecs,list(maxes[1,:]),c='b')
    #for bs in list(btstart.flatten()):
    #    P.axvline(x=bs,color='r')
    if labfile != '':
        startbeats,stopbeats,labels = DUMMY.read_lab_file(labfile)
        for sb in startbeats:
            pos = btstart[0,sb]
            P.axvline(x=pos,color='g')
    P.hold(False)
    P.show()
    


def siplca_method(wavfile,rank=4,win=60,plotiter=10,printiter=10,niter=200,fullspec=False):
    """
    Compute beats using Dan's code
    Get the fingerprints
    Align landmarks with the beats
    Run SIPLCA method
    Measure errors
    """
    # compute beats
    print 'compute beats'
    x,fs = mlab.wavread(wavfile,nout=2)
    x = np.average(x,axis=1)
    assert x.shape[0] > 2,'bad signal averaging'
    feats,beats = mlab.chrombeatftrs(x,fs,400,1,1,nout=2)
    # get the fingerprints
    print 'compute landmarks,',beats.shape[1],'beats found'
    L,S,T,maxes = LANDMARKS.find_landmarks_from_wav(wavfile)
    # LANDMARKS
    if not fullspec:
        # transform them into per beats features
        maxessecs = get_actual_times(maxes)
        print 'get features per beat,',len(maxessecs),'landmarks found'
        beatfeats = get_fingerprint_feats_per_beat(beats,np.max(maxessecs)+.1,
                                                   maxes,maxessecs)
        databeat = np.zeros([256,len(beatfeats)])
        for bf_idx in range(len(beatfeats)):
            bf = beatfeats[bf_idx]
            if bf.shape[1] == 0:
                continue
            for k in range(bf.shape[1]):
                databeat[int(bf[1,k]-1),bf_idx] += 1
        print 'number of empty rows:',np.shape(np.where(databeat.sum(1)==0))[1],', removed...'
        databeat = databeat[np.where(databeat.sum(1)>0)[0],:]
    # FULL SPECTROGRAM
    else:
        # get time for each pos of the spectrogram, then beat for each pos
        fakemaxes = np.zeros([2,S.shape[1]])
        fakemaxes[0,:] = np.array(range(S.shape[1])).reshape(1,S.shape[1])
        times = get_actual_times(fakemaxes)
        # fill in databeat
        #beats = np.array(beats)[0]
        databeat = np.zeros([S.shape[0],beats.shape[1]])
        for k in range(S.shape[1]):
            t = times[k]
            bs = np.where(np.array(beats)[0] > t)[0]
            if bs.shape[0] == 0: # last beat
                b = databeat.shape[1] - 1
            else:
                b = max(0,bs[0]-1)
            databeat[:,b] += np.exp(S[:,k]) # remove the log for NMF
        databeat -= databeat.min()
        print 'full spec, max value:',databeat.max(),', shape =',databeat.shape
    # launch siplca,
    databeat += 1e-16
    print 'launch siplca on',wavfile,', databeat.shape=',databeat.shape
    np.random.seed(123)
    V = databeat.copy()
    V/=V.sum()
    labels, W, Z, H, segfun, norm= SEGMENTER.segment_song(V, rank=rank,win=win,
                                                          plotiter=plotiter,
                                                          printiter=printiter,
                                                          niter=niter)
    #res = SEGMENTER.convert_labels_to_segments(labels, beats[0])
    # transform labels output to actuall startbeat and stopbeat
    startbeats = [0]
    stopbeats = []
    currlabel = labels[0]
    for k in range(1,len(labels)):
        if labels[k] != currlabel:
            currlabel = labels[k]
            startbeats.append(k)
            stopbeats.append(k-1)
    stopbeats.append(len(labels)-1)
    # get groundtruth
    relwavfile = os.path.relpath(wavfile,start=_audio_dir)
    labfile = os.path.join(_seglab_dir,relwavfile[:-4]+'.lab')
    segstarts = []
    fIn = open(labfile,'r')
    for line in fIn.readlines():
        if line == '' or line.strip() == '':
            continue
        segstarts.append( float(line.strip().split('\t')[0]) )
    fIn.close()
    refstartbeats = []
    for ss in segstarts: # slow...!
        for k in range(beats.shape[1]-1):
            if beats[0,k] <= ss and beats[0,k+1] > ss:
                refstartbeats.append(k)
                break
        if ss > beats[0,-1]:
            refstartbeats.append(beats.shape[1]-1)
        elif ss < beats[0,0]:
            refstartbeats.append(0)
    refstartbeats = list(np.unique(refstartbeats))
    refstopbeats = list(np.array(refstartbeats[1:]) - 1) + [beats.shape[1]-1]
    # measure error
    prec,rec,f,So,Su = MEASURES.prec_rec_f_So_Su(refstartbeats,
                                                 refstopbeats,
                                                 startbeats,
                                                 stopbeats)
    print 'prec =',prec,', rec =',rec,', f =',f,', So =',So,', Su =',Su
    return prec,rec,f,So,Su


def siplca_testalldata(datadir,resfile,fullspec=False):
    """
    Test the whole Beatles dataset using siplca method
    """
    allwavs = DUMMY.get_all_files(datadir,pattern='*.wav')
    allwavs = map(lambda x: os.path.abspath(x), allwavs)
    np.random.shuffle(allwavs)
    print len(allwavs),'wavfiles found'
    if not os.path.exists(resfile):
        fOut = open(resfile,'w')
        fOut.close()
    # iterate over wavs
    for wavfile in allwavs:
        # check if result exists
        isdone = False
        fIn = open(resfile,'r')
        for line in fIn.readlines():
            if line == '' or line.strip() == '':
                continue
            if line.strip().split("\t")[0] == wavfile:
                isdone = True
                break
        fIn.close()
        # do file
        if not isdone:
            try:
                prec,rec,f,So,Su = siplca_method(wavfile,fullspec=fullspec)
            except ValueError, msg:
                print 'siplca ValueError:',msg
                print 'skipping song',wavfile
                continue
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                print 'unexpected error:',sys.exc_info()[0]
                print 'skipping song',wavfile
                continue
            # write to resfile
            fOut = open(resfile,'a')
            fOut.write(wavfile + '\t' + str(prec) + '\t' + str(rec) +'\t')
            fOut.write(str(f) + '\t' + str(So) + '\t' + str(Su) + '\n')
            fOut.close()
    # all files done, report results
    allprec = 0
    allrec = 0
    allf = 0
    allSo = 0
    allSu = 0
    cnt = 0
    fIn = open(resfile,'r')
    for line in fIn.readlines():
        if line == '' or line.strip() == '':
            continue
        results = line.strip().split("\t")
        allprec += float(results[1])
        allrec += float(results[2])
        allf += float(results[3])
        allSo += float(results[4])
        allSu += float(results[5])
        cnt += 1.
    fIn.close()
    allprec /= cnt
    allrec /= cnt
    allf /= cnt
    allSo /= cnt
    allSu /= cnt
    print 'average prec =',allprec,', rec =',allrec,', f =',allf,', So =',allSo,', Su =',allSu    


def die_with_usage():
    """ HELP MENU """
    print 'functions to do segmentation with fingerprint features'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # DEBUGGING
    wavfile = sys.argv[1]
    sig,sr,maxes,btstart,dur,segstart,labels = maxes_beattimes_segs_from_audiofile(wavfile)
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
    # get sim matrix
    #simmat = build_simmat(feats_per_beat)

    # plot it
    print 'we plot the sim matrix'
    relwavfile = os.path.relpath(wavfile,start=_audio_dir)
    enmatfile = os.path.join(_enfeats_dir,relwavfile+'.mat')
    labfile = enmatfile + '.lab'
    #plot_simmat(simmat,labfile=labfile)
    #plot_nearby_diff(feats_per_beat,labfile=labfile)
    plot_maxes_beats_segs(maxes,maxessecs,btstart,labfile=labfile)
