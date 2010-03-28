"""

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import time
import numpy as np
# sqlite stuff
import sqlite3
import sqlite3.dbapi2 as sqlite
# echonest stuff
from pyechonest import config
from pyechonest import artist as artistEN
try:
    config.ECHO_NEST_API_KEY = os.environ['ECHO_NEST_API_KEY']
except:
    config.ECHO_NEST_API_KEY = os.environ['ECHONEST_API_KEY']



def mine(sqlite_db,maxartists=1000000,verbose=False,nsims=100):
    """
    Mine EchoNest for artist name
    Method is simple: starts from the Beatles, get similar artists,
    mine similar artists.
    nsims - number of similar artists to ask for at Echo Nest, between
    1 and 100
    """

    assert nsims > 0 and nsims <= 100,'wrong nsims (# similar): %d'%nsims

    # start time
    tstart = time.time()

    # connects to the DB, creates it if necessary
    connection = sqlite.connect(sqlite_db)
    # gets cursor
    cursor = connection.cursor()

    # count iterations before commit
    cnt_commit = 0
    iter_between_commits = 10

    # db empty? create table, add Beatles
    try:
        cursor.execute('SELECT * FROM artists WHERE name="The Beatles"')
    except sqlite3.OperationalError:
        cursor.execute('CREATE TABLE artists (id INTEGER PRIMARY KEY,name VARCHAR(50), checked INTEGER)')
        cursor.execute('INSERT INTO artists VALUES (null, "The Beatles",0)')

    try:
        while True:
            # check if too many artists
            query = 'SELECT COUNT(id) FROM artists'
            cursor.execute(query)
            nArtists = int(cursor.fetchone()[0])
            if nArtists > maxartists:
                print 'db has',nArtists,', we want',maxartists,', we stop.'
                break
            
            # get an artist not checked
            query = 'SELECT name FROM artists WHERE checked=0 ORDER BY RANDOM() LIMIT 1'
            cursor.execute(query)
            unchecked = cursor.fetchone()
            if len(unchecked) == 0:
                print "we stop, all artists checked"
                break
            unchecked_artist = unchecked[0]
            if verbose:
                print '#artists:',nArtists,'new query artist:',unchecked_artist

            # find similar artists
            aEN = artistEN.search_artists(unchecked_artist)[0]
            asim = aEN.similar(rows=nsims)
            
            # add them to the database
            for a in asim:
                # artist name
                aname = a.name.replace('"','')
                # already in?
                query = 'SELECT name FROM artists WHERE name='
                query += '"' + aname + '"'
                cursor.execute(query)
                found = cursor.fetchmany(2)
                if len(found) == 0:
                    query = 'INSERT INTO artists VALUES (null, "'
                    query += aname + '",0)'
                    cursor.execute(query)

            # check in the query artist
            query = 'UPDATE artists SET checked=1 WHERE name='
            query += '"' + unchecked_artist + '"'
            cursor.execute(query)

            # commit
            cnt_commit += 1
            if cnt_commit % iter_between_commits == 0:
                if verbose:
                    print 'commiting...'
                connection.commit()

    # easy case, user terminates the program
    except KeyboardInterrupt:
        print "ERROR:", sys.exc_info()[0]        
        connection.close()
        return
    # try to get debug information
    except:
        print "ERROR:", sys.exc_info()[0]
        print 'last query=',query
        connection.close()
        return
    

    # finish correctly
    connection.commit()
    connection.close()
    print 'EchoNest artist name mining finished correctly'
    print 'program ran for',time.time()-tstart,'seconds'



def die_with_usage():
    """
    HELP MENU
    """
    print 'code to mine EchoNest for artists names'
    print 'usage:'
    print '   python mine_en_for_artists.py [flags] dbname'
    print 'FLAGS:'
    print ' -maxartists M    maximum number of artists, stop db size >= M'
    print ' -verbose         print every new artist query, and db size'
    print ' -nsims           num. similar artists to request from EN (100)'
    sys.exit(0)



if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # flags
    verbose = False
    maxartists = 1000000
    nsims = 100
    while True:
        if sys.argv[1] == '-maxartists':
            maxartists = int(sys.argv[2])
            sys.argv.pop(1)
        elif sys.argv[1] == '-verbose':
            verbose = True
        elif sys.argv[1] == '-nsims':
            nsims = int(sys.argv[2])
            sys.argv.pop(1)
        else:
            break
        sys.argv.pop(1)

    # params
    dbname = sys.argv[1]

    # go!
    mine(dbname,maxartists=maxartists,verbose=verbose)
