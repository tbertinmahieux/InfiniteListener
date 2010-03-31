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
from collections import deque
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


    def update(self,feats,lrate=1e-5):
        """
        Receives a set of features (one pattern per line)
        Do prediction on whole set.
        Update the codebook.

        Use the online VQ algorithm (simple online k-means)
        
        Note that we do minibatch, not exactly online, because
        updating the kdtree takes time for not much if learning
        rate is low.

        Return avg_dist (mean squared distance per pixel)
        """
        # predicts on the features
        best_code_per_p,dists = self.predicts(feats)
        # update codebook
        for idx in range(feats.shape[0]):
            cidx = best_code_per_p[idx]
            self._codebook[cidx,:] += (feats[idx,:] - self._codebook[cidx,:]) * lrate
        # return mean dists
        return np.average(dists)

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
        Threshold set at 200 features.
        """
        # ann
        use_ann = feats.shape[0] > 200
        if use_ann:
            if sys.version_info[1] == 5: # problems on boar...
                use_ann = False
            else:
                kdtree = ann.kdtree(self._codebook)
        # prepare result
        best_code_per_p = np.zeros(feats.shape[0])
        avg_dists = np.zeros(feats.shape[0])
        idx = -1
        for f in feats:
            idx += 1
            if use_ann:
                code,dist = self._closest_code_ann(f,kdtree)
            else:
                code,dist = self._closest_code_batch(f)
            best_code_per_p[idx] = code
            avg_dists[idx] = dist * dist * 1. / feats.shape[1]
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


    def _closest_code_ann(self,sample,kdtree):
        """
        Finds the closest code to a given sample.
        Do it using a kd-tree, good if the codebook is not modified.
        Returns the index of the closest code
        and euclidean distance
        """
        res = kdtree.knn(sample,1)
        return res[0][0][0], res[1][0][0]  




def ModelFilter(Model):
    """
    Implements a regular online VQ model, but with a twist, a
    filter is added when updating the model.
    Difficult patterns are preferred.
    Model is slower, but... that's life.
    P.S. Uniorns rock!!!!
    """

    def __init__(self,codewords):
        """
        Constructor
        """
        # parent
        Model.__init__(self,codewords)
        # for average dist per code
        self._avg_dist_per_code = []
        for k in range(self._nCodes):
            self._avg_dist_per_code = deque()
        self._avg_dist_qlen = 200 # queue length


    def _add_dist(self,dist,codeidx):
        """
        Add a new distance to one of the codes.
        """
        self._avg_dist_per_code[codeix].append(dist)
        if len(self._avg_dist_per_code[codeix]) > self._avg_dist_qlen:
            self._avg_dist_per_code[codeix].popleft()

    def _get_avg_dist(self,codeidx):
        """
        Return average distance for a particular codeword, or None
        if no data is available
        """
        if len(self._avg_dist_per_code[codeix]) == 0:
            return None
        return np.average(self._avg_dist_per_code[codeix])

    def _accept_prob(self,dist,codeidx):
        """
        Compute the probability of acceptance given a distance and
        a particular codewords index.
        """
        if dist == 0:
            return 0.
        avg_dist_for_code = self._get_avg_dist(codeidx)
        if avg_dist_for_code == None:
            return 1.
        # logistic function on ratio 1/(1+exp(dist / avg_dist))
        # it's certain to be between 0 and 1 (excluded)
        return 1. / (1. + np.exp(dist / avg_dist_for_code) )

    def update(self,feats,lrate=1e-5):
        """
        Receives a set of features (one pattern per line)
        Do prediction on whole set.
        Update the codebook.

        Use the online VQ algorithm (simple online k-means)
        Adds filtering.
        Overrides Model() method!!!
        
        Note that we do minibatch, not exactly online, because
        updating the kdtree takes time for not much if learning
        rate is low.

        Return avg_dist (mean squared distance per pixel)
        """
        # predicts on the features
        best_code_per_p,dists = self.predicts(feats)
        # FILTER
        probs = np.array(map(lambda k: self._accept_prob(self,dists[k],best_code_per_p[k]),range(feats.shape[0])))
        idxs_to_keep = np.where(probs - np.random.rand(feats.shape[0])>0)[0]
        best_code_per_p_select = best_code_per_p[idxs_to_keep]
        feats_select = feats[idxs_to_keep]
        # update codebook
        for idx in range(feats_select.shape[0]):
            cidx = best_code_per_p_select[idx]
            self._codebook[cidx,:] += (feats_select[idx,:] - self._codebook[cidx,:]) * lrate
        # return mean dists
        return np.average(dists)


    

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
