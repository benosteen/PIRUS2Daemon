# -*- coding: utf-8 -*-
import random, unittest, re

from plugins import ora_utils

from LogConfigParser import Config

# Test suite for ora_utils plugin

BOTDOWNLOAD = '''2010-03-16 13:31:15,239,239 INFO  [wsgi] 207.46.204.228 - - [16/Mar/2010:13:31:14 +0100] "GET /objects/uuid%3A8fc817c9-9dd9-448a-9961-872bb07a138b/datastreams/ATTACHMENT01 HTTP/1.1" 200 2291968 "-" "msnbot/2.0b (+http://search.msn.com/msnbot.htm)"'''

NOTADOWNLOAD = '''2010-03-16 13:31:15,794,794 INFO  [wsgi] 116.125.141.4 - - [16/Mar/2010:13:31:15 +0100] "GET /objects/uuid%3A4184c918-b851-43fa-acef-ee2ab0bed0e7/relationships?format=xml HTTP/1.1" 200 - "http://ora.ouls.ox.ac.uk/" "Mozilla/5.0 (compatible; MSIE or Firefox mutant; not on Windows server; +http://ws.daum.net/aboutWebSearch.html) Daumoa/2.0"'''

JOURNALDOWNLOAD = '''2009-03-31 13:56:55,666,666 INFO  [wsgi] 195.171.182.14 - - [31/Mar/2009:13:56:54 +0100] "GET /objects/uuid%3A054790ca-08eb-4365-af4b-79748fab1fd9/datastreams/ATTACHMENT01 HTTP/1.1" 200 280090 "-" "Python-urllib/2.5"'''

DOWNLOAD = '''2009-04-01 01:14:28,301,301 INFO  [wsgi] 75.26.142.230 - - [01/Apr/2009:01:14:27 +0100] "GET /objects/uuid%3Ac2c638d3-fc6c-4dd1-85c8-682f3e9f40a2/datastreams/ATTACHMENT02 HTTP/1.1" 200 375650 "http://www.google.com/search?hl=en&q=dusp+gene+family&aq=f&oq=" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; GTB5; .NET CLR 1.1.4322; .NET CLR 2.0.50727; MS-RTC LM 8)"'''

class TestORAUtils(unittest.TestCase):
  def setUp(self):
    pass

  def test_get_doi(self):
    p = ora_utils._get_doi({'doi':'12345/1234', 'foo':'bar'})
    self.assertEquals(p, 'info:doi:http://dx.doi.org/12345/1234')
    
  def test_get_doi_http(self):
    p = ora_utils._get_doi({'doi':'http://dx.doi.org/12345/1234', 'foo':'bar'})
    self.assertEquals(p, 'info:doi:http://dx.doi.org/12345/1234')

  def test_get_journal_info_host(self):
    p = ora_utils._get_journal_info({'host':'Journal of Something or other', 'foo':'bar'})
    self.assertEquals(p, {'rft.jtitle':'Journal of Something or other'})

  def test_get_journal_info_issn(self):
    p = ora_utils._get_journal_info({'issn':'1234-1234', 'foo':'bar'})
    self.assertEquals(p, {'rft.issn':'1234-1234'})

  def test_get_journal_info_joint(self):
    p = ora_utils._get_journal_info({'host':'Journal of Something or other', 'foo':'bar','issn':'1234-1234'})
    self.assertEquals(p, {'rft.jtitle':'Journal of Something or other','rft.issn':'1234-1234'})

  def test_splitline_DOWNLOAD(self):
    sl = ora_utils._splitup_logline(DOWNLOAD)
    self.assertEquals(sl['date'], "2009-04-01")
    self.assertEquals(sl['ip'], "75.26.142.230")
    self.assertEquals(sl['responsecode'], "200")
    
  def test_splitline_NOTADOWNLOAD(self):
    sl = ora_utils._splitup_logline(NOTADOWNLOAD)
    self.assertEquals(sl['date'], "2010-03-16")
    self.assertEquals(sl['responsecode'], "200")
    self.assertEquals(sl['ip'], "116.125.141.4")
    self.assertEquals(sl['useragent'], '"Mozilla/5.0 (compatible; MSIE or Firefox mutant; not on Windows server; +http://ws.daum.net/aboutWebSearch.html) Daumoa/2.0"')
    
  def test_id_and_datastream_from_splitline_DOWNLOAD(self):
    sl = ora_utils._splitup_logline(DOWNLOAD)
    ident = ora_utils._get_id_and_datastream_from_splitline(sl)
    self.assertEquals(ident, {'namespace': 'uuid', 'dsid': 'ATTACHMENT02', 'id': 'c2c638d3-fc6c-4dd1-85c8-682f3e9f40a2'})

  def test_id_and_datastream_from_splitline_NOTADOWNLOAD(self):
    sl = ora_utils._splitup_logline(NOTADOWNLOAD)
    ident = ora_utils._get_id_and_datastream_from_splitline(sl)
    self.assertEquals(ident, {})

  def test_parseline_DOWNLOAD(self):
    pl = ora_utils.parseline(DOWNLOAD)
    self.assertEquals(pl[u'host'], u'BMC Genomics')
    self.assertEquals(pl[u'datetime'], u'01/Apr/2009:01:14:27 +0100')
    self.assertEquals(pl[u'useragent'], u'"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; GTB5; .NET CLR 1.1.4322; .NET CLR 2.0.50727; MS-RTC LM 8)"')
    self.assertEquals(pl[u'dsid'],'ATTACHMENT02')

  def check_params(self, line, expected_params={}):
    c = Config()
    worker_section = 'worker_pirus2'
    pl = ora_utils.parseline(line)
    params = ora_utils.get_openurl_params(c, worker_section, pl)
    if expected_params:
      for key in expected_params:
        self.assertEquals(params[key], expected_params[key])
    else:
      self.assertEquals(params, {})
    return params
    
  def test_get_openURL_params_DOWNLOAD(self):
    line = DOWNLOAD
    expected_params = {'svc_dat': 'Accepted version', 
                       'rfr_id': 'ora.bodleian.ox.ac.uk', 
                       'url_ver': 'Z39.88-2004', 
                       'rft_id': u'info:doi:http://dx.doi.org/10.1186/1471-2164-7-271', 
                       'req_id': 'urn:ip:75.26.142.230', 
                       'rfr_dat': '2009-04-01T01:14:28,301,301', 
                       'req_dat': '"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; GTB5; .NET CLR 1.1.4322; .NET CLR 2.0.50727; MS-RTC LM 8)"'}
    params = self.check_params(line, expected_params)

  def test_get_openURL_params_NOTADOWNLOAD(self):
    self.check_params(NOTADOWNLOAD)

  def test_get_openURL_params_JOURNALDOWNLOAD(self):
    expected_params = {'svc_dat': 'Accepted version', 
                       'rfr_id': 'ora.bodleian.ox.ac.uk', 
                       'url_ver': 'Z39.88-2004', 
                       'rft_id': u'info:doi:http://dx.doi.org/10.1121/1.2195267', 
                       'req_id': 'urn:ip:195.171.182.14', 
                       'rfr_dat': '2009-03-31T13:56:55,666,666', 
                       'req_dat': '"Python-urllib/2.5"'}
    params = self.check_params(JOURNALDOWNLOAD, expected_params)
    
  def test_get_openURL_params_BOTDOWNLOAD(self):
    expected_params = {'svc_dat': 'Accepted version', 
                       'rfr_id': 'ora.bodleian.ox.ac.uk', 
                       'url_ver': 'Z39.88-2004', 
                       'req_id': 'urn:ip:207.46.204.228', 
                       'rfr_dat': '2010-03-16T13:31:15,239,239', 
                       'rft.jtitle': u'Contributions to Nepalese Studies', 
                       'rft.issn': u'0376-7574', 
                       'req_dat': '"msnbot/2.0b (+http://search.msn.com/msnbot.htm)"'}
    params = self.check_params(BOTDOWNLOAD, expected_params)

if __name__ == '__main__':
    unittest.main()
