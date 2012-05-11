#!/usr/bin/env python
import argparse
import time
import re
import cleverbot
from omegle import Omegle

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", help="name to replace occurences of 'cleverbot'", default="captain howdy")
parser.add_argument("-d", "--debug", help="enable debug messages", action="store_true")
parser.add_argument("-i", "--intro", help="message to be sent upon connecting")
parser.add_argument("-q", "--quirkset", help="set of typing quirks to use", type=int, default=0)

parser.add_argument("-t", "--test", help="whatever wacky shit I'm trying to do at the moment", action="store_true")
args = parser.parse_args()

quirks = [
  [],
  [
    ["capslock"],

    ["I", "1"],
    ["E", "3"],
    ["A", "4"],
    ["([^\.])\.[$\s]", '\\1 '], # remove lone periods
    [",", ""],
    ["'S", "S"],
    # emoticons
    [":\)", ">:]"],
    ["\(:", ">:]"],
    ["\):", ">:["],
    [":\(", ">:["],
    [":D",  ">:D"],
    ["D:",  "D:<"],

    ["LOL", "H3H3"],
  ],
  [
    ["([\w\s])([\w\s]?)", "\\1".upper()+"\\2"],
  ],
]

def log(val):
  print val
  with open("log.txt", 'a') as f:
    f.write("%f: %s\n" % (time.time(), val))

def quirkify(message):
  for quirk in quirks[args.quirkset]:
    if len(quirk) == 1 and quirk[0] == 'capslock':
      message = message.upper()
    else:
      message = re.sub(quirk[0], quirk[1], message)
  return message

if args.test:
  print quirkify("Hello. :) :( (: ): :D D:")
  print quirkify("Hello...")
  exit()

try:
  while True:
    log("*****Conversation Start*****")
    cb = cleverbot.Session()
    om = Omegle()
    is_typing = False

    def typing(ev):
      is_typing = ev
      print "Stranger %s typing." % "started" if ev else "stopped"

    def connected(ev):
      if args.intro:
        send(args.intro)

    def send(message):
      log("You: " + message)
      om.send_msg(message)

    def debug(ev):
      if args.debug:
        print "DEBUG: " + ev

    def recv(ev):
      log("Stranger: " + ev)
      while True:
        try:
          om.send_typing_event()
          resp = cb.Ask(ev)
          resp = re.sub("cleverbot", args.name, resp, re.IGNORECASE)

          resp = quirkify(resp)
          break
        except cleverbot.ServerFullError:
          print "DEBUG: cleverbot.ServerFullError"
          continue

      if om.connected and len(resp) > 0:
        send(resp)

    om.connect("connected", connected)
    om.connect("message-received", recv)
    om.connect("typing", typing)
    om.connect("debug", debug)

    om.start()
    log("*****Conversation End*****")
except KeyboardInterrupt:
  exit()
