"""
Code to parse a folder of saved model and trim the unimportant one.
Use heuristics to do so.
Never remove a folder part of the traceback of the most recent
saved model.
Never remove saved models from the initial first 2 hours.
Keep a maximum of one model per hour after that.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import glob
import numpy as np

import analyze_saved_model as ANALYZE
from trainer import StatLog

def is_in_path_set(p,pathset):
    """
    Check if a given path is in a set of paths. Returns True if it is the
    case, False otherwise.
    """
    p_is_in = False
    for p2 in pathset:
        if os.path.samefile(p,p2):
            p_is_in = True
            break
    return p_is_in


def die_with_usage():
    """
    HELP MENU
    """
    print 'Removed non essential saved models'
    print 'usage:'
    print '  python trim_savedmodels_dir.py [FLAGS] <last saved model>'
    print 'ARGS'
    print ' <last saved model>   most recent saved model'
    print '                      here we trim its parent directory!'
    print 'FLAGS'
    print '  -dryrun     prints all folders to remove, do not actually do it'
    sys.exit(0)


# MAIN
if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # flags
    dryrun = True # debug, change to False
    while True:
        if sys.argv[1] == '-dryrun':
            print 'we do a dry run, nothing will be deleted'
            dryrun = True
        else:
            break
        sys.argv.pop(1)

    # last saved model
    savedmodel = os.path.abspath(sys.argv[1])
    trimdir = os.path.dirname(savedmodel)
    print 'most recent saved model:',savedmodel
    print 'directory to trim:',trimdir

    # get traceback
    traceback = ANALYZE.traceback(savedmodel)
    traceback = np.sort(traceback)
    print '*********** TRACEBACK *************'
    for k in traceback:
        print k
    print '***********************************'
    # keep only folders
    traceback = filter(lambda x: os.path.isdir(x), traceback)

    # get all dirs in trimdir, in order
    all_in_folder = glob.glob(os.path.join(trimdir,'*'))
    all_in_folder = filter(lambda x: os.path.isdir(x), all_in_folder)
    all_in_folder = np.sort(all_in_folder)
    print 'number of folders found in main folder:',len(all_in_folder)

    # go through them, add some to the 'remove set'
    to_delete = []
    first_time = ANALYZE.stop_time(traceback[0])
    current_time = first_time
    # iterate over directories in trimdir
    for d in all_in_folder:
        # if part of traceback, adjust current time and move on
        if is_in_path_set(d,traceback):
            current_time = ANALYZE.stop_time(d)
            continue
        # get stop time for dir
        try:
            stop_time = ANALYZE.stop_time(d)
        except ValueError:
            # not a savedmodel dir? ignore
            print 'ignoring directory:',d
            continue
        # less than two hours? keep safe
        if stop_time - first_time < 60 * 60 * 2:
            print 'stop time:', stop_time
            print 'first time:',first_time
            assert stop_time - first_time >= 0,'did not start from most recent saved model?'
            continue
        # otherwise
        if stop_time - current_time < 60 * 60:
            assert stop_time - current_time >= 0,'did not start from most recent saved model?'
            # less than an hour from most recent one? delete
            to_delete.append(d)
        else:
            # set current time
            current_time = stop_time
            continue

    # print files to be removed
    print '*********** TO REMOVE *************'
    for k in to_delete:
        print k
    print '***********************************'


    # if not dry run, remove


