#!/usr/bin/env python

"""Fake in-memory queue for test purposes (doesn't affect Redis)"""

import Queue

class FakeRedisQueue(object):
  def __init__(self, queuename, workername, db="", host="", port="", workerprefix=""):
    self.host = host
    if isinstance(port, str):
      try:
        self.port = int(port)
      except ValueError:
        self.port = 1234
    else:
      self.port = port
    self.queuename = queuename
    self.workeritem = ":".join([workerprefix, workername])
    self._inprogress = []
    self.db = db
    self._initclient()

  def _initclient(self):
    self._qs = {}
    self._qs[self.queuename] = Queue.Queue()

  def __len__(self):
    if self.inprogress():
      return self._qs[self.queuename].qsize() + 1
    else:
      return self._qs[self.queuename].qsize()

  def inprogress(self):
    if self._inprogress:
      return self._inprogress[0]

  def task_complete(self):
    self._inprogress = []

  def task_failed(self):
    if self._inprogress:
      self._qs[self.queuename].put(self._inprogress.pop())

  def push(self, item, to_queue=None):
    if to_queue:
      if to_queue not in self._qs:
        self._qs[to_queue] = Queue.Queue()
      self._qs[to_queue].put(item)
    else:
      return self._qs[self.queuename].put(item)

  def pop(self):
    if not self._inprogress:
      try:
        item = self._qs[self.queuename].get(block=False)
        self._inprogress.append(item)
      except Queue.Empty:
        return None
    return self.inprogress()
