"""
Simple code to compute the number of codes necessary to keep the
same bitrate.
"""

import sys
import numpy as np

def die_with_usage():
    print 'python compute_ncodes.py <smallest # beats> <smallest # codes> <# beats>'
    sys.exit(0)


if __name__ == '__main__':

    if len(sys.argv) < 4:
        die_with_usage()

    b1 = int(sys.argv[1])
    c1 = int(sys.argv[2])
    b2 = int(sys.argv[3])
    
    # we want b2/b1 = log_c1(c2)
    # ->   b2/b1 = log(c2) / log(c1)
    # ...
    # ->   c2 = exp( log(c1) * b2 / b1 )\

    tmp = np.log(c1) * b2 / b1
    tmp = np.exp(tmp)
    print 'approx. value:',tmp
    print 'rounded up:',int(np.round(tmp))

