"""
Set of measures to evaluates segmentation.
Main ones ares precision recall f-measure

All this measures should work on the EN data.
All we need is:
- startbeat and stopbeat for reference
- startbeat and stopbeat for candidate

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import numpy as np




def pairwise_precision(startbref,stopbref,startbcand,stopbcand):
    """
    Inputs are startbeat and stopbeat for reference and candidate.
    Formula taken from:
    Levy and Sandler, Structural Segmentation of Musical Audio
    by Constrained Clustering, IEEE TASLP, 2008
    """
    assert stopbref[-1] == stopbcand[-1], "different end beat for cand and ref?"
    # get last beat
    lastb = stopbref[-1]
    # get all cuts for the intersection
    cuts_inter = np.unique([0] + startbref + startbcand + [lastb])
    # get number of pairs
    npairs_inter = count_similar_pairs(cuts_inter)
    # get all cuts for just the candidate
    cuts_cand = np.unique([0] + startbcand + [lastb])
    # get number of pairs
    npairs_cand = count_similar_pairs(cuts_cand)
    # return pairwise precision
    return npairs_inter * 1. / npairs_cand


def pairwise_recall(startbref,stopbref,startbcand,stopbcand):
    """
    Inputs are startbeat and stopbeat for reference and candidate.
    Formula taken from:
    Levy and Sandler, Structural Segmentation of Musical Audio
    by Constrained Clustering, IEEE TASLP, 2008
    """
    assert stopbref[-1] == stopbcand[-1], "different end beat for cand and ref?"
    # get last beat
    lastb = stopbref[-1]
    # get all cuts for the intersection
    cuts_inter = np.unique([0] + startbref + startbcand + [lastb])
    # get number of pairs
    npairs_inter = count_similar_pairs(cuts_inter)
    # get all cuts for just the reference
    cuts_ref = np.unique([0] + startbref + [lastb])
    # get number of pairs
    npairs_ref = count_similar_pairs(cuts_ref)
    # return pairwise recall
    return npairs_inter * 1. / npairs_ref
    

def pairwise_prec_rec_f(startbref,stopbref,startbcand,stopbcand):
    """
    pairwise precision, recall, f-value
    slightly faster than to compute separately the two + f-value
    Inputs are startbeat and stopbeat for reference and candidate.
    Formula taken from:
    Levy and Sandler, Structural Segmentation of Musical Audio
    by Constrained Clustering, IEEE TASLP, 2008
    """
    assert stopbref[-1] == stopbcand[-1], "different end beat for cand and ref?"
    # get last beat
    lastb = stopbref[-1]
    # get all cuts for the intersection
    cuts_inter = np.unique([0] + startbref + startbcand + [lastb])
    # get number of pairs
    npairs_inter = count_similar_pairs(cuts_inter)
    # get all cuts for just the candidate
    cuts_cand = np.unique([0] + startbcand + [lastb])
    # get number of pairs
    npairs_cand = count_similar_pairs(cuts_cand)
    # compute pairwise precision
    prec =  npairs_inter * 1. / npairs_cand
    # get all cuts for just the reference
    cuts_ref = np.unique([0] + startbref + [lastb])
    # get number of pairs
    npairs_ref = count_similar_pairs(cuts_ref)
    # compute pairwise recall
    rec = npairs_inter * 1. / npairs_ref
    # compute f-value
    fval = 2 * prec * rec / (prec + rec)
    # return all 3 values
    return prec, rec, fval


def count_similar_pairs(cuts,assume0=True):
    """
    Subroutine to count similar pairs
    If we get [3,4,6], that means: 3*4/2 + 1*2/2 + 2*3/2 = 9 similar pairs
    Does not have to provide 0 first, added if not there (if assume0 True)
    """
    if cuts[0] != 0 and assume0:
        cuts = [0] + cuts
    # compute diffs
    diffs = np.diff(cuts)
    # compute similar pairs
    npairs = map(lambda x: x*(x+1)/2,diffs)
    # get total
    total = sum(npairs)
    # done, return
    return total
    
