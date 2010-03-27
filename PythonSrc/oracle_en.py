"""
Oracle to go get data from the EchoNest

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""



import os
import sys
import time
import copy
import thread
from collections import deque
import numpy as np

from pyechonest import config
from pyechonest import track as trackEN
from pyechonest import artist as artistEN
import en_extras



# ECHO NEST THREAD STUFF

# to stop the thread
_stop_en_thread = False
# queue size
_en_queue_size = 20
# to keep in song data
_thread_en_song_data = deque()
# lock for the song_data
#_thread_en_lock = thread.allocate_lock() # deque supposed to be thread safe
def _thread_en(artist_list=[]):
    """
    Thread that load EN data
    """
    print '_thread_en starting...'
    cnt_iter = 0
    while not _stop_en_thread:
        # debug
        cnt_iter += 1
        print cnt_iter,'_thread_en iterations'
        # queue full?
        if len(_thread_en_song_data) > _en_queue_size :
            time.sleep(0.050) # sleep for 50 milliseconds
            continue
        # get artist
        if artist_list == []:
            raise NotImplementedError
        else:
            idx = np.random.randint(len(artist_list))
            artist = artist_list[idx]

        #artists = artistEN.search_artists(artist)
        #if len(artists) == 0:
        #    continue
        #artist = artists[np.random.randint(len(artists))]

        # get song
        tids,titles,aids,artists = en_extras.search_tracks(artist)
        if tids == None or len(tids) == 0:
            continue
        trackid = tids[np.random.randint(len(tids))]
        # save EchoNest data to queue
        segstart,chromas,beatstart,barstart,duration = en_extras.get_our_analysis(trackid)
        if segstart == None:
            continue
        d = {'segstart':segstart,'chromas':chromas,
             'beatstart':beatstart,'barstart':barstart,'duration':duration}
        # put data in queue
        #_thread_en_lock.acquire() # deque is supposed to be thread safe
        _thread_en_song_data.appendleft(d)
        #_thread_en_lock.release()
        
    print '_thread_en closing...'






# ORACLE CLASS

class OracleEN():
    """
    Class to get EchoNest features
    """

    def __init__(self,artist_list=[],nThreads = 1):
        """
        Constructor
        """
        # start a number of EN threads
        assert nThreads > 0,'you need at least one thread'
        assert nThreads <= 15,'15 threads is the limit, that is a lot!'
        for k in range(nThreads):
            thread.start_new_thread(_thread_en,(),{'artist_list':artist_list})

    def __del__(self):
        """
        Destructor
        """
        # stop thread
        _stop_en_thread = True







def die_with_usage():
    """
    HELP MENU
    """
    print 'Class and function to serve as an EchoNest oracle'
    print 'for simple test/debug, launch:'
    print '    python oracle_en.py -go'
    sys.exit(0)


if __name__ == '__main__':

    if len(sys.argv) < 2 :
        die_with_usage()


    # DEBUG

    oracle = OracleEN(['The Beatles','Weezer','ABBA'],nThreads=4)

    # check if queue fills up
    tstart = time.time()
    for k in range(20):
        time.sleep(10)
        print 'after',time.time()-tstart,'seconds, queue size:',len(_thread_en_song_data)

    # kill oracle and thread
    del oracle
