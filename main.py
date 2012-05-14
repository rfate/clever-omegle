#!/usr/bin/env python
import argparse
from time import gmtime, strftime
import curses
import curses.textpad
import re
import cleverbot
from omegle import Omegle

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(1)
curses.curs_set(0) # hide caret
size = stdscr.getmaxyx()
log_window = curses.newwin(size[0]-2, size[1], 0, 0)
input_window = curses.newwin(1, size[1], size[0]-1, 0)
text_pad = curses.textpad.Textbox(input_window)

buf = []

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", help="name to replace occurences of 'cleverbot'", default="captain howdy")
parser.add_argument("-d", "--debug", help="enable debug messages", action="store_true")
parser.add_argument("-i", "--intro", help="message to be sent upon connecting")
parser.add_argument("-q", "--quirkset", help="set of typing quirks to use", type=int, default=0)
parser.add_argument("--show-typing", help="display message when strager begins/stops typing", action="store_true")

parser.add_argument("-t", "--test", help="whatever wacky shit I'm trying to do at the moment", action="store_true")
args = parser.parse_args()

quirks = [
  [],
  [
    ["capslock"],

    ["I", "1"],
    ["E", "3"],
    ["A", "4"],
    ["([^\.])\.($|[^\.]|\b)", '\\1 '], # remove lone periods
    [",", ""],
    ["'S", "S"],
    # emoticons
    ["\):", ":("], # flip
    ["\(:", ":)"],
    [":\)", ":]"], # squarify
    [":\(", ":["],
    [":(3|O|P|D|\[|\])", ">:\\1"], # da hornz
    ["D:",  "D:<"],

    ["\b(HA|HE|AH)+\b", "H3H3"],
  ],
  [
    ["([\w\s])([\w\s]?)", "\\1".upper()+"\\2"],
  ],
]

def log(message):
  time = strftime("%H:%M:%S", gmtime())
  buf.append("[%s] %s\n" % (time, message))
  if len(buf) >= log_window.getmaxyx()[0]:
    buf.pop(0)
  update()

def update():
  for i, message in enumerate(buf):
    log_window.addstr(i, 0, message)
  log_window.refresh()

def quirkify(message):
  for quirk in quirks[args.quirkset]:
    if len(quirk) == 1 and quirk[0] == 'capslock':
      message = message.upper()
    else:
      message = re.sub(quirk[0], quirk[1], message)
  return message

try:
  while True:
    log("*****Conversation Start*****")
    cb = cleverbot.Session()
    om = Omegle()
    is_typing = False

    def typing(ev):
      is_typing = ev
      if args.show_typing:
        print "Stranger %s typing." % ("started" if ev else "stopped")

    def connected(ev):
      if ev and args.intro:
        send(args.intro)

    def send(message):
      if message.startswith("/next"):
        om.disconnect()
        return

      message = quirkify(message)
      log("You: " + message)
      om.send_msg(message)

    def debug(ev):
      if args.debug:
        print "DEBUG: " + ev

    def recv(ev):
      is_typing = False
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

      if om.connected and len(resp) > 0 and not is_typing and not args.test:
        send(resp)

    om.connect("connection_state", connected)
    om.connect("message-received", recv)
    om.connect("typing", typing)
    om.connect("debug", debug)

    om.start(threaded = True)

    while om.connected:
      inputted = text_pad.edit()
      if len(inputted) > 0 and om.connected:
        send(inputted)
        input_window.clear()

    log("*****Conversation End*****")
except KeyboardInterrupt:
  curses.nocbreak(); stdscr.keypad(0); curses.echo()
  curses.endwin()
  exit()
