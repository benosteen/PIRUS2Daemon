Usage statistics distributor - for the PIRUS2 project
=====================================================

A set of small processes that take in, parse, and redistribute repository usage managed by a supervisord process (http://supervisord.org)

* Plugin-orientated: Can be extended by writing plugins to parse the incoming data as required.
* Distributed: Not necessary to run all the processes on the same machine
* JSON via message-queues - extensible to add other log tracking functionality and realtime appraisal.
* Single core configuration file with a tool to create an Debian-Apache style approach to managing worker processes (per-worker configurations in 'workers_available' with symlinks or copies in 'workers_enabled')
* Worker transactionality - workers can recover from unexpected crashes. Failed tasks are requeued and optional notifications can be added in this case.

Dependancies
------------

Supervisord, simplejson, Redis (>=1.2.6) and the python client for Redis.

(NB install python-dev package or equivalent, as the following should then build the C-backed library for simplejson which is very fast.)

* sudo easy_install supervisor simplejson

Take care to install the correct python client for your version of redis

Redis:
http://code.google.com/p/redis/

Python redis client:
http://github.com/andymccurdy/redis-py

Usage
-----

* Get, unpack and build redis on the host machine.
* Download or pull a copy of this project and unpack into an empty directory
* Open 'loglines.cfg':
 * Change the username/password in the 'supervisor' section
 * If you wish to manage the redis instance through supervisor, add in the path to the 'redis-server' command in the redis directory.
 * Configure the logfilewatcher section to tail the log that user access will be written to and change the 'servicename' to be the unique identifier for your repository
 * Configure the pirus2 section as required - see inline comments for more details
* run ./create_supervisord_config.py - this will create the requisite supervisord configuration
* To test, run 'supervisord -n -c supervisord.conf' - the '-n' option will stop supervisor from detaching and you can watch its progress.
* Point a web browser at http://localhost:9001 and enter the username and password to view and manage the workers
* You are looking for a clean line of green lights at this point if everything is happy!

Plugin system
-------------

## How to use: 

Place plugin files into the 'plugins' directory and change the plugin options in the pirus2 section in 'loglines.cfg'

## What are plugins used for?

A pirus2 plugin must provide two functions: 'parseline' and 'get_openurl_params'

> def parseline(jmsg) - where:
>   jmsg is a JSON encoded string. The default that is expected is a JSON-encoded dictionary of terms, the default being:
>   {'service':'service_unique_id', 'logline':'line from the logger that is to be parsed'}

parseline returns a dictionary of terms that it was able to extract from the logline

> def get_openurl_params(c, worker_section, pl) where:
>    c - ConfigParser instance, containing a parsed version of 'loglines.cfg' so you can include whatever variables in this that you require
>               (for custom configuration data, please use a section prefixed with your plugin's name to curb collisions)
>   worker_section - this will be the 'pirus2' section of the configuration for the worker that uses this plugin
>   pl - the parsed dictionary that came from 'parseline' above
    
get_openurl_params should return a dictionary of terms if it is to be sent to a PIRUS2 endpoint. Therefore this function should also determine whether or not it is eligable for PIRUS2. If not, it should return an empty dictionary or None.


