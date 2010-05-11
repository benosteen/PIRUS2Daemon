#!/usr/bin/env python

from redisqueue import RedisQueue

from LogConfigParser import Config

from pirus2_openurl import make_request

import sys

from time import sleep

from urllib import urlopen, urlencode

import logging

logger = logging.getLogger("pirus2_dispatcher")
logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

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
    logger.error("Coundn't import module: '%s' - %s" % (c.get(worker_section, "repository_plugin"), e))
    sys.exit(2)
  
  if c.has_option(worker_section, 'pauseonfail'):
    try:
      delay_on_fail = int(c.get(worker_section, 'pauseonfail'))
    except:
      delay_on_fail = 300

  if c.has_option(worker_section, 'ratelimit'):
    try:
      delay = float(c.get(worker_section, 'ratelimit'))
    except:
      delay = 1
  logger.debug("Delay on fail set to: %s   Ratelimit set to: %s" % (delay_on_fail, delay))
  
  while(True):
    line = rq.pop()
    if line:
      pl = plugin_module.parseline(line)
      openurl_params = plugin_module.get_openurl_params(c, worker_section, pl)
      if openurl_params:
        if c.has_option(worker_section, 'debug'):
          logger.info("Article download - OpenURL params: %s" % openurl_params)
        else:
          logger.debug("OpenURL params: %s" % openurl_params)
        response = make_request(c, worker_section, openurl_params)
        if response == True:
          if c.has_option(worker_section, "success_queue"):
            rq.push(line, c.get(worker_section, "success_queue"))
          rq.task_complete()
          sleep(delay)
        else:
          rq.task_failed()
          sleep(delay_on_fail)
      else:
        logger.debug("Not an article download")
        logger.debug(line)
        if c.has_option(worker_section, "other_queue"):
          rq.push(line, c.get(worker_section, "other_queue"))
        rq.task_complete()
    else:
      sleep(delay)
