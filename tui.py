# -*- coding: UTF-8 -*-
"""
Helper functions to build CLI applications

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import os
import readline
import subprocess
import tempfile
import locale
import colors as C
from yokadiexception import YokadiException

# Default user encoding. Used to decode all input strings
# This is the central yokadi definition of encoding - this constant is imported from all other modules
# Beware of circular import definition when add dependencies to this module
ENCODING=locale.getpreferredencoding()

def editText(text):
    """Edit text with external editor
    @raise YokadiException: if editor cannot be started
    @return: newText"""
    (fd, name) = tempfile.mkstemp(suffix=".txt", prefix="yokadi-")
    try:
        try:
            fl = file(name, "w")
            fl.write(text.encode(ENCODING))
            fl.close()
            editor = os.environ.get("EDITOR", "vi")
            retcode = subprocess.call([editor, name])
            if retcode != 0:
                raise Exception()
            return unicode(file(name).read(), ENCODING)
        except:
            raise YokadiException("Starting editor failed")
    finally:
        os.close(fd)
        os.unlink(name)


def editLine(line, prompt="edit> "):
    """Edit a line using readline"""
    # Init readline
    # (Code copied from yagtd)
    def pre_input_hook():
        readline.insert_text(line.encode(ENCODING))
        readline.redisplay()

        # Unset the hook again
        readline.set_pre_input_hook(None)

    readline.set_pre_input_hook(pre_input_hook)

    line = raw_input(prompt)
    # Remove edited line from history:
    #   oddly, get_history_item is 1-based,
    #   but remove_history_item is 0-based
    length = readline.get_current_history_length()
    if length > 0:
        readline.remove_history_item(length - 1)

    return line.decode(ENCODING)


def selectFromList(prompt, lst, default):
    for score, caption in lst:
        print "%d: %s" % (score, caption)
    minStr = str(lst[0][0])
    maxStr = str(lst[-1][0])
    if default is None:
        line = ""
    else:
        line = str(default)
    while True:
        answer = editLine(line, prompt = prompt + ": ")
        if minStr <= answer and answer <= maxStr:
            return int(answer)
        print C.BOLD+C.RED+"ERROR: Wrong value"+C.RESET


def enterInt(prompt, default):
    if default is None:
        line = ""
    else:
        line = str(default)
    while True:
        answer = editLine(line, prompt = prompt + ": ")
        if answer == "":
            return None
        try:
            value = int(answer)
            return value
        except ValueError:
            print C.BOLD+C.RED+"ERROR: Wrong value"+C.RESET


def confirm(prompt):
    while True:
        answer = editLine("", prompt = prompt + " (y/n)? ")
        answer = answer.lower()

        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print C.BOLD+C.RED+"ERROR: Wrong value"+C.RESET
# vi: ts=4 sw=4 et
