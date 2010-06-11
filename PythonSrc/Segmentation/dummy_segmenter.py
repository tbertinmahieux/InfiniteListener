"""
Set of 'stupid' segmenter to try to get a better benchmark
value
"""

import os
import sys
import glob
import numpy as np

import measures as MEASURES


def get_all_files(basedir,pattern='*') :
    """
    From a root directory, go through all subdirectories
    and find all files that fit the pattern.
    Example: *.mat, *.lab, allo*.txt, etc
    Return them in a list.
    """
    allfiles = []
    for root, dirs, files in os.walk(basedir):
        matfiles = glob.glob(os.path.join(root,pattern))
        for f in matfiles :
            allfiles.append( os.path.abspath(f) )
    return allfiles



def read_lab_file(fnIn):
    """
    Read a segmentation file, based on EN beats
    RETURN
    startbeats, stopbeats, labels
    """
    startbeats = []
    stopbeats = []
    labels = []
    # open file, iterate over lines, close file
    f = open(fnIn,'r')
    for line in f.readlines():
        if line == "" or line.strip() == "":
            continue
        line = line.strip()
        stubs = filter(lambda x: x != "", line.split('\t'))
        assert len(stubs) >= 3, 'weird line'
        startbeats.append( int (stubs[0]) )
        stopbeats.append( int (stubs[1]) )
        labels.append( stubs[2] )
    f.close()
    # done, return
    return startbeats, stopbeats, labels


def typical_splits(basedir):
    """
    Read all lab files.
    Find the most common number of segments.
    For that number, find the average proportion of each
    segment.
    Apply it to every song.
    """
    # get all lab files
    labfiles = get_all_files(basedir,pattern='*.lab')
    # find the typical number of segments
    hist_nsegs = np.zeros(2000)
    for f in labfiles:
        startbs,stopbs,labels = read_lab_file(f)
        hist_nsegs[ len(startbs) ] += 1
    # most common number of segments
    common_nsegs = np.argmax(hist_nsegs)
    print 'most common number of segments:',common_nsegs
    # for that number, find typical proportion
    proportions = np.zeros(common_nsegs)
    count_common_segmentation = 0
    for f in labfiles:
        startbs,stopbs,labels = read_lab_file(f)
        if len(startbs) != common_nsegs:
            continue
        count_common_segmentation += 1
        nbeats = stopbs[-1] + 1
        diffs = np.diff(startbs + [nbeats])
        for k in range(common_nsegs):
            proportions[k] += diffs[k] * 1. / nbeats
    for k in range(common_nsegs):
        proportions[k] *= 1. / count_common_segmentation
    # our typical proportions are:
    print 'typical proportions:',proportions
    # test on all lab files
    allprec = 0
    allrec = 0
    allf = 0
    allSo = 0
    allSu = 0
    for f in labfiles:
        startbs,stopbs,labels = read_lab_file(f)
        # get ideal fake segmentation
        nbeats = stopbs[-1]+1
        nbeats_per_seg = np.zeros(common_nsegs)
        for k in range(common_nsegs):
            nbeats_per_seg[k] = nbeats * proportions[k]
        # adjust so it fits the number of beats
        while np.sum(nbeats_per_seg) > nbeats:
            nbeats_per_seg[ np.argmax(nbeats_per_seg) ] -= 1
        while np.sum(nbeats_per_seg) < nbeats:
            nbeats_per_seg[ np.argmax(nbeats_per_seg) ] += 1
        # create corresponding startbs and stopbs
        startbscand = np.zeros(common_nsegs)
        startbscand[0] = 0
        for k in range(1,common_nsegs):
            startbscand[k] = startbscand[k-1] + nbeats_per_seg[k-1]
        startbscand = list(startbscand)
        stopbscand = startbscand[1:] + [nbeats-1]
        # measure
        prec,rec,f,So,Su = MEASURES.prec_rec_f_So_Su(startbs,stopbs,
                                                     startbscand,
                                                     stopbscand)
        allprec += prec
        allrec += rec
        allf += f
        allSo += So
        allSu += Su

    # done, average
    allprec *= 1./len(labfiles)
    allrec *= 1./len(labfiles)
    allf *= 1./len(labfiles)
    allSo *= 1./len(labfiles)
    allSu *= 1./len(labfiles)
    # print
    print 'average prec =',allprec,', rec =',allrec,', f =',allf,', So =',allSo,', Su =',allSu
