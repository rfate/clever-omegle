#!/usr/bin/env python
import argparse
from time import gmtime, strftime
import re
import cleverbot
from omegle import Omegle
from quirks import quirkify

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", help="name to replace occurences of 'cleverbot'", default="captain howdy")
parser.add_argument("-d", "--debug", help="enable debug messages", action="store_true")
parser.add_argument("-i", "--intro", help="message to be sent upon connecting")
parser.add_argument("-q", "--quirkset", help="set of typing quirks to use", type=int, default=0)
parser.add_argument("-c", "--disable-cleverbot", help="disables cleverbot", action="store_true")
parser.add_argument("--disable-curses", help="disables ncurses interface", action="store_true")
conf = parser.parse_args()

if not conf.disable_curses:
  import curses
  import curses.textpad

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

  chat_buffer = []

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

  if conf.disable_curses:
    print line
  else:
    chat_buffer.append(line)

    if len(chat_buffer) >= log_window.getmaxyx()[0]:
      chat_buffer.pop(0)
    update()

def update():
  for i, message in enumerate(chat_buffer):
    log_window.addstr(i, 0, message)
  log_window.refresh()

try:
  while True:
    log("*****Conversation Start*****")
    cb = cleverbot.Session()
    om = Omegle()
    is_typing = False
    is_connected = False

    # this is a fat fucking hack
    def handle_command(command):
      command = command.split(' ')
      if   command[0] == 'next' or command[0] == 'n':
        om.disconnect()
      elif command[0] == 'quirks' or command[0] == 'q':
        conf.quirkset = int(command[1]) if (len(command[1]) > 0) else 0
      elif command[0] == 'clever' or command[0] == 'c':
        conf.disable_cleverbot = not conf.disable_cleverbot
        log("Cleverbot %s" % ('disabled' if conf.disable_cleverbot else 'enabled'))
      else: # default
        log("Command '%s' not found!" % command)

    def typing(ev):
      is_typing = ev
      if not conf.disable_curses:
        if ev:
          note_window.addstr(0, 0, "Stranger is typing...")
        else:
          note_window.clear()
        note_window.refresh()

    def connected(ev):
      is_connected = ev
      typing(False)
      if ev and conf.intro:
        send(conf.intro)

    def send(message):
      if message.startswith("/"):
        handle_command(message[1:])
        return

      message = quirkify(conf.quirkset, message)
      log("You: " + message)
      om.send_msg(message)

    def debug(ev):
      if conf.debug:
        log("DEBUG: " + ev)

    def recv(ev):
      typing(False)
      log("Stranger: " + ev)
      if not conf.disable_cleverbot:
        while True:
          try:
            om.send_typing_event()
            resp = cb.Ask(ev)
            resp = re.compile("cleverbot").sub(conf.name, resp, re.IGNORECASE)
            break
          except cleverbot.ServerFullError:
            continue

        # this line also needs to check if cleverbot is disabled as it may be changed
        # while obtaining a response from cleverbot
        if om.connected and len(resp) > 0 and not is_typing and not conf.disable_cleverbot:
          send(resp)

    om.connect("connection_state", connected)
    om.connect("message-received", recv)
    om.connect("typing", typing)
    om.connect("debug", debug)

    om.start(threaded = True)

    while om.connected:
      if conf.disable_curses:
        inputted = str(raw_input("> "))
      else:
        inputted = text_pad.edit()
      if len(inputted) > 0 and om.connected:
        send(inputted)
        if not conf.disable_curses:
          input_window.clear()

    log("*****Conversation End*****")
except KeyboardInterrupt:
  if not conf.disable_curses:
    clean_curses()
  raise
