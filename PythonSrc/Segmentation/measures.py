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




def precision(startbref,stopbref,startbcand,stopbcand):
    """
    Inputs are startbeat and stopbeat for reference and candidate.
    Formula taken from:
    Levy and Sandler, Structural Segmentation of Musical Audio
    by Constrained Clustering, IEEE TASLP, 2008
    """




    
