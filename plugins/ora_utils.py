#!/usr/bin/env python

#from solr import SolrConnection

import re
LOGLINE_PATTERN = re.compile(r'(?P<date>[^\s]*) (?P<time>[^\s]*) (?P<level>[^\s]*) ([^\s]*) (?P<logger>[^\s]*) (?P<ip>[^\s]*) ([^\s]*) ([^\s]*) \[(?P<datetime>[^\]]*)\] \"(?P<request>[^\"]*)\" (?P<responsecode>[\d]*) ([^\s]*) ([^\s]*) (?P<useragent>[^\s]*)')

# Matches any GET on an object datastream
OBJ_DATASTREAM = re.compile(r"""GET /objects/(?P<namespace>ora|uuid|hdl)(\:|\%3A|\%253A)(?P<id>[0-9abcedf\-]+)/datastreams/(?P<dsid>[0-9A-z\-]+) """, re.I|re.U)


def _splitup_logline(line):
  params = LOGLINE_PATTERN.match(line)
  if params != None:
    return params.groupdict()
  else:
    return {}

def _get_id_and_datastream_from_splitline(sl):
  if 'responsecode' in sl and 'request' in sl:
    if sl['responsecode'] == 200:
      params = LOGLINE_PATTERN.match(line)
      if params != None:
        return params.groupdict()
  return {}

def parseline(line):
  sl = _splitup_logline(line)
  if sl:
    ident = _get_id_and_datastream_from_splitline(sl)
    if ident:
      # It's a download, go grab the metadata
      
  # Dictionary *must* include the demonstration keys below with the correct values set:
  return {'id':'test_id:4', 
           'ip':'163.1.127.176', 
           'useragent':'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; InfoPath.2; Badongo 2.0.0)',
           'referer':'http://google.com'}

def get_openurl_params(c, worker_section, pl):
  # Some useful defaults and mandatory keys which can be overriden in the cfg
  params = {'url_ver':'Z39.88-2004',
            'svc_dat':'Accepted version',
            'rfr_id':'',
            }
  for key in params:
    if c.has_option(worker_section, key):
      params[key] = c.get(worker_section, key)
  
  # DOI or ISSN+Journal Title
  doi = _get_doi(pl)
  params['rft_id'] = doi
  
  # Mimetype
  mimetype = _get_mimetype(pl)
  params['svc_format'] = mimetype
  
  # log line params to OpenURL params
  params['req_id'] = "urn:ip:%s" % pl['ip']
  params['req_dat'] = pl['useragent']
  
  return params

def _get_doi(pl):
  return "info:doi:http://dx.doi.org/10.1016/S0022-460X(03)00773-9"

def _get_mimetype(pl):
  return 'application/pdf'
