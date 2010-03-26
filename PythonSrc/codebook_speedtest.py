"""
Implements a smart codebook.
The goal is to easily find the closest codeword to a given new
sample.
This can be used for k-means-like algorithms.

We use Elkan's paper on triangle inequality to speed things up.
(See Elkan, ICML 2003)

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import sys
import copy
import time
import numpy as np

#import kdtree
import scipy as sp
import scipy.spatial
# ANN
sys.path.append('scikits.ann-0.2.dev-r803/scikits')
import scikits.ann as ann


def euclidean_dist(a,b):
    """
    Typical euclidean distance. A and B must be row vectors!!!!
    """
    return np.sqrt(np.square(a-b).sum())

def euclidean_norm(a):
    """ regular euclidean norm of a numpy vector """
    return np.sqrt(np.square(a).sum())



class Codebook:
    """
    Implements an efficient codebook
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
        self._codebounds = np.ones([self._nCodes,self._nCodes]) * np.inf
        self._init_bounds()
        # test kd-tree
        self._kdtree = scipy.spatial.KDTree(self._codebook,leafsize=100)
        self._ckdtree = scipy.spatial.cKDTree(self._codebook,leafsize=100)
        # test ann kdtree
        self._ann = ann.kdtree(self._codebook)
        
    def _init_bounds(self):
        """
        init bounds with real distances
        """
        for l in range(len(self)):
            for c in range(l+1,len(self)):
                self._codebounds[l,c] = self._dist(self[l],self[c])

    def _update_bounds(self,codeidx,newcode,oldcode):
        """
        Compute a new bound between the update code and all the other
        codes
        """
        diffdist = self._dist(newcode,oldcode)
        # _codebounds is upper triangle
        for l in range(len(self)):
            if l == codeidx:
                continue
            idxs = np.sort( (l,codeidx) )
            self._codebounds[idxs[0],idxs[1]] = max(0,self._codebounds[idxs[0],idxs[1]]-diffdist)
        # done


    def closest_code(self,sample):
        """
        Returns index of the closest code
        """
        return closest_code_kdtree(sample)
    
        
    def closest_code_kdtree(self,sample):
        """
        Finds the closest code to a given sample.
        Do it using a kd-tree
        Returns the index of the closest code.
        """
        res = self._kdtree.query(sample)
        return res[1]

    def closest_code_ckdtree(self,sample):
        """
        Finds the closest code to a given sample.
        Do it using a kd-tree
        Returns the index of the closest code.
        """
        res = self._ckdtree.query(sample)
        return res[1]

    def closest_code_ann(self,sample):
        """
        Finds the closest code to a given sample.
        Do it using a kd-tree
        Returns the index of the closest code.
        """
        res = self._ann.knn(sample,1)
        return res[0][0][0]

    def closest_code_ann_approx(self,sample,eps=.1):
        """
        Finds the closest code to a given sample.
        Do it using a kd-tree
        Returns the index of the closest code.
        """
        res = self._ann.knn(sample,1,eps=.1)
        return res[0][0][0]
        

    def closest_code_debug(self,sample):
        """
        Finds the closest code to a given sample
        Do it in an trivial gready way.
        Returs the index of the closest code.
        """
        bestdist = np.inf
        bestidx = -1
        for idx in range(len(self)):
            dist = self._dist(self[idx],sample)
            if dist < bestdist:
                bestdist = dist
                bestidx = idx
        assert bestidx > -1, "debug function: did not find closest code???"
        return bestidx



    def __getitem__(self,index):
        """
        Returns the code at the given index
        Shallow copy!!!
        """
        return self._codebook[index]
    

    def __len__(self):
        """
        Gives the number of codes
        """
        return self._nCodes
    

    def __copy__(self):
        """ Shallow copy constructor """
        print 'Codebook.__copy__() called, does nothing'


    def clone(self):
        """ Deep copy the class """
        res = Codebook(self._codebook)
        res._nCodes = self._nCodes
        res._codesize = self._codesize
        
    




def die_with_usage():
    """ HELP MENU """
    print 'library file, contains class Codebook'
    sys.exit(0)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        die_with_usage()



    # DEBUGGING BASIC SPEED, no code update
    print ('debugging fast codebook')

    sample_size = 100
    codebook = np.random.rand(1000,sample_size)
    samples = np.random.rand(2000,sample_size)
    print 'creating a codebook of shape:',codebook.shape
    print 'testing on',samples.shape[0],'samples'
    timeslow = 0
    timekd = 0
    timeckd = 0
    timeann = 0
    tstart = time.time()
    cb = Codebook(codebook)
    print 'initialized codebook in',time.time()-tstart,'seconds.'
    for sample in samples:
        # debug
        tstart = time.time()
        idx2 = cb.closest_code_debug(sample)
        timeslow += time.time() - tstart
        # kdtree
        tstart = time.time()
        idx3 = cb.closest_code_kdtree(sample)
        timekd += time.time() - tstart
        # ckdtree
        tstart = time.time()
        idx4 = cb.closest_code_ckdtree(sample)
        timeckd += time.time() - tstart
        # ann
        tstart = time.time()
        idx5 = cb.closest_code_ann(sample)
        timeann += time.time() - tstart
        assert idx2 == idx3 or (cb[idx2] == cb[idx3]).all()
        assert idx2 == idx4 or (cb[idx2] == cb[idx4]).all()
        assert idx2 == idx5 or (cb[idx2] == cb[idx5]).all()
    #print 'time for fast algo:',timefast,'seconds.'
    print 'time for slow algo:',timeslow,'seconds.'
    print 'time for kd algo:  ',timekd,'seconds.'
    print 'time for ckd algo: ',timeckd,'seconds.'
    print 'time for ann algo: ',timeann,'seconds.'
