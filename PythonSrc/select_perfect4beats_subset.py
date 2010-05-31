"""
Code to select songs that are made of regular 4 beats bars according
to the EchoNest.
This should improve the analysis.
"""


import sys
import os
import os.path
import scipy
import scipy.io
import numpy as np
import oracle_matfiles as ORACLE
import shutil



def relpath(path, start=curdir):
    """
    Taken from source code in python 2.6
    Useful on boar (python 2.5)
    http://mail.python.org/pipermail/python-list/2009-August/1215220.html
    Return a relative version of a path
    """
    if not path:
        raise ValueError("no path specified")
    start_list = abspath(start).split(sep)
    path_list = abspath(path).split(sep)
    if start_list[0].lower() != path_list[0].lower():
        unc_path, rest = splitunc(path)
        unc_start, rest = splitunc(start)
        if bool(unc_path) ^ bool(unc_start):
            raise ValueError("Cannot mix UNC and non-UNC paths (%s and %s)" % (path, start))
        else:
            raise ValueError("path is on drive %s, start on drive %s" % (path_list[0],start_list[0]))
    # Work out how much of the filepath is shared by start and path.
    for i in range(min(len(start_list), len(path_list))):
        if start_list[i].lower() != path_list[i].lower():
            break
    else:
        i += 1

    rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return curdir
    return join(*rel_list)



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
    try:
        barbts = mat['barbts']
    except KeyError:
        print 'problem, no barbts in file:',path
        return False
    # test diff
    try:
        if (np.diff(barbts) == 4).all():
            return True
    except IndexError:
        #print 'problem, weird barbts in file:',path
        #print 'barbts = ',barbts
        pass
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
        try:
            relf = os.path.relpath(f,start=startdir)
        except AttributeError:
            relf = relpath(f,start=startdir)
        newf = os.path.join(newdir,relf)
        # copy file
        shutil(f,newf)
    print 'done'
