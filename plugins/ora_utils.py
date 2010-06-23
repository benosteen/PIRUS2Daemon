#!/usr/bin/env python

from hashlib import md5

from fedoraClient30 import FedoraClient

import re
LOGLINE_PATTERN = re.compile(r'(?P<date>[^\s]*) (?P<time>[^\s]*) (?P<level>[^\s]*) ([^\s]*) (?P<logger>[^\s]*) (?P<ip>[^\s]*) ([^\s]*) ([^\s]*) \[(?P<datetime>[^\]]*)\] \"(?P<request>[^\"]*)\" (?P<responsecode>[\d]*) ([^\s]*) ([^\s]*) (?P<useragent>.*$)')

# Matches any GET on an object datastream
OBJ_DATASTREAM = re.compile(r"""GET /objects/(?P<namespace>ora|uuid|hdl)(\:|\%3A|\%253A)(?P<id>[0-9abcedf\-]+)/datastreams/(?P<dsid>[0-9A-z\-]+) """, re.I|re.U)

OBJ_METADATA_DATASTREAM = re.compile(r"""GET /objects/(?P<namespace>ora|uuid|hdl)(\:|\%3A|\%253A)(?P<id>[0-9abcedf\-]+)/datastreams/(?P<dsid>MODS|DC|MARC21|FULLTEXT|RELS-EXT) """, re.I|re.U)

from solr import SolrConnection

import simplejson

from httplib import BadStatusLine

from time import sleep

import logging

logger = logging.getLogger("ora_utils")
logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

import urllib

SERVER = "http://ora.ouls.ox.ac.uk:8080/fedora/risearch"

SALT = "Oh I do like to be besides the seaside"

def getTrippi(query_type, query, lang='itql', format='Sparql',limit='100'):
  query_type = query_type.lower()
  if query != '' and (query_type == 'tuples' or query_type == 'triples'):
    queryparams = urllib.urlencode({'type' : query_type, 'lang' : lang, 'format' : format, 'query' : query, 'limit' : limit })
    response = urllib.urlopen( SERVER, queryparams).read()
    return response
  return None

def getTuples(query, lang='itql', format='sparql', limit='100', offset='0'):
  return getTrippi('tuples', query, lang, format, limit)

def resolveTinyPid(pid):
  query = "select $object from <#ri> where $object <info:fedora/fedora-system:def/model#label> '" + pid +"'"
  linelist = getTuples(query, format='csv').split("\n")
  if len(linelist) == 3:
    return linelist[1].split('/')[-1]
  else:
    return pid

def oralookup(pid=None, uuid=None, fields_to_return="f_name, f_subject, f_keyphrase, faculty, f_institution, thesis_type, content_type, collection", endpoint="http://ora.ouls.ox.ac.uk:8080/solr/select"):
  s = SolrConnection(endpoint)
  results = {}
  query = ""
  if pid:
    pid = "\:".join(pid.split(":"))
    query = "id:%s" % pid
  elif uuid:
    query = "id:uuid\:%s" % uuid
  else:
    return results
  # Running actual query (3 tries, failover)
  tries = 0
  while(tries != 3):
    try:
      r = s.query(q = query, fields = fields_to_return)
      logger.debug("Solr response: %s" % r.header)
      tries = 3
    except BadStatusLine:
      sleep(0.5)
      tries = tries + 1
  try:
    assert len(r.results) == 1
    return r.results[0]
  except ValueError:
    logger.warn("Couldn't parse json response from Solr endpoint: %s" % r)
    return {}
  except AssertionError:
    logger.warn("Couldn't assert that only a single result was fetched: %s" % results)
    return {}

def _splitup_logline(line):
  params = LOGLINE_PATTERN.match(line)
  if params != None:
    return params.groupdict()
  else:
    return {}

def _get_id_and_datastream_from_splitline(sl):
  # returns {} is if is not download from an item
  # otherwise the dict contains the id, datastream_id (dsid) and namespace
  if 'responsecode' in sl and 'request' in sl:
    if sl['responsecode'] == "200" or sl['responsecode'] == "204":
      params = OBJ_DATASTREAM.match(sl['request'])
      m_params = OBJ_METADATA_DATASTREAM.match(sl['request'])
      if params != None and m_params == None:
        return params.groupdict()
  return {}

def parseline(jmsg):
  pl = {}
  msg = simplejson.loads(jmsg)
  pl['rfr_id'] = msg['service']
  line = msg['logline']
  
  pl.update(_splitup_logline(line))
  if pl:
    ident = _get_id_and_datastream_from_splitline(pl)
    if ident:
      pl.update(ident)
      # It's a download, go grab the metadata and see if it's a journal title
      md_terms = oralookup(pid=":".join([ident['namespace'], ident['id']]), 
                fields_to_return="title, host, version, family, issn, eissn, doi, collection, content_type")
      pl.update(md_terms)
  return pl

def get_openurl_params(c, worker_section, pl):
  # Some useful defaults and mandatory keys which can be overriden in the cfg
  params = {'url_ver':'Z39.88-2004',
            'svc_dat':'Accepted version',
            'rfr_id':'',
            }
  for key in params:
    if c.has_option(worker_section, key):
      params[key] = c.get(worker_section, key)
    if key in pl:
      params[key] = pl[key]
  
  # DOI or ISSN+Journal Title
  doi = _get_doi(pl)
  if doi:
    params['rft_id'] = doi
  else:
    j_dict = _get_journal_info(pl)
    if j_dict:
      params.update(j_dict)
    else:
      # No DOI, no Journal Title/ISSN - doesn't meet PIRUS2 minimum standards.
      # Ignore
      return {}
      
  # Mimetype
  mimetype = _get_mimetype(pl)
  params['svc_format'] = mimetype
  
  # Repository URL
  pid = "%s:%s" % (pl['namespace'], pl['id'])
  params['rft.artnum'] = "http://ora.ouls.ox.ac.uk/objects/%s" % pid
  # log line params to OpenURL params
  #params['req_id'] = "urn:ip:%s" % pl['ip']
  params['req_id'] = md5(pl['ip'] + SALT).hexdigest()
  params['req_dat'] = pl['useragent']
  params['url_tim'] = "%sT%s" % (pl['date'], pl['time'])

  if pl.has_key("version") and pl['version']:
    params['svc_dat'] = pl['version']
  return params

def _get_doi(pl):
  if pl.has_key("doi"):
    doi_data = pl['doi']
    if isinstance(pl['doi'], list):
      for item in pl['doi']:
        if item:
          doi_data = item
    if doi_data.startswith("http://dx"):
      return "info:doi:%s" % doi_data
    else:
      return "info:doi:http://dx.doi.org/%s" % doi_data
  #return "info:doi:http://dx.doi.org/10.1016/S0022-460X(03)00773-9"

def _get_journal_info(pl):
  j_dict = {}
  # Journal Article test:
  if not (pl.has_key("collection") and pl['collection'] == [u"ora:articles"] \
      and pl.has_key("content_type") and pl['content_type'] == [u"article"]):
      return {}
  if pl.has_key("host"):
    try:
      j_dict['rft.jtitle'] = pl['host'].encode("UTF-8")
    except:
      j_dict['rft.jtitle'] = pl['host']
  if pl.has_key("title"):
    try:
      j_dict['rft.atitle'] = pl['title'].encode("UTF-8")
    except:
      j_dict['rft.atitle'] = pl['title']
  if pl.has_key("family") and pl['family']:
    try:
      # first author, last name:
      j_dict['rft.aulast'] = pl['family'][0].encode("UTF-8")
    except:
      j_dict['rft.aulast'] = pl['family'][0]
  if pl.has_key("issn"):
    if isinstance(pl['issn'], list):
      j_dict['rft.issn'] = pl['issn'][0]
    else:
      j_dict['rft.issn'] = pl['issn']
  if pl.has_key("eissn"):
    if isinstance(pl['eissn'], list):
      j_dict['rft.eissn'] = pl['eissn'][0]
    else:
      j_dict['rft.eissn'] = pl['eissn']
  return j_dict

def _get_mimetype(pl):
  if pl.has_key('dsid'):
    f = FedoraClient(server="http://ora.ouls.ox.ac.uk:8080/fedora")
    dl = f.listDatastreams("%s:%s" % (pl['namespace'], pl['id']), format="python")
    if pl['dsid'] in dl:
      return dl[pl['dsid']]['mimetype']
