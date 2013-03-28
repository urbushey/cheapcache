''' 
cheapcache.py
license:    http://opensource.org/licenses/MIT
author:     Uri Bushey
github:     https://github.com/urbushey/cheapcache

Provides a decorator such that If the decorated function's argument has been 
previously called, it will be retrieved from MongoDB. If the argument is 
not cached in MongoDB already, both the argument and the results will
be cached there.

Can only be used to decorate a function that takes a single 
argument (such as the API call URL) and returns a string 
(assumed to be a json_string). 

NOTE: This decorator DOES NOT take care of removing cached values from the
cache.

'''
db          = 'cheapcache'    # db to use for cache
collection  = 'test'          # collection to use for cache

import pymongo
import json

# If mongo is not installed and configured, we'll find out here. 
# TODO investigate moving this into cheapcached constructor
try:
    conn = pymongo.MongoClient()
    db   = conn[db]
    collection = db[collection]
except pymongo.errors.ConnectionFailure, e:
    print "Could not connect to MongoDB: %s" % e
    raise e

class cheapcached(object):
    ''' Decorator. If the decorated function's argument has been previously
    called, it will be retrieved from MongoDB. If it is not cached in MongoDB,
    it will be placed there.

    Example:

    >>> @cheapcached
    ... def request_data(url):
    ...    print "Getting data from the 'server'"
    ...    data = {}
    ...    data['foo'] = 'bar' # ignore url, mock the response
    ...    return json.dumps(data)

    >>> request_data('http://www.twitter.com/')
    Getting data from the 'server'
    '{"foo": "bar"}'
    >>> request_data('http://www.twitter.com/')
    u'{"foo": "bar"}'
    >>> request_data('http://www.google.com/')
    Getting data from the 'server'
    '{"foo": "bar"}'
    >>> request_data('http://www.twitter.com/urbushey')
    Getting data from the 'server'
    '{"foo": "bar"}'
    >>> from cheapcache import collection
    >>> collection.drop()
    '''

    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        url = args[0]
        # Check to see if url has been called (exists in mongodb)
        cached_json = collection.find_one({'url': url})
        
        # If it exists, return it
        if cached_json:
            json_string = cached_json['data']
            return json_string
        
        # Else, if url key does not exist in mongodb, take a trip to the server
        # (i.e. call the original function)
        json_string = self.func(url)
        
        # And cache the data returned
        self.cache_data(json_string, url)
        
        # And return the json string.
        return json_string

    def cache_data(self, json_string, url):
        cache_data = {}
        cache_data['url'] = url
        cache_data['data'] = json_string
        # no need to JSON-encode the cache_data dictionary, 
        # pymongo takes care of this for us
        collection.insert(cache_data)

if __name__ == '__main__':
    import doctest
    doctest.testmod()