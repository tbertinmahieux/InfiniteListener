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
import threading
from collections import deque
import numpy as np
# features stuff
import features
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
# deque is thread-save for pop and append, but not length. Trying to repeatedly
# pop and catching InderError is super inefficient!
# regular queue lock must be dumb, sempahore should improve things
_thread_en_sem = threading.BoundedSemaphore()


def _add_data(data):
    """
    Add data (if queue not full) and release semaphore
    Return number of elements in queue
    """
    # get _en_queue_size, if 0 or negative we stop threads
    max_qs = _en_queue_size
    if max_qs < 1:
        _stop_en_thread = True
    # get lock
    _thread_en_sem.acquire()
    # get queue size
    qs = len(_thread_en_song_data)
    # add
    if qs < max_qs:
        _thread_en_song_data.appendleft(data)
        qs += 1
    # release mutex
    _thread_en_sem.release()
    # return queue size
    return qs

def _get_data():
    """
    Returns data or None if queue empty, and release semaphore
    """
    # get lock
    _thread_en_sem.acquire()
    # get data
    if len(_thread_en_song_data) > 0:
        data = _thread_en_song_data.pop()
    else:
        data = None
    # relase semaphore
    _thread_en_sem.release()
    # return
    return data


def _thread_en(artistsdb,filename=''):
    """
    Thread that load EN data
    For artists receives a SQLlite database containing a table 'artists' with
    a field 'name'.
    Filename is used when downloading a dict from EN. If a filename is provided,
    we retrieve the uri to this file. Therefore, filename must be unique
    for each thread. If no filename is provided, we read straight from
    the stream, and we eventually seg fault.
    """
    cnt_iter = 0
    cnt_provided = 0
    waiting_artists = deque() # for db

    # MAIN LOOP
    while not _stop_en_thread:
        # debug
        cnt_iter += 1

        # get artist
        if len(waiting_artists) == 0:
            artist_list = get_artists_from_db(artistsdb)
            if artist_list == None:
                print 'ERROR,: en_thread, cant get artist from SQL database'
                time.sleep(50)
                continue
            for k in artist_list:
                waiting_artists.append(k)
        artist = waiting_artists.pop() # no thread concurrency here

        # get song
        tids,tmp_titles,tmp_aids,tmp_artists = en_extras.search_tracks(artist)
        if tids == None or len(tids) == 0:
            continue
        trackid = tids[np.random.randint(len(tids))]

        # save EchoNest data to queue
        segstart,chromas,beatstart,barstart,duration = en_extras.get_our_analysis(trackid,filename=filename)
        if segstart == None:
            continue
        d = {'segstart':segstart,'chromas':chromas,
             'beatstart':beatstart,'barstart':barstart,'duration':duration}
        # put data in queue, deque is supposed to be thread safe but we have
        # an extra semaphore
        queue_size = _add_data(d)

        # queue full?        
        if queue_size >= _en_queue_size :
            time.sleep(5) # sleep for 5 seconds
            cnt_iter -= 1
            continue

        #print 'added data (artist :',artist,') to _en_queue' #debugging
        # success rate too low? print WARNING
        cnt_provided += 1
        if cnt_provided % 100 == 0:
            prob_provide = cnt_provided*100./cnt_iter
            if prob_provide < 85.:
                print 'WARNING: _en_thread, prob. of providing is low:',prob_provide,'% , artists do not actually have song?'

    # done
    print 'stopping _en_thread, prob. of providing:',cnt_provided*1./cnt_iter



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
    connection = sqlite.connect(dbname)
    # gets cursor
    cursor = connection.cursor()
    try:
        query = 'SELECT name FROM artists ORDER BY RANDOM() LIMIT '+str(nArtists)
        cursor.execute(query)
        res = cursor.fetchall()
        connection.close()
        if len(res) == 0:
            return None
        return [x[0] for x in res]
    except sqlite3.OperationalError:
        connection.close()
        return None



# ORACLE CLASS

class OracleEN:
    """
    Class to get EchoNest features
    """

    def __init__(self,params,artists):
        """
        Constructor
        params is a dictionary containing all we need to now about:
          - features
          - nThreads
        """
        # features stuff
        self._pSize = params['pSize']
        self._usebars = params['usebars']
        self._keyInv = params['keyInv']
        self._songKeyInv = params['songKeyInv']
        self._positive = params['positive']
        self._do_resample = params['do_resample']
        self._partialbar = 0
        if params.has_key('partialbar'):self._partialbar = params['partialbar']
        # start a number of EN threads
        nThreads = params['nThreads']
        assert nThreads > 0,'you need at least one thread'
        assert nThreads <= 15,'15 threads is the limit, that is a lot!'
        self._thread_files = []
        randint = str(int(np.random.randint(1000000)))
        for k in range(nThreads):
            thread_file = '.en_thread_file_'+str(k)+'_'+str(time.time())
            thread_file += '_' + randint
            self._thread_files.append(thread_file)
            thread.start_new_thread(_thread_en,(),{'artistsdb':artists,
                                                   'filename':thread_file})
        # statistics
        self._nTracksGiven = 0

    def __del__(self):
        """
        Destructor
        """
        # stop thread
        _stop_en_thread = True
        for k in self._thread_files:
            try:
                os.remove(k)
            except:
                pass
            self._thread_files = []


    def next_track(self,sleep_time=5.0):
        """
        Get the next song features
        Take it from the queue (waits infinitely if needed...!)
        Sleep time between iterations when waiting is sleep_time (seconds)
        """
        # get data
        while True:
            data = _get_data()
            if data != None:
                break
            time.sleep(sleep_time)
        self._nTracksGiven += 1
        # get features
        return features.get_features(data,pSize=self._pSize,
                                     usebars=self._usebars,
                                     keyInv=self._keyInv,
                                     songKeyInv=self._songKeyInv,
                                     positive=self._positive,
                                     do_resample=self._do_resample,
                                     partialbar=self._partialbar,
                                     btchroma_barbts=None)

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
