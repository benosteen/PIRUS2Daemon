from urllib import urlencode

import socket
import urllib2

def make_request(c, worker_section, openurl_params):
  encoded_params = urlencode(openurl_params)
  endpoint_url = c.get(worker_section, 'endpoint_url')
  
  url = "%s?%s" % (endpoint_url, encoded_params)
  
  if c.has_option(worker_section, 'timeout'):
    try:
      timeout = int(c.get(worker_section, 'timeout'))
    except ValueError:
      timeout = 60
  
  socket.setdefaulttimeout(timeout)
  
  if c.has_option(worker_section, 'success'):
    try:
      success_code = int(c.get(worker_section, 'success'))
    except ValueError, e:
      success_code = 200
  
  f = urllib2.Request(url)
  try:
    response = urllib2.urlopen(req)
    response.close()
    if response.getcode() == success_code:
      return True
    else:
      return response
  except IOError, e:
    if hasattr(e, 'reason'):
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
  except:
    return response
