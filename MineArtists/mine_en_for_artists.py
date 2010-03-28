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





def table_exists(cursor,tablename):
    """
    Checks if a table exists.
    Trick taken from:
    http://sqlserver2000.databases.aspfaq.com/
    how-do-i-determine-if-a-table-exists-in-a-sql-server-database.html
    """
    query =  'IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES ' 
    query += "WHERE TABLE_TYPE='BASE TABLE' "
    query += "AND TABLE_NAME='" + tablename + "') " 
    query += "SELECT 1 ELSE SELECT 0" 
    cursor.execute(query)
    res = cursor.fetchone()[0]
    if res == 1:
        return True
    return False

def mine(sqlite_db,maxartists=1000000):
    """
    Mine EchoNest for artist name
    Method is simple: starts from the Beatles, get similar artists,
    mine similar artists.
    """

    # start time
    tstart = time.time()

    # connects to the DB, creates it if necessary
    connection = sqlite.connect(sqlite_db)
    # gets cursor
    cursor = connection.cursor()

    # db empty? create table, add Beatles
    #cursor.execute('CREATE TABLE artists (id INTEGER PRIMARY KEY,name VARCHAR(50), checked INTEGER)')
    #cursor.execute('INSERT INTO names VALUES (null, "The Beatles",0)')


    try:
        while True:
            # check if too many artists
            cursor.execute('SELECT COUNT(id) FROM artists')
            nArtists = cursor.fetchone()[0]
            if nArtist > maxartists:
                break
            
            # get an artist not checked
            cursor.execute('SELECT name FROM names WHERE checked=0')
            unchecked = cursor.fetchmany(1000)
            unchecked_artist = unchecked[np.random.randint(len(unchecked))][0]

            # find similar artists
            aEN = artistEN.search_artists(unchecked_artist)[0]
            asim = aEN.similar(rows=100)
            
            # add them to the database
            for a in asim:
                # already in?
                query = 'SELECT name FROM artists WHERE name='
                query += a.name
                cursor.execute(query)
                found = cursor.fetchmany(2)
                if len(found) == 0:
                    query = 'INSERT INTO artists VALUES (null, "'
                    query += a.name + '",0)'
                    cursor.execute(query)

            # check in the query artist
            query = 'UPDATE artists SET checked=1 WHERE name='
            query += unchecked_artist
            cursor.execute(query)

            # commit
            connection.commit()


            raise NotImplementedError
    except:
        print "ERROR:", sys.exc_info()[0]
        connection.commit()
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
    sys.exit(0)



if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 2:
        die_with_usage()

    # flags
    maxartists = 1000000
    while True:
        if sys.argv[1] == '-maxartists':
            maxartists = int(sys.argv[2])
            sys.argv.pop(1)
        else:
            break
        sys.argv.pop(1)

    # params
    dbname = sys.argv[1]

    # go!
    mine(dbname,maxartists=maxartists)
