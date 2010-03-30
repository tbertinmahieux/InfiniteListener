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
                if tids != None and len(tids) > 0: # got songs
                    query = 'INSERT INTO artists VALUES (null, "'
                    query += artist + '",' + str(int(len(tids))) +')'
                    try:
                        cursor_new.execute(query)
                        connection_new.commit()
                    except sqlite.OperationalError, sqlite.IntegrityError :
                        pass
                # artist done
                query = 'INSERT INTO artists VALUES (null, "'
                query += artist + '")'
                cursor_done.execute(query)
                try:
                    connection_done.commit()
                except OperationalError:
                    pass
            
    except KeyboardInterrupt:
        # stop all threads
        _main_artist_queue.clear()
        # try to quit clean, commit than close
        connection_done.commit()
        connection_new.commit()
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
    connection_transf.close()

    # initalize new db
    connection_new = sqlite.connect(new_db)
    cursor_new = connection_new.cursor()
    try:
        cursor_new.execute('SELECT * FROM artists WHERE name="abc"')
    except sqlite3.OperationalError:
        cursor_new.execute('CREATE TABLE artists (id INTEGER PRIMARY KEY,name VARCHAR(50) UNIQUE, nsongs INTEGER)')
        connection_new.commit()
    connection_new.close()

    # launch threads
    assert nThreads > 0,'you need at least one thread'
    assert nThreads <= 15,'15 threads is the limit, that is a lot!'
    for k in range(nThreads):
        thread.start_new_thread(check_one_artist,(),{'done_db':transf_db,
                                                     'new_db':new_db})
    print 'launched',nThreads,'threads.'

    # to print info every minute
    last_print = time.time()
    # stupidly wait for queue to be empty
    try:
        while len(_main_artist_queue) > 0:
            if time.time() - last_print > 60.:
                print 'num. artists still in queue:',len(_main_artist_queue)
                last_print = time.time()
            time.sleep(1)
    except KeyboardInterrupt:
        print 'quitting, num. artists still in queue:',len(_main_artist_queue)
        _main_artist_queue.clear()
        time.sleep(1)
