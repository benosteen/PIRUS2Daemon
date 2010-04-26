#!/usr/bin/env python

from redisqueue import RedisQueue

from LogConfigParser import Config

from pirus2_openurl import make_request

import sys

from time import sleep

from urllib import urlopen, urlencode

if __name__ == "__main__":
  c = Config()
  redis_section = "redis"
  worker_number = sys.argv[1]
  worker_section = "worker_pirus2"
  if len(sys.argv) == 3:
    if "redis_%s" % sys.argv[2] in c.sections():
      redis_section = "redis_%s" % sys.argv[2]

  rq = RedisQueue(c.get(worker_section, "listento"), "pirus_%s" % worker_number,
                  db=c.get(redis_section, "db"), 
                  host=c.get(redis_section, "host"), 
                  port=c.get(redis_section, "port")
                  )

  try:
    plugin_name = c.get(worker_section, "repository_plugin")
    plugin_module = __import__(plugin_name)
    components = plugin_name.split('.')
    for comp in components[1:]:
        plugin_module = getattr(plugin_module, comp)
  except ImportError, e:
    print "Coundn't import module: '%s' - %s" % (c.get(worker_section, "repository_plugin"), e)
    sys.exit(2)
  
  if c.has_option(worker_section, 'pauseonfail'):
    try:
      delay_on_fail = int(c.get(worker_section, 'pauseonfail'))
    except:
      delay_on_fail = 300

  if c.has_option(worker_section, 'ratelimit'):
    try:
      delay = int(c.get(worker_section, 'ratelimit'))
    except:
      delay = 1

  while(True):
    line = rq.pop()
    if line:
      pl = plugin_module.parseline(line)
      openurl_params = plugin_module.get_openurl_params(c, worker_section, pl)
      if openurl_params:
        response = make_request(c, worker_section, openurl_params)
        if response == True:
          if c.has_option(worker_section, "success_queue"):
            rq.push(line, c.get(worker_section, "success_queue"))
          rq.task_complete()
          sleep(delay)
        else:
          rq.task_failed()
          print "Failed to send OpenURL to PIRUS2"
          print response
          sleep(delay_on_fail)
      else:
        if c.has_option(worker_section, "other_queue"):
          rq.push(line, c.get(worker_section, "other_queue"))
        rq.task_complete()
    else:
      sleep(delay)
