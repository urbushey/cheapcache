''' 
cheapcache.py
license:    http://opensource.org/licenses/MIT
author:     Uri Bushey
github:     https://github.com/urbushey/cheapcache

Provides a decorator such that if the decorated function's argument has been 
previously called, it will be retrieved from MongoDB. If the argument is 
not cached in MongoDB already, both the argument and the results will
be cached there.

Can only be used to decorate a function that takes a single 
argument (such as the API call URL) and returns a string 
(assumed to be a json_string). 

NOTE: This decorator DOES NOT take care of removing cached values from the
cache.

'''
import pymongo
import json
from datetime import datetime, timedelta

db          = 'cheapcache'          # db to use for cache
collection  = 'test'                # collection to use for cache
cache_age   =  timedelta(minutes=1) # timedelta object representing age of cache

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
    ...     print "Getting data from the 'server'"
    ...     data = {}
    ...     data['foo'] = 'bar' # ignore url, mock the response
    ...     return json.dumps(data)
    >>> collection = db['doctest'] 
    >>> request_data('http://www.twitter.com/')
    Getting data from the 'server'
    '{"foo": "bar"}'
    >>> request_data('http://www.twitter.com/')
    '{"foo": "bar"}'
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
            json_string = str(cached_json['data']) #added str to get rid of unicode, messing up doctests
            return json_string
        
        # Else url key does not exist in mongodb, take a trip to the server
        # (i.e. call the original function) andcache the data returned
        else:
            json_string = self.func(url)
            self.cache_data(json_string, url)
        
        # And return the json string.
        return json_string

    def cache_data(self, json_string, url):
        cache_data = {}
        cache_data['url']  = url
        cache_data['data'] = json_string
        # no need to JSON-encode the cache_data dictionary, 
        # pymongo takes care of this for us
        collection.insert(cache_data)

class cheapcached_with_datetime(cheapcached):  # todo add argument of time-delta
    ''' Decorator. Like cheapcached, but will store the datetime that 
    the data entered the cache. The function will check for items newer than
    cache_age (defined at the top) in the cache, ignoring older results.
    Note that, like cheapcached, this function will not clean up older data
    in the cache.

    Example:
    >>> @cheapcached_with_datetime
    ... def request_data(url):
    ...     print "Getting data from the 'server'"
    ...     data = {}
    ...     data['foo'] = 'bar' # ignore url, mock the response
    ...     return json.dumps(data)
    >>> collection = db['doctest'] 
    >>> request_data('http://www.twitter.com/')
    Getting data from the 'server'
    '{"foo": "bar"}'
    >>> request_data('http://www.twitter.com/')
    '{"foo": "bar"}'
    >>> request_data('http://www.google.com/')
    Getting data from the 'server'
    '{"foo": "bar"}'
    >>> request_data('http://www.twitter.com/urbushey')
    Getting data from the 'server'
    '{"foo": "bar"}'
    >>> from cheapcache import collection
    >>> collection.drop()

    '''
    
    def __call__(self, *args):
        url      = args[0]
        check_dt = datetime.now() - cache_age
        
        # check to see if the url exists (in MongoDB)
        cached_json = collection.find_one({'url': url})
        
        # If cached data exists, check date
        if cached_json:
            cached_dt = cached_json['date']
            # if the date exists, compare it to the check_dt
            if cached_dt:
                # cached data is younger than check_dt, return cached data
                if cached_dt > check_dt:
                    json_string = str(cached_json['data'])
                    return json_string
                # cached data is older than check_dt, ignore cached data
                else:
                    json_string = self.ignore_cache(url) 
            # the date doesn't exist, better ignore cached data
            else:
                json_string = self.ignore_cache(url)
            
        # Else url key does not exist in mongodb, take a trip to the server
        # (i.e. call the original function) and record the current time
        else:
            json_string = self.ignore_cache(url)
        
        # And return the json string.
        return json_string

    def ignore_cache(self, url):
        json_string = self.func(url)
        self.cache_data(json_string, url)
        return json_string

    def cache_data(self, json_string, url):
        cache_data = {}
        cache_data['url']  = url
        cache_data['data'] = json_string
        cache_data['date'] = datetime.utcnow()
        # no need to JSON-encode the cache_data dictionary, 
        # pymongo takes care of this for us
        collection.insert(cache_data)

if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding("UTF-8")
    import doctest
    doctest.testmod()