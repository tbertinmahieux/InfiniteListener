"""
Oracle to go get data from Matfiles.
Usefull to reproduces experiments from ISMIR 2010 paper
or initialize a codebook wth some downloaded data.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import time
import copy
import glob
import numpy as np
# features stuff
import features


# ORACLE CLASS

class OracleMatfiles:
    """
    Class to get EchoNest features
    """

    def __init__(self,params,folder,oneFullIter=False):
        """
        Constructor, get a folder name containing matfiles in any subdirectory.
        if oneFullIter is True, go through the data once (e.g. for testing)
        """
        # features stuff
        self._pSize = params['pSize']
        self._usebars = params['usebars']
        self._keyInv = params['keyInv']
        self._songKeyInv = params['songKeyInv']
        self._positive = params['positive']
        self._do_resample = params['do_resample']
        self._partialbar = 0
        if params.has_key('partialbar'):self._partialbar = params['partialbar']
        # find all matfiles
        self._matfiles = get_all_matfiles(folder)
        assert len(self._matfiles) > 0,'no matfiles found in %s'%folder
        # statistics
        self._nTracksGiven = 0
        # one iteration?
        self._oneFullIter = oneFullIter
        self._fileidx = 0
        # autobar
        self._autobar = None


    def next_track(self,auto_bar=None):
        """
        Returns features for a random matlab file, or None if some error.
        If only one iter over the data, raise StopIteration at the end.
        """
        # find next matfile
        if not self._oneFullIter:
            matfile = self._matfiles[np.random.randint(len(self._matfiles))]
        else:
            if self._fileidx >= len(self._matfiles):
                self._fileidx = 0 # for next time
                raise StopIteration
            matfile = self._matfiles[self._fileidx]
            self._fileidx += 1
        # return features
        if auto_bar == None:
            return features.features_from_matfile(matfile,
                                                  pSize=self._pSize,
                                                  usebars=self._usebars,
                                                  keyInv=self._keyInv,
                                                  songKeyInv=self._songKeyInv,
                                                  positive=self._positive,
                                                  do_resample=self._do_resample,
                                                  partialbar=self._partialbar)
        else:
            # we assume auto_bar contains a model
            # we predict on every offset, return features with the best offset based on the model
            best_dist = np.inf
            best_feats = None
            realSize = self._pSize
            if self._partialbar > 0:
                realSize = self._partialbar
            for offset in range(realSize):
                # get features
                feats = features.features_from_matfile(matfile,
                                                       pSize=self._pSize,
                                                       usebars=self._usebars,
                                                       keyInv=self._keyInv,
                                                       songKeyInv=self._songKeyInv,
                                                       positive=self._positive,
                                                       do_resample=self._do_resample,
                                                       partialbar=self._partialbar,
                                                       offset=offset)
                if feats == None:
                    continue
                # predicts
                tmp,avg_dist = auto_bar.predicts(feats)
                d = np.average(avg_dist)
                if d < best_dist:
                    best_dist = d
                    best_feats = feats
            # done, return best features
            return best_feats

    def use_autobar_in_iterator(self,model):
        """
        When we want a model to use the autobar function
        and the iterator syntax.
        By setting the model here, every time we call next, autobar
        is used with the given model.
        To change the model, call back this function.
        To stop that behavior, pass None as an argument.
        """
        self._autobar = model

    def tracksGiven(self):
        """
        Return the number of tracks given since the creation of
        ths instance.
        """
        return self._nTracksGiven


    def __iter__(self):
        """
        For iterator interface
        """
        return self

    def next(self):
        """
        For iterator interface
        Can be used only if oneFulliter is True
        """
        assert self._oneFullIter,'cant use this oracle as an iterator unless we do only one pass on the data, set oneFullIter=True at creation.'
        return self.next_track(auto_bar=self._autobar)



def get_all_matfiles(basedir) :
    """
    From a root directory, go through all subdirectories
    and find all matlab files. Return them in a list.
    """
    allfiles = []
    for root, dirs, files in os.walk(basedir):
        matfiles = glob.glob(os.path.join(root,'*.mat'))
        for f in matfiles :
            allfiles.append( os.path.abspath(f) )
    return allfiles


def die_with_usage():
    """
    HELP MENU
    """
    print 'Class and function to serve as a downloaded data Oracle'
    print 'Data takes the form of matfiles containing beat chromas'
    print 'Similar to ISMIR 2010 project (Boston HackDay)'
    sys.exit(0)


if __name__ == '__main__':
    # help menu than exit
    die_with_usage()

        
