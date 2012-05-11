#!/usr/bin/env python
import argparse
import time
import re
import cleverbot
from pyomegle import Omegle

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", help="name to replace occurences of 'cleverbot'", default="captain howdy")
parser.add_argument("-d", "--debug", help="enable debug messages", action="store_true")
parser.add_argument("-i", "--intro", help="message to be sent upon connecting")
args = parser.parse_args()

def log(val):
  print val
  with open("log.txt", 'a') as f:
    f.write("%f: %s\n" % (time.time(), val))

while True:
  log("*****Conversation Start*****")
  cb = cleverbot.Session()
  om = Omegle()

  def send(message):
    log("You: " + message)
    om.send_msg(message)

  def debug(obj, ev):
    if args.debug:
      print "DEBUG: " + ev
    if ev == "Connected." and args.intro:
      send(args.intro)

  def recv(obj, ev):
    log("Stranger: " + ev)
    while True:
      try:
        om.send_typing_event()
        resp = cb.Ask(ev)
        resp = re.sub("cleverbot", args.name, resp, re.IGNORECASE)
        break
      except cleverbot.ServerFullError:
        print "DEBUG: cleverbot.ServerFullError"
        continue
    
    if om.connected and len(resp) > 0:
      send(resp)

  om.connect("message-received", recv)
  om.connect("debug", debug)

  om.start(threaded = False)
  log("*****Conversation End*****")
