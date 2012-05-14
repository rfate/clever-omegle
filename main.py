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
note_window = curses.newwin(1, size[1], size[0]-2, 0)
input_window = curses.newwin(1, size[1], size[0]-1, 0)
text_pad = curses.textpad.Textbox(input_window)

buf = []

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", help="name to replace occurences of 'cleverbot'", default="captain howdy")
parser.add_argument("-d", "--debug", help="enable debug messages", action="store_true")
parser.add_argument("-i", "--intro", help="message to be sent upon connecting")
parser.add_argument("-q", "--quirkset", help="set of typing quirks to use", type=int, default=0)
parser.add_argument("-c", "--disable-cleverbot", help="disables cleverbot", action="store_true")

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

def clean_curses():
  curses.nocbreak()
  stdscr.keypad(0)
  curses.echo()
  curses.endwin()

def log(message):
  time = strftime("%H:%M:%S", gmtime())
  line = "[%s] %s\n" % (time, message)
  with open("log.txt", 'a') as f:
    f.write(line)

  buf.append(line)

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

    def handle_command(command):
      command = command.split(' ')
      if   command[0] == 'next' or command[0] == 'n':
        om.disconnect()
      elif command[0] == 'quirks' or command[0] == 'q':
        args.quirkset = int(command[1])
      elif command[0] == 'clever' or command[0] == 'c':
        args.disable_cleverbot = not args.disable_cleverbot
        log("Cleverbot %s" % ('disabled' if args.disable_cleverbot else 'enabled'))
      else: # default
        log("Command '%s' not found!" % command)

    def typing(ev):
      is_typing = ev
      if ev:
        note_window.addstr(0, 0, "Stranger is typing...")
      else:
        note_window.clear()
      note_window.refresh()

    def connected(ev):
      typing(False)
      if ev and args.intro:
        send(args.intro)

    def send(message):
      if message.startswith("/"):
        handle_command(message[1:])
        return

      message = quirkify(message)
      log("You: " + message)
      om.send_msg(message)

    def debug(ev):
      if args.debug:
        log("DEBUG: " + ev)

    def recv(ev):
      typing(False)
      log("Stranger: " + ev)
      if not args.disable_cleverbot:
        while True:
          try:
            om.send_typing_event()
            resp = cb.Ask(ev)
            resp = re.sub("cleverbot", args.name, resp, re.IGNORECASE)
            break
          except cleverbot.ServerFullError:
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
  clean_curses()
  exit()
except:
  clean_curses()
  raise
