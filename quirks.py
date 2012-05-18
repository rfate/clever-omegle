import re

default_quirks = [
  [],
  [
  	# pattern, action, args
    ["upper"],

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
    [":(\\\\|/|3|O|P|D|\[|\])", ">:\\1"], # da hornz
    ["D:",  "D:<"],

    ["\b(HA|HE|AH)+\b", "H3H3"]
  ]
]

def quirkify(set, message):
  for quirk in default_quirks[set]:
    if len(quirk) == 1 and quirk[0] == 'upper':
      message = message.upper()
    else:
      message = re.sub(quirk[0], quirk[1], message)
  return message
