"""
T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu

Code to encode a song using many dictionaries, usually with different
beat sizes, using dynamic programming.
"""

import sys
import os
import numpy as np
import scipy
import scipy.io as SIO


class dict_lib():
    """
    A class that simply contains a set of dictionaries.
    A dictionary is a numpy 2d array, one codeword per line.
    Usefull to pass around.
    """
    
    def dict_lib(self):
        """ Constructor """
        self._dicts = []

    def add_dict(self,d):
        """ add a dictionary """
        # add to the list
        self._dicts.append(d)
        # sort by beat size (primary) and # codes (secondary)
        self._dicts = sorted(self._dicts, key=lambda x : x.shape[0]) # secondary
        self._dicts = sorted(self._dicts, key=lambda x : x.shape[1]) # primary

    def __str__(self):
        """ string representation of the object """
        s = "dict_lib contains " + len(self._dict) + " dictionaries:\n"
        for k in range(len(self._dict)):
            s += str(self._dict[k].shape[1]/12) + " beats - "
            s += str(self._dict[k].shape[0]) + " codewords\n"
        return s
    

def die_with_usage():
    """ HELP MENU. """
    print 'python multidict_encode.py -dictdir <dir> <song beat feats>'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()
