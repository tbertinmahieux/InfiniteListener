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
    """
    Most simple model, has a codebook and updates by
    gradient descent using the online vector quantization algorithm.
    """

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

    def predicts(self,feats):
        """
        Returns two lists, best_code_per_pattern
        and average squared distance

        Note on method used:
        Uses ann if we have many features. Reason:
        during training, when we might look at one new sample
        at a time then update the codebook, building a kdtree is
        useless. If the model is trained and we want to predict on
        a large database, t's worth having the kdtree.
        Threshold set at 500.
        """
        # ann
        use_ann = feats.shape[0] > 500
        if use_ann:
            self._ann = ann.kdtree(self._codebook)
        # prepare result
        best_code_per_p = np.zeros(feats.shape[0])
        avg_dists = np.zeros(feats.shape[0])
        idx = -1
        for f in feats:
            idx += 1
            if use_ann:
                code,dist = self._closest_code_ann(self,sample)
            else:
                code,dist = self._closest_code_batch(self,sample)
            best_code_per_p[idx] = code
            avg_dists[idx] = code * code * 1. / feats.shape[1]
        # done, return two list
        return best_code_per_p, avg_dists


    def _closest_code_batch(self,sample):
        """
        Efficiently compute the distance from one sample to all codewords.
        Methods works well if the codebook is often modified.
        Returns the index of the closest code
        and euclidean distance
        """
        dists = euclidean_dist_batch(self._codebook,sample)
        bestidx = np.argmin(dists)
        return bestidx,dists[bestidx]


    def _closest_code_ann(self,sample):
        """
        Finds the closest code to a given sample.
        Do it using a kd-tree, good if the codebook is not modified.
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

def euclidean_dist_batch(a,b):
    """
    Typical euclidean distance. B must be row vectors!!!!
    A is a batch, one vector per row.
    """
    return np.sqrt(np.square(a-b).sum(axis=1))

def euclidean_norm(a):
    """ regular euclidean norm of a numpy vector """
    return np.sqrt(np.square(a).sum())
