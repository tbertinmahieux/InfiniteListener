"""
T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu

Code to encode a song using many dictionaries, usually with different
beat sizes, using dynamic programming.
"""

import sys
import os
import glob
import numpy as np
import scipy
import scipy.io as SIO


class dict_lib():
    """
    A class that simply contains a set of dictionaries.
    A dictionary is a numpy 2d array, one codeword per line.
    Usefull to pass around.
    """

    def __init__(self):
        """ Constructor, inits dictionary list """
        self._dicts = []

    def add_dict(self,d):
        """ add a dictionary """
        # add to the list
        self._dicts.append(d)
        # sort dicts by beat size (primary) and # codes (secondary)
        self._dicts = sorted(self._dicts, key=lambda d : d.shape[0]) # secondary
        self._dicts = sorted(self._dicts, key=lambda d : d.shape[1]) # primary

    def __str__(self):
        """ string representation of the object """
        s = "dict_lib contains " + str(len(self._dicts)) + " dictionaries:\n"
        for d in self:
            s += str(d.shape[1]/12) + " beats - "
            s += str(d.shape[0]) + " codewords\n"
        return s

    def __size__(self):
        """ returns the number of dictionaries"""
        return len(self._dicts)

    def __iter__(self):
        """ init iterations """
        self._iterpos = 0
        return self
        
    def next(self):
        """ returns the next dictionary """
        if self._iterpos >= len(self._dicts):
            raise StopIteration
        self._iterpos += 1
        return self._dicts[self._iterpos - 1]



def load_dict_dir(dirpath,dictlib=None):
    """
    Loads all dictionaries in the dir in a dict_lib instance.
    Dictionaries are assumed to be all matfiles in the dir,
    key is 'codebook'
    """
    # init dict_lib instance if necessary
    if not dictlib:
        dictlib = dict_lib()
    # find all matfiles
    matfiles = glob.glob(os.path.join(dirpath,'*.mat'))
    # load them all, add them
    for f in matfiles:
        mat = SIO.loadmat(f)
        cb = mat['codebook']
        dictlib.add_dict(cb)
    # done, return dict_lib instance
    return dictlib

    
def die_with_usage():
    """ HELP MENU. """
    print 'python multidict_encode.py -dictdir <dir> <song beat feats>'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # flags
    dictlib = None
    while True:
        if len(sys.argv) < 2:
            break
        if sys.argv[1] == '-dictdir':
            dictlib = load_dict_dir(sys.argv[2],dictlib=dictlib)
            sys.argv.pop(1)
        else:
            break
        sys.argv.pop(1)

    # print dictlib info
    print dictlib

            
