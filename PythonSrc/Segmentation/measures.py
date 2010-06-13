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
    cuts_inter = lit(np.unique([0] + list(startbref) + list(startbcand) + [lastb]))
    # get number of pairs
    npairs_inter = count_similar_pairs(cuts_inter)
    # get all cuts for just the candidate
    cuts_cand = list(np.unique([0] + startbcand + [lastb]))
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
    cuts_inter = list(np.unique([0] + list(startbref) + list(startbcand) + [lastb]))
    # get number of pairs
    npairs_inter = count_similar_pairs(cuts_inter)
    # get all cuts for just the reference
    cuts_ref = list(np.unique([0] + startbref + [lastb]))
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
    cuts_inter = list(np.unique([0] + list(startbref) + list(startbcand) + [lastb]))
    # get number of pairs
    npairs_inter = count_similar_pairs(cuts_inter)
    # get all cuts for just the candidate
    cuts_cand = list(np.unique([0] + startbcand + [lastb]))
    # get number of pairs
    npairs_cand = count_similar_pairs(cuts_cand)
    # compute pairwise precision
    prec =  npairs_inter * 1. / npairs_cand
    assert prec < 1. + 1e-10, 'precision > 1'
    # get all cuts for just the reference
    cuts_ref = list(np.unique([0] + startbref + [lastb]))
    # get number of pairs
    npairs_ref = count_similar_pairs(cuts_ref)
    # compute pairwise recall
    rec = npairs_inter * 1. / npairs_ref
    assert rec < 1. + 1e-10, 'recall > 1'
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
    


def entropy_So_Su(startbref,stopbref,startbcand,stopbcand):
    """
    Computes entropy measures based on Lukashevich 2008
    First, H(estimated | ground truth) than H(gound truth | estimated)
    """
    assert stopbref[-1] == stopbcand[-1], "different end beat for cand and ref?"
    assert len(np.unique(startbref)) == len(startbref), 'empty segs in reference'
    assert len(np.unique(startbcand)) == len(startbcand), 'empty segs in cadidate'
    assert startbref[0] == 0, 'ref start beat not 0?'
    assert startbcand[0] == 0, 'cand start beat not 0?'
    # get last beat
    lastb = stopbref[-1]
    # compute number of segments (a -> ground truth, e -> candidate)
    Na = len(startbref)
    Ne = len(startbcand)
    # get belonging of eahc beat to a segment in both ref and cand
    beat_per_a_seg = np.zeros(lastb+1)
    for k in range(len(startbref)):
        beat_per_a_seg[startbref[k]:stopbref[k]+1] = k
    beat_per_e_seg = np.zeros(lastb+1)
    for k in range(len(startbcand)):
        beat_per_e_seg[startbcand[k]:stopbcand[k]+1] = k
    # computes n_ij, number of frames that belong simultaneously to segment i of ref
    # and j of candidate
    Nij = np.zeros([Na,Ne])
    for k in range(lastb+1):
        Nij[ beat_per_a_seg[k], beat_per_e_seg[k] ] += 1
    # compute H(e|a)
    Hea = 0
    for sega in range(len(startbref)):
        nia = np.sum(Nij[sega,:])
        pia = nia / (lastb+1.)
        for sege in range(len(startbcand)):
            pjiea = Nij[sega,sege] / nia
            if pjiea == 0:
                continue
            Hea -= pia * pjiea * np.log2(pjiea)
    assert not np.isnan(Hea),'Hea nan'
    # compute H(a|e)
    Hae = 0
    for sege in range(len(startbcand)):
        nje = np.sum(Nij[:,sege])
        pje = nje / (lastb+1.)
        for sega in range(len(startbref)):
            pijae = Nij[sega,sege] / nje
            if pijae == 0:
                continue
            Hae -= pje * pijae * np.log2(pijae)
    assert not np.isnan(Hae),'Hae nan'
    # compute So and Su
    So = 1 - Hea / np.log2( Ne )
    Su = 1 - Hae / np.log2( Na )
    # done, return
    return So, Su



def prec_rec_f_So_Su(startbref,stopbref,startbcand,stopbcand):
    """
    Convenience function, computes the 5 measures used in R. Weiss' paper
    at ISMIR 2010
    """
    prec, rec, f = pairwise_prec_rec_f(startbref,stopbref,startbcand,stopbcand)
    So, Su = entropy_So_Su(startbref,stopbref,startbcand,stopbcand)
    return prec, rec, f, So, Su
