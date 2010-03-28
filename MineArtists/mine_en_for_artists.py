"""

T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""

import os
import sys
import sqlite3
import sqlite3.dbapi2 as sqlite


def mine(sqlite_db,maxartists=1000000):
    """
    Mine EchoNest for artist name
    Method is simple: starts from the Beatles, get similar artists,
    mine similar artists.
    """

    # connects to the DB, creates it if necessary
    connection = sqlite.connect(sqlite_db)






    raise NotImplementedError






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
