"""
A set of functions to complement pyechonest
Mainly, do URL calls, get XML, parse it

For help on XML with Python, check:
http://diveintopython.org/xml_processing/index.html


T. Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu
"""


import os
import sys
import time
import copy
import xml
from xml.dom import minidom
import urllib
import numpy as np

try:
    _api_dev_key = os.environ['ECHO_NEST_API_KEY']
except:
    _api_dev_key = os.environ['ECHONEST_API_KEY']
from pyechonest import config
config.ECHO_NEST_API_KEY = _api_dev_key
from pyechonest import track as trackEN


def do_xml_call(url):
    """
    Calls echonest with a given command, expect XML document
    Return XML object
    """
    # open stream
    stream = urllib.urlopen(url)
    # directly parse it to XML
    xmldoc = minidom.parse(stream).documentElement
    # close stream
    stream.close()
    # done, return xml document
    return xmldoc

    # SLOW METHOD, BY CREATING A FILE:
    # call the url, save the output to file
    filename,httpmesage = urllib.urlretrieve(url)
    # open the file
    f = open(filename,'r')
    # parse it to xml
    xmldoc = minidom.parse(f).documentElement
    # close the file
    f.close()
    # return xml object
    return xmldoc



def check_xml_success(xmldoc):
    """
    Check an XML document received from the EchoNest
    Return True if success, otherwise
    """
    status = xmldoc.getElementsByTagName('status')[0]
    code = xmldoc.getElementsByTagName('code')[0]
    value = code.firstChild
    assert value.__class__.__name__ == 'Text'
    if value.data == '0':
        return True # succes
    return False # failure

    

def get_audio(artist_id,max_result=15):
    """
    Get the audio given an artist EchoNest id.
    artist_id example: ARH6W4X1187B99274F

    INPUT:
    - artist_id    something like: ARH6W4X1187B99274F
    - max_result   max number  of results (must be <= 15)

    Returns two list, or two None if error
    RETURN:
       ids,titles,artist    two lists + one string
       None,None,?          if problem, two none + none or artist

    This one is actually easy with pyechonest.
    This is a debugging case.
    """
    # build call
    url = 'http://developer.echonest.com/api/get_audio?api_key='
    url += _api_dev_key
    url += '&id=music://id.echonest.com/~/AR/'
    url += artist_id
    url += '&rows=' + str(int(max_result))
    url += '&version=3'
    # call, get XML
    xmldoc = do_xml_call(url)
    # check success
    if not check_xml_success(xmldoc):
        return None,None,None
    # get artist name
    artist_name = xmldoc.getElementsByTagName('artist')[0].firstChild.firstChild.data
    # get all audio
    results = xmldoc.getElementsByTagName('results')[0]
    nAudio = int(results.getAttribute('shown'))
    if nAudio == 0:
        return None,None,artist_name
    # we have positive results
    ids = []
    titles = []
    docs = results.getElementsByTagName('doc')
    for doc in docs:
        ids.append(doc.getAttribute('id'))
        title = doc.getElementsByTagName('title')[0].firstChild.data
        titles.append(title)
    # done, return lists
    return ids,titles,artist_name
    


def get_track_from_id(track_id):
    """
    Get track info (call 'analyze') given an id obtained from
    an artist, for instance.

    Typical call:
    http://developer.echonest.com/api/analyze?api_key=5ZAOMB3BUR8QUN4PE&id=fb6e02de612836c3b6d407291ba2260e&version=3


    RETURN
       pyechonest.track.Track instance or none
    """
    raise NotImplementedError
    # build call
    url = 'http://developer.echonest.com/api/get_audio?api_key='
    url += _api_dev_key
    url += '&id=' + track_id
    url += '&version=3'
    print url
    # call, get XML
    xmldoc = do_xml_call(url)
    # check success
    if not check_xml_success(xmldoc):
        return None
    # DEBUG
    print xmldoc.toprettyxml()

    

def die_with_usage():
    """
    HELP MENU
    """
    print 'library, set of function to complement pyechonest'
    print 'to test/debug, launch:'
    print '    python en_extras.py -go'
    sys.exit(0)


    
if __name__ == '__main__' :

    if len(sys.argv) < 2:
        die_with_usage()


    # DEBUGGING
    call1 = 'http://developer.echonest.com/api/get_audio?api_key=5ZAOMB3BUR8QUN4PE&id=musicbrainz:artist:6fe07aa5-fec0-4eca-a456-f29bff451b04&rows=2&version=3'

    # do a call, get XML
    xmldoc = do_xml_call(call1)

    # call for all audio for a given artist
    artist_id = 'ARH6W4X1187B99274F'
    ids, titles, artist_name = get_audio(artist_id)
    print 'after get_audio with',artist_name,'id, got:'
    for t in titles:
        print '   ',t

    # get info on the first track from previous call
    print 'calling id:',ids[0]
    track = get_track_from_id(ids[0])


