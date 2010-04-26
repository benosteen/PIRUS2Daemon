#!/usr/bin/env python

import sys

from LogConfigParser import Config

if __name__ == "__main__":
  c = Config()
  base_superv_conf = "supervisord.conf.base"
  if len(sys.argv) == 2:
    # use a different base supervisor file
    base_superv_conf = sys.argv[1]
  supervisord_config = Config(base_superv_conf)
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
    
    section_name = "program:%s" % worker
    supervisord_config.add_section(section_name)
    for key in params:
      if c.has_option(worker, key):
        supervisord_config.set(section_name, key, c.get(worker, key))
      else:
        supervisord_config.set(section_name, key, params[key])
    # set command
    command = c.get(worker, 'command')
    supervisord_config.set(section_name, 'command', "%s %s" % (command, "%(process_num)s") )

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
    
    section_name = "program:%s" % logger
    supervisord_config.add_section(section_name)
    for key in params:
      if c.has_option(logger, key):
        supervisord_config.set(section_name, key, c.get(logger, key))
      else:
        supervisord_config.set(section_name, key, params[key])    
    
    # set command
    command = c.get(logger, 'command')
    supervisord_config.set(section_name, 'command', "%s %s %s" % (command, "%(process_num)s", logger) )

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
