import urllib2
import md5
import time
import logging

from google.appengine.api import memcache
from xml.dom import minidom

service = 'http://api.quova.com/'
version = 'v1/'
method = 'ipinfo/'

QUOVAAPI_KEY = 'QUOVA_KEY'
QUOVAAPI_SECRET = 'QUOVA_SECRET'

QUOVA_NAMESPACE = "quova"

def ipinfo(ip):
  # set a default IP address for testing
  if ip is None or ip=='127.0.0.1':
        ip = '4.2.2.2'

  # cache responses from quova
  data = memcache.get(ip, namespace=QUOVA_NAMESPACE)
  if data is not None:
    #logging.info("cache hit")
    return data
  else:
    data = ipinfo_request(ip)
    memcache.add(ip, data, namespace=QUOVA_NAMESPACE)
    #logging.info("cache miss")
    return data

def ipinfo_request(ip):
  hash = md5.new()
  # seconds since GMT Epoch
  timestamp = str(int(time.time()))
  # print timestamp
  sig = md5.new(QUOVAAPI_KEY + QUOVAAPI_SECRET + timestamp).hexdigest()
  url = service + version + method + ip + '?apikey=' + QUOVAAPI_KEY + '&sig=' + sig
  # print url
  xml = urllib2.urlopen(url).read()
  xml = minidom.parseString(xml)
  return xml

def get(xml, name):
  elem = xml.getElementsByTagName(name)[0]
  return getText(elem.childNodes)

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
