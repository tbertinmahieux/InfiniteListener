"""
Code to select a subset of a database containing artist names.
The goal is to keep only artists that have actual song on the EchoNest
servers.

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import time
import thread
import threading
from collections import deque
import traceback
import numpy as np
# sqlite stuff
import sqlite3
import sqlite3.dbapi2 as sqlite
# echonest stuff
import pyechonest
from pyechonest import config
from pyechonest import artist as artistEN
try:
    config.ECHO_NEST_API_KEY = os.environ['ECHO_NEST_API_KEY']
except:
    config.ECHO_NEST_API_KEY = os.environ['ECHONEST_API_KEY']
import en_extras




# queue containing all artists
_main_artist_queue = deque()

# checked artists, queue contains pairs: (artist name,nSongs)
_checked_artists_queue = deque()



def eta(starttime,nstartelems,nelems,currtime=-1):
    """
    Compute an estmate time of arrival (completion) based on
    initial time, current time (by defult taking the computer time),
    number of elements to begin with and number of elements remaining.
    RETURN: string
    """
    if currtime == -1:
        currtime = time.time()
    time_elapsed = currtime - starttime # in seconds
    elems_done = nstartelems - nelems
    if elems_done <= 0:
        return 'UNKNOWN (zero or negative remaining elems?)'
    if time_elapsed <= 0:
        return 'UNKNOWN (zero or negative time elapsed?)'
    secs_per_elem = time_elapsed * 1. / elems_done
    time_remaining = secs_per_elem * nelems
    # less than minute
    if time_remaining < 60:
        return str(int(time_remaining)) + 'secs'
    # less than an hour
    if time_remaining < 3600:
        return str(int(time_remaining/60.)) + 'mins'
    # more than an hour
    return str(int(time_remaining/3600.)) + 'hours'


def check_one_artist(done_db=None,new_db=None):
    """
    Check one artist to see if it has songs.
    -Get an artist name from the main queue
    -Check if it is in 'done_db', don't redo it if it is
    -Check number of songs, add it to 'new_db' if needed

    The two databases must be initialized.
    """

    # open connections
    connection_done = sqlite.connect(done_db)
    connection_new = sqlite.connect(new_db)
    # gets cursors
    cursor_done = connection_done.cursor()
    cursor_new = connection_new.cursor()

    try:
        while len(_main_artist_queue) > 0:
            # get artist name
            try:
                artist = _main_artist_queue.pop()
            except IndexError:
                continue # we're probably done
            # artist already done?
            query = 'SELECT name FROM artists WHERE name='
            query += '"' + artist + '"'
            cursor_done.execute(query)
            found = cursor_done.fetchmany(2)
            # artist not found = not done, get songs
            if len(found) == 0:
                try:
                    tids,tmp_titles,tmp_aids,tmp_artists = en_extras.search_tracks(artist)
                except pyechonest.util.EchoNestAPIError:
                    # add abck to queue, wait a second, move to other song
                    _main_artist_queue.appendleft(artist)
                    time.sleep(1)
                    continue
                if tids == None:
                    tids = ()
                _checked_artists_queue.appendleft( (artist, len(tids)) )                    
    except KeyboardInterrupt:
        # stop all threads
        _main_artist_queue.clear()
        # try to quit clean, commit than close
        connection_done.close()
        connection_new.close()
        return

    except:
        # just close
        connection_done.close()
        connection_new.close()
        # print execution queue
        traceback.print_exc()
        # last query
        print 'last query = ', query
        return

    # finished correctly, queue empty
    connection_done.commit()
    connection_new.commit()
    connection_done.close()
    connection_new.close()
    print 'THREAD FINISHED'






def die_with_usage():
    """
    HELP MENU
    """
    print 'Select from a database artists that have confirmed songs at'
    print 'the Echo Nest API.'
    print 'usage:'
    print '  python find_artists_with_songs.py [FLAGS] <artistdb> <transferdb> <newdb>'
    print 'PARAMS'
    print ' <artistdb>    existing artist db with table: artists and field: name'
    print ' <transferdb>  databased not to check any artist twice, can be deleted after'
    print ' <newdb>       new db containing table: artists and fields: name, nsongs'
    print 'FLAGS'
    print '  -nThreads n  number of threads (default = 3)'
    print ''
    print 'code by T. Bertin-Mahieux (2010) Columbia University'
    print 'tb2332@columbia.edu'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        print die_with_usage()

    # flags
    nThreads = 3
    while True:
        if sys.argv[1] == '-nThreads':
            nThreads = int(sys.argv[2])
            sys.argv.pop(1)
        else:
            break
        sys.argv.pop(1)

    # get db name
    old_db = sys.argv[1]
    transf_db = sys.argv[2]
    new_db = sys.argv[3]

    # retrieve all songs from old_db, random order
    connection_old = sqlite.connect(old_db)
    cursor_old = connection_old.cursor()
    query = 'SELECT name FROM artists ORDER BY RANDOM()'
    cursor_old.execute(query)
    allartists = cursor_old.fetchall()
    connection_old.close()
    print 'found',len(allartists),'in original database'
    assert len(allartists) > 0,'no artist to start with?'
    nStartArtists = len(allartists)
    allartists = map(lambda x: x[0], allartists)
    # put them in the queue
    for k in allartists:
        _main_artist_queue.append(k)

    # initialize transfer db
    connection_transf = sqlite.connect(transf_db)
    cursor_transf = connection_transf.cursor()
    try:
        cursor_transf.execute('SELECT * FROM artists WHERE name="abc"')
    except sqlite3.OperationalError:
        cursor_transf.execute('CREATE TABLE artists (id INTEGER PRIMARY KEY,name VARCHAR(50))')
        connection_transf.commit()

    # initalize new db
    connection_new = sqlite.connect(new_db)
    cursor_new = connection_new.cursor()
    try:
        cursor_new.execute('SELECT * FROM artists WHERE name="abc"')
    except sqlite3.OperationalError:
        cursor_new.execute('CREATE TABLE artists (id INTEGER PRIMARY KEY,name VARCHAR(50) UNIQUE, nsongs INTEGER)')
        connection_new.commit()

    # launch threads
    assert nThreads > 0,'you need at least one thread'
    assert nThreads <= 15,'15 threads is the limit, that is a lot!'
    if nThreads > 1:
        print 'concurrency problem with the db, using 1 thread is safer'
    for k in range(nThreads):
        thread.start_new_thread(check_one_artist,(),{'done_db':transf_db,
                                                     'new_db':new_db})
    print 'launched',nThreads,'threads.'

    # to print info every minute
    start_time = time.time()
    last_print = time.time()
    # wait for artist queue to be empty and commit stuff
    try:
        while True:
            # print info
            if time.time() - last_print > 60.:
                print 'num. artists still in queue:',len(_main_artist_queue)
                print 'num. artists to commit:',len(_checked_artists_queue)
                print 'ETA: ' + eta(start_time,nStartArtists,len(_main_artist_queue))
                last_print = time.time()
            
            # done?
            if len(_checked_artists_queue) == 0 and len(_main_artist_queue) == 0:
                time.sleep(30) # to be sure no thread is finishing
                if len(_checked_artists_queue) == 0:
                    break

            # nothing to commit, wait
            if len(_checked_artists_queue) == 0:
                time.sleep(.5)
                continue

            cnt = 0
            while len(_checked_artists_queue) > 0:
                artist,nSongs = _checked_artists_queue.pop()
                # add to artists with songs
                if nSongs > 0:
                    query = 'INSERT INTO artists VALUES (null, "'
                    query += artist + '",' + str(nSongs) +')'
                    try:
                        cursor_new.execute(query)
                    except sqlite3.IntegrityError:
                        pass
                # add to checked
                query = 'INSERT INTO artists VALUES (null, "'
                query += artist + '")'
                cursor_transf.execute(query)
                cnt += 1
            # commit
            connection_transf.commit()
            connection_new.commit()

            
    except KeyboardInterrupt:
        print 'quitting, num. artists still in queue:',len(_main_artist_queue)
        # stop threads
        _main_artist_queue.clear()
        # close connections
        connection_transf.commit()
        connection_new.commit()
        connection_transf.close()
        connection_new.commit()
        # to be cleaner... maybe
        time.sleep(1)

    except:
        print 'MAIN THREAD:'
        print '********** DEBUGGING INFO *******************'
        formatted_lines = traceback.format_exc().splitlines()
        if len(formatted_lines) > 2:
            print formatted_lines[-3]
        if len(formatted_lines) > 1:
            print formatted_lines[-2]
        print formatted_lines[-1]
        print '*********************************************'
        # stop threads
        _main_artist_queue.clear()
        # just close
        connection_transf.close()
        connection_new.close()
        # to be cleaner... maybe
        time.sleep(1)
