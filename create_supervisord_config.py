#!/usr/bin/env python

import sys, os

from LogConfigParser import Config

from ConfigParser import ConfigParser

OPTIONAL_SUPERVISOR_PROCESS_OPTIONS = ['user']

if __name__ == "__main__":
  if not os.path.exists("workers_enabled"):
    os.mkdir("workers_enabled")
  else:
    # clear out the enabled directory
    for conf in os.listdir("workers_enabled"):
      if os.path.isfile(os.path.join("workers_enabled", conf)):
        os.remove(os.path.join("workers_enabled", conf))

  if not os.path.exists("workers_available"):
    os.mkdir("workers_available")
  c = Config()
  base_superv_conf = "supervisord.conf.base"
  if len(sys.argv) == 2:
    # use a different base supervisor file
    base_superv_conf = sys.argv[1]
  supervisord_config = Config(base_superv_conf)

  if 'supervisor' in c.sections():
    supervisord_config.add_section('inet_http_server')
    params = {'username':'guest',
              'password':'mypassword',
              'port':'127.0.0.1:9001'}
    for key in params:
      if c.has_option('supervisor', key):
        supervisord_config.set('inet_http_server', key, c.get('supervisor', key))
      else:
        supervisord_config.set('inet_http_server', key, params['key'])

  with open("supervisord.conf", "w") as cfgfile:
    supervisord_config.write(cfgfile)
    
  # process_* for simple, single use processes that don't require additional configuration
  #     aside from the 'command' instruction
  #     eg  command = ../redis/redis-server ../redis/redis.conf  
  for worker in [x for x in c.sections() if x.startswith("process_")]:
    # Worker defaults:
    params = {'autorestart':'true',
              'numprocs':'1',
              'process_name':'%s_%%(process_num)s' % worker,
              'autostart':'true',
              'redirect_stderr':'True',
              'stopwaitsecs':'10',
              'startsecs':'10',
              'priority':'999',
              'startretries':'3',
              'stdout_logfile':'workerlogs/%s.log' % worker}
    worker_config = ConfigParser()
    section_name = "program:%s" % worker
    worker_config.add_section(section_name)
    for key in params:
      if c.has_option(worker, key):
        worker_config.set(section_name, key, c.get(worker, key))
      else:
        worker_config.set(section_name, key, params[key])
    for key in OPTIONAL_SUPERVISOR_PROCESS_OPTIONS:
      if c.has_option(worker, key):
        worker_config.set(section_name, key, c.get(worker, key))
    # set command
    command = c.get(worker, 'command')
    worker_config.set(section_name, 'command', command )
    
    worker_conf_fname = "workers_available/%s.conf" % worker
    
    with open(worker_conf_fname, "w") as cfgfile:
      worker_config.write(cfgfile)
    try:
      os.symlink(os.path.join("..", worker_conf_fname), "workers_enabled/%s.conf" % worker)
    except Exception, e:
      # make a copy, for those systems that cannot symlink
      import shutil
      shutil.copy(worker_conf_fname, "workers_enabled/%s.conf" % worker)

  
  for worker in [x for x in c.sections() if x.startswith("worker_")]:
    # Worker defaults:
    params = {'autorestart':'true',
              'numprocs':'3',
              'process_name':'%s_%%(process_num)s' % worker,
              'autostart':'true',
              'redirect_stderr':'True',
              'stopwaitsecs':'10',
              'startsecs':'10',
              'priority':'999',
              'startretries':'3',
              'stdout_logfile':'procname.log'}
    worker_config = ConfigParser()
    section_name = "program:%s" % worker
    worker_config.add_section(section_name)
    for key in params:
      if c.has_option(worker, key):
        worker_config.set(section_name, key, c.get(worker, key))
      else:
        worker_config.set(section_name, key, params[key])
    for key in OPTIONAL_SUPERVISOR_PROCESS_OPTIONS:
      if c.has_option(worker, key):
        worker_config.set(section_name, key, c.get(worker, key))
    # set command
    command = c.get(worker, 'command')
    worker_config.set(section_name, 'command', "%s %s" % (command, "%(process_num)s") )
    
    worker_conf_fname = "workers_available/%s.conf" % worker
    
    with open(worker_conf_fname, "w") as cfgfile:
      worker_config.write(cfgfile)
    try:
      os.symlink(os.path.join("..", worker_conf_fname), "workers_enabled/%s.conf" % worker)
    except Exception, e:
      # make a copy, for those systems that cannot symlink
      import shutil
      shutil.copy(worker_conf_fname, "workers_enabled/%s.conf" % worker)

  for logger in [x for x in c.sections() if x.startswith("logger_")]:
    # Worker defaults:
    params = {'autorestart':'true',
              'numprocs':'1',
              'process_name':'%s_%%(process_num)s' % logger,
              'autostart':'true',
              'redirect_stderr':'True',
              'stopwaitsecs':'10',
              'startsecs':'10',
              'priority':'999',
              'startretries':'3',
              'stdout_logfile':'procname.log'}
    worker_config = ConfigParser()
    section_name = "program:%s" % logger
    worker_config.add_section(section_name)
    for key in params:
      if c.has_option(logger, key):
        worker_config.set(section_name, key, c.get(logger, key))
      else:
        worker_config.set(section_name, key, params[key])    
    
    for key in OPTIONAL_SUPERVISOR_PROCESS_OPTIONS:
      if c.has_option(logger, key):
        worker_config.set(section_name, key, c.get(logger, key))
    # set command
    command = c.get(logger, 'command')
    worker_config.set(section_name, 'command', "%s %s %s" % (command, "%(process_num)s", logger) )

    worker_conf_fname = "workers_available/%s.conf" % logger

    with open("workers_available/%s.conf" % logger, "w") as cfgfile:
      worker_config.write(cfgfile)

    try:
      os.symlink(os.path.join("..", worker_conf_fname), "workers_enabled/%s.conf" % logger)
    except Exception, e:
      # make a copy, for those systems that cannot symlink
      import shutil
      shutil.copy(worker_conf_fname, "workers_enabled/%s.conf" % logger)
