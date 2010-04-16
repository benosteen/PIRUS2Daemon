#!/usr/bin/env python

from redisqueue import RedisQueue

from LogConfigParser import Config

import sys

from time import sleep

if __name__ == "__main__":
  c = Config()
  redis_section = "redis"
  worker_number = sys.argv[1]
  worker_section = sys.argv[2]
  if len(sys.argv) == 4:
    if "redis_%s" % sys.argv[3] in c.sections():
      redis_section = "redis_%s" % sys.argv[3]

  rq = RedisQueue(c.get(worker_section, "listento"), "logger_%s" % worker_number,
                  db=c.get(redis_section, "db"), 
                  host=c.get(redis_section, "host"), 
                  port=c.get(redis_section, "port")
                  )

  with open(c.get(worker_section, "logfile"), "a+") as logfile:
    while(True):
      line = rq.pop()
      if line:
        try:
          if line.endswith("\n"):
            logfile.write(line)
            rq.task_complete()
          else:
            logfile.writelines((line, "\n"))
            rq.task_complete()
        except Exception,e:
          rq.task_failed()
          print "Failed to log to file: %s" % e
          print line
      else:
        # Might as well flush the IO
        logfile.flush()
        # Check again after a 5 seconds wait
        sleep(5)
