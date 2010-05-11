#!/usr/bin/env python
import simplejson

import time, os, sys

from redis import Redis

from redis.exceptions import ConnectionError

from LogConfigParser import Config

REDIS_PUSH_ATTEMPTS = 3
DELAY_BETWEEN_ATTEMPTS = 5

class Redislogger(object):
  def __init__(self, servicename, queuename, redis_config):
    self.c = redis_config
    self.refresh_client()

  def refresh_client(self):
    self.r = Redis(**self.c)
  
  def submit_line(self, line):
    try_count = REDIS_PUSH_ATTEMPTS
    if try_count:
      try:
        msg = simplejson.dumps({'service':servicename, 'logline':line})
        self.r.lpush(queuename, msg)
        print "Pushed %s to %s" % (msg, queuename)
      except ConnectionError, e:
        try_count = try_count - 1
        time.sleep(DELAY_BETWEEN_ATTEMPTS)
        self.refresh_client()
    else:
      print "REDIS PUSH FAIL: %s" % line

def log_watcher(log_filename, servicename, queuename, redis_config, seek_point=None):
  fh = open(log_filename, 'r')
  r = Redislogger(servicename, queuename, redis_config)
  watcher = os.stat(log_filename)
  this_modified = last_modified = watcher.st_mtime
  # Seek to the correct point in the logfile
  if seek_point and isinstance(seek_point, int):
    fh.seek(seek_point)
  else:
    fh.seek(0,2) # seek to the end otherwise

  while True:
    if this_modified > last_modified:
      last_modified = this_modified
      """ File was modified, so read new lines, look for error keywords """
      while True:
        line = fh.readline()
        if not line: break	
        print line
        r.submit_line(line)

    watcher = os.stat(log_filename)
    this_modified = watcher.st_mtime
    time.sleep(1)

if __name__=='__main__':
  c = Config()
  redis_section = "redis"
  worker_number = sys.argv[1]
  worker_section = sys.argv[2]
  if len(sys.argv) == 4:
    if "redis_%s" % sys.argv[3] in c.sections():
      redis_section = "redis_%s" % sys.argv[3]
      
  # from config:
  redis_config = dict(c.items(redis_section))
  
  if 'port' in redis_config:
    redis_config['port'] = int(redis_config['port'])
  servicename = c.get(worker_section, "servicename")
  queuename = c.get(worker_section, "pushto")
  logfilename = c.get(worker_section, "logfile")
  
  log_watcher(logfilename, servicename, queuename, redis_config)
