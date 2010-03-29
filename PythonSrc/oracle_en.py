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
# sqlite stuff
import sqlite3
import sqlite3.dbapi2 as sqlite
# python stuff
from pyechonest import config
from pyechonest import track as trackEN
from pyechonest import artist as artistEN
import en_extras



# ECHO NEST THREAD STUFF

# to stop the thread
_stop_en_thread = False
# queue size
_en_queue_size = 100
# to keep in song data
_thread_en_song_data = deque()
# lock for the song_data
#_thread_en_lock = thread.allocate_lock() # deque supposed to be thread safe
def _thread_en(artists):
    """
    Thread that load EN data
    For artists receives a SQLlite database containing a table 'artists' with
    a field 'name'.
    """
    print '_thread_en starting...'
    cnt_iter = 0
    waiting_artists = deque() # for db

    # MAIN LOOP
    while not _stop_en_thread:
        # debug
        cnt_iter += 1

        # queue full?
        if len(_thread_en_song_data) > _en_queue_size :
            time.sleep(0.050) # sleep for 50 milliseconds
            continue

        # get artist
        if len(waiting_artists) == 0:
            artist_list = get_artists_from_db(artists)
            if artist_list == None:
                print 'ERROR,: en_thread, cant get artist from SQL database'
                time.sleep(50)
                continue
            for k in artist_list:
                waiting_artists.append(k)        
        artist = waiting_artists.pop()

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

        # put data in queue, deque is supposed to be thread safe
        _thread_en_song_data.appendleft(d)

        
    print '_thread_en closing...'




def get_artists_from_db(dbname,nArtists=100):
    """
    Get a random set of artists from an SQLLite db
    Returns a list, or None if a problem.
    Number actually receives could be smaller than nArtists if db
    has less names. We return None only if we receive 0 artists.

    DB must contain a table 'artists' with a field 'name'
    DB is SQLlite, handled by sqlite3 package.
    """
    assert nArtists > 0,'ask for at least one artist!'
    assert nArtists < 10000,'wow.... that is a lot of artists'
    # connects to the DB
    connection = sqlite.connect(sqlite_db)
    # gets cursor
    cursor = connection.cursor()
    try:
        query = 'SELECT name FROM artists ORDER BY RANDOM() LIMIT '+str(nArtists)
        cursor.execute(q)
        res = cursor.fetchall()
        if len(res) == 0:
            return None
        return res
    except sqlite3.OperationalError:
        return None



# ORACLE CLASS

class OracleEN():
    """
    Class to get EchoNest features
    """

    def __init__(self,artists,nThreads = 1):
        """
        Constructor
        """
        # start a number of EN threads
        assert nThreads > 0,'you need at least one thread'
        assert nThreads <= 15,'15 threads is the limit, that is a lot!'
        for k in range(nThreads):
            thread.start_new_thread(_thread_en,(),{'artists':artists})
        # statistics
        self._nTracksGiven = 0

    def __del__(self):
        """
        Destructor
        """
        # stop thread
        _stop_en_thread = True


    def next_track(self,sleep_time=0.05):
        """
        Get the next song represented as a dictionary.
        Take it from the queue (waits infinitely if needed...!)
        Sleep time between iterations when waiting is sleep_time (seconds)
        """
        # make sure there is something in queue
        while True:
            if len(_thread_en_song_data) > 0:
                break
            time.sleep(sleep_time)
        # done
        self._nTracksGiven += 1
        return _thread_en_song_data.pop()

    def tracksGiven(self):
        """
        Return the number of tracks given since the creation of
        ths instance.
        """
        return self._nTracksGiven



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
