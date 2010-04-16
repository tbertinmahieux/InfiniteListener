"""
Code to analyze a set of experiments and automatically plot the
curves, and saves the data
"""

import os
import sys
import glob
import pickle
import numpy as np















def die_with_usage():
    """
    HELP MENU
    """
    print 'usage:'
    print 'python plot_bitdistrate_curves.py <valid dir> <test dir> <output> <exp1> .... <expN>'
    print 'PARAMS:'
    print ' <valid dir>    contains matfiles of validation set'
    print '  <test dir>    contains matfiles of test set'
    print '    <output>    filename to text file, something like results.txt'
    print '     <exp..>    path to experiment folder, "set2exp12" for instance'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    
