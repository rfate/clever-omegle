#!/usr/bin/env python
from urllib2 import urlopen, HTTPError
import json
import Queue
import thread

class Omegle:

  def __init__(self):
    self.event_queue = Queue.Queue()
    self.connected = False
    self.callbacks = {}

  def connect(self, type, callback):
    self.callbacks[type] = callback;

  def emit(self, type, data):
    if self.callbacks.has_key(type):
      self.callbacks[type](data)

  def start(self, threaded = False):
    self.id = json.loads(urlopen("http://promenade.omegle.com/start","").read())
    self.emit("debug", "Got ID: %s - waiting for connection..." % self.id)
    while not self.connected:
      rec = urlopen("http://promenade.omegle.com/events", "&id="+self.id).read()
      events = json.loads(rec)
      for event in (events.pop(0) for _ in range(len(events))):
        if event == ["waiting"]:
          self.emit("debug", "Waiting for connection...")
        elif event == ["connected"]:
          self.connected = True
          self.emit("debug", "Connected.")
          self.emit("connection_state", True)
          break
    for event in events:
      self.event_queue.put(event) # Queue extra remaining events in case we got them

    if threaded:
      thread.start_new_thread(self.__event_listener, ())
    else:
      self.__event_listener()

  def __event_listener(self):
    while self.connected:
      while True:
        try:
          event = self.event_queue.get_nowait()
          if not event:
            continue
          self.emit("debug", repr(event))
          if event[0] == "strangerDisconnected":
            self.connected = False
            self.emit("debug", "Stranger disconnected.")
            self.emit("connection_state", False)
            return
          elif event[0] in ("typing", "stoppedTyping"):
            self.emit("typing", event[0] == "typing")
            self.emit("event-received", event)
          elif event[0] == "gotMessage":
            self.emit("event-received", event[1])
            self.emit("message-received", event[1])
          else:
            self.disconnect()
            raise Exception("Unexpected response from server: " + repr(event))
          self.event_queue.task_done()
        except Queue.Empty:
          break
        except Exception, e:
          self.emit("debug", repr(e.args))
          break
      rec = urlopen("http://promenade.omegle.com/events", "&id="+self.id).read()

      raw_events = json.loads(rec)
      if raw_events:
        for event in raw_events:
          self.event_queue.put(event)

  def send_msg(self, msg_text):
    if not self.connected:
      raise Exception("Omegle(): No longer connected")
    assert( isinstance(msg_text, str) and len(msg_text) > 0 )
    try:
      urlopen("http://promenade.omegle.com/send", "&msg="+msg_text+"&id="+self.id).close()
    except HTTPError:
      self.event_queue.put(["strangerDisconnected"])

  def send_typing_event(self):
    if not self.connected:
      raise Exception("Omegle(): No longer connected")
    urlopen("http://promenade.omegle.com/typing", "&id="+self.id).close()

  def disconnect(self):
    if self.connected:
      self.connected = False
      urlopen("http://promenade.omegle.com/disconnect", "&id="+self.id).close()
      self.event_queue.put(["strangerDisconnected"])

  def __del__(self):
    self.disconnect()
