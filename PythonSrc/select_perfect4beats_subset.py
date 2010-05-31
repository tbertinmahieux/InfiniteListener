"""
Code to select songs that are made of regular 4 beats bars according
to the EchoNest.
This should improve the analysis.
"""


import sys
import os
import scipy
import scipy.io
import numpy as np
import oracle_matfiles as ORACLE
import shutil



def is_perfect_4(path):
    """
    Returns True if the path is a matfile representing a song in with perfect
    4 beats bars
    Real job done here!
    """
    assert(path[-4:]=='.mat','path should be a MATFILE')
    # load matfile
    mat = scipy.io.loadmat(path)
    # get bars in term of beats
    barbts = mat['barbts']
    # test diff
    if (np.diff(barbts) == 4).all():
        return True
    return False


def find_all_songs(startdir):
    """
    Find all songs that are perfect 4s, return a list of path.
    """
    # find all matfiles
    allfiles = ORACLE.get_all_matfiles(startdir)
    # for each song, check perfect 4
    goodfiles = filter(lambda x: is_perfect_4(x),allfiles)
    # done, return
    return goodfiles,allfiles


def die_with_usage():
    """ HELP MENU """
    print 'to select songs that are made of perfect 4 beats bars'
    print 'usage:'
    print '   python select_perfect4beats_subset.py [FLAGS] <original dir> <new dir>'
    print 'FLAGS'
    print '  -dryrun    simply tells the number of songs that fit'
    sys.exit(0)



if __name__ == '__main__' :

    # help menu
    if len(sys.argv) < 3:
        die_with_usage()

    # flags
    dryrun = False
    while True:
        if sys.argv[1] == '-dryrun':
            dryrun = True
            print 'doing dry run'
        else:
            break
        sys.argv.pop(1)

    # params
    startdir = sys.argv[1]
    print 'looking at songs in dir:',startdir
    if not dryrun:
        newdir = sys.argv[2]
        print 'copying them to dir:',newdir
        
    # get list of perfect 4 files
    goodfiles,allfiles = find_all_songs(startdir)

    # dryrun?
    if dryrun:
        print 'found',len(goodfiles),' appropriate files out of',len(allfiles)
        sys.exit(0)

    # copying them, preserving the relative naming
    print 'copying files...'
    for f in goodfiles:
        relf = os.path.relpath(f,start=startdir)
        newf = os.path.join(newdir,relf)
        # copy file
        shutil(f,newf)
    print 'done'
