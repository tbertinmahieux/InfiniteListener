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
        artists = artistEN.search_artists(artist)
        if len(artists) == 0:
            continue
        artist = artists[np.random.randint(len(artists))]
        # get song
        audio = artist.audio()
        if len(audio) == 0:
            continue
        songid = audio[np.random.randint(len(audio))]['id']
        # save stuff to queue
        entrack = trackEN.Track(songid)
        d = dict()
        d['segments'] = entrack.segments
        d['duration'] = entrack.duration
        d['beats'] = entrack.beats
        d['bars'] = entrack.bars
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

    def __init__(self,artist_list=[]):
        """
        Constructor
        """
        # start EN thread
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
    print '    python OracleEN.py -go'
    sys.exit(0)


if __name__ == '__main__':

    if len(sys.argv) < 2 :
        die_with_usage()


    # DEBUG

    oracle = OracleEN(['The Beatles','Weezer','ABBA'])

    # check if queue fills up
    tstart = time.time()
    for k in range(20):
        time.sleep(10)
        print 'after',time.time()-tstart,'seconds, queue size:',len(_thread_en_song_data)

    # kill oracle and thread
    del oracle
