# Sample app

from urllib import urlencode
from urllib2 import urlopen
from json import loads
from pprint import pprint
from cheapcache import cheapcached
import secret

wu_url = 'http://api.wunderground.com/api/'
wu_operation = '/geolookup/conditions/q/'
wu_response_type = '.json'

zip_code = '80224'

url = wu_url + secret.key + wu_operation + zip_code + wu_response_type

@cheapcached
def get_json(url):
    response = urlopen(url)
    json_string = response.read()
    return json_string

def pretty_print(json_string):
    wdata = loads(json_string)
    pprint(wdata)