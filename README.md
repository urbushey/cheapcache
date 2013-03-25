cheapcache
==========

Literal cheap caching with MongoDB - for storing documents from APIs that charge 
on a by-the-call basis.

Provides a decorator such that if the decorated function's argument has been 
previously called, it will be retrieved from MongoDB. If the argument is 
not cached in MongoDB already, both the argument and the results will
be cached there.

Can only be used to decorate a function that takes a single 
argument (such as the API call URL) and returns a string 
(assumed to be a json_string). 

NOTE: This decorator DOES NOT take care of removing cached values from the
cache.