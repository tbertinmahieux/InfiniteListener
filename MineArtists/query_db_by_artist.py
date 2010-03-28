"""
Simple util to check if an artist name is in an SQLlite database.

T. Bertin-Mahieux (2010) Colummbia Unviersity
tb2332@columbia.edu
"""


import os
import sys
import time
import copy
import sqlite3
import sqlite3.dbapi2 as sqlite




def die_with_usage():
    print 'usage:'
    print 'python query_db_by_name.py <dbname> <artist name>'
    print ' '
    print 'Query an SQLlist database for a given artist name.'
    print "Assumes there is a table 'artists' with a field 'name'."
    print '<artist name> must be exact in the sense:'
    print '     if weird composed name, add " before and after'
    print '     all " must be removed'
    print '     otherwise, must appear exactly like in EchoNest data'
    print 'RETURN'
    print '  everything for the row containing the artist, or NOT FOUND'
    sys.exit(0)


if __name__ == '__main__':

    if len(sys.argv) < 3:
        die_with_usage()

    dbname = sys.argv[1]
    artist = sys.argv[2]
    artist = artist.replace('"','')

    try:
        # connection
        connection = sqlite.connect(dbname)
        cursor = connection.cursor()

        # query
        query = 'SELECT name FROM artists WHERE name='
        query += '"' + artist + '"'
        cursor.execute(query)
        found = cursor.fetchall()
        
    except sqlite3.OperationalError:
        print 'ERROR, wrong database name? artist name with weird signs?'
        sys.exit(0)

    # NOT FOUND
    if len(found) == 0:
        print 'NOT FOUND'
        sys.exit(0)

    print len(found),'entries found:'
    for entry in found:
        print '  ',entry
    
        
