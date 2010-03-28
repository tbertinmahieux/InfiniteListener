"""
Typical model, codebook that updates using online
vector quantization.

Model can predict and update

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import sys
import copy
import time
import numpy as np
import scikits.ann as ann



class Model():


    def __init__(self,codewords):
        """
        Constructor.
        Needs an initialized codebook, one code per line.
        """
        self._codebook = copy.deepcopy(codewords)
        self._nCodes = codewords.shape[0]
        self._codesize = codewords.shape[1]
        self._dist = euclidean_dist
        self._ann = ann.kdtree(self._codebook)


    def update(self,feats,lrate=1e-5):
        """
        Receives a set of features (one pattern per line)
        Do prediction on whole set.
        Update the codebook.

        Use the online VQ algorithm (simple online k-means)
        
        Note that we do minibatch, not exactly online, because
        updating the kdtree takes time for not much if learning
        rate is low.
        """
        # predicts on the features
        best_code_per_p,dists = self.predicts(feats)
        # update codebook
        for idx in range(feats):
            cidx = best_code_per_p[idx]
            self._codebook[cidx,:] += (feats[idx,:] - self._codebook[cidx,:]) * lrate
        # prepare kdtree for next time
        self._ann = ann.kdtree(self._codebook)


    def predicts(self,feats):
        """
        Returns two lists, best_code_per_pattern
        and average squared distance
        """
        
        best_code_per_p = np.zeros(feats.shape[0])
        avg_dists = np.zeros(feats.shape[0])
        idx = -1
        for f in feats:
            idx += 1
            code,dist = self._closest_code_ann(self,sample)
            best_code_per_p[idx] = code
            avg_dists[idx] = code * code * 1. / feats.shape[1]
        # don, return two list
        return best_code_per_p, avg_dists


    def _closest_code_ann(self,sample):
        """
        Finds the closest code to a given sample.
        Do it using a kd-tree
        Returns the index of the closest code
        and euclidean distance
        """
        res = self._ann.knn(sample,1)
        return res[0][0][0], res[1][0][0]  


def euclidean_dist(a,b):
    """
    Typical euclidean distance. A and B must be row vectors!!!!
    """
    return np.sqrt(np.square(a-b).sum())

def euclidean_norm(a):
    """ regular euclidean norm of a numpy vector """
    return np.sqrt(np.square(a).sum())
