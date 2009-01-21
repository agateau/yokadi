# -*- coding: UTF-8 -*-
"""
Helper functions to build CLI applications

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""

import os
import readline
import subprocess
import sys
import tempfile
import locale

import colors as C
from yokadiexception import YokadiException

# Default user encoding. Used to decode all input strings
# This is the central yokadi definition of encoding - this constant is imported from all other modules
# Beware of circular import definition when add dependencies to this module
ENCODING=locale.getpreferredencoding()

_answers = []
class IOStream:
    def __init__(self, original_flow):
        self.__original_flow = original_flow
        if sys.platform == 'win32':
            import pyreadline
            self.__console = pyreadline.GetOutputFile()
        
    def write(self, text):
        if sys.platform == 'win32':
            self.__console.write_color(text)
        else:
            self.__original_flow.write(text) 

class IOHandler:
    def __init__(self):
        self.stdout = IOStream(sys.stdout)
        self.stderr = IOStream(sys.stderr)
        self.stdin  = IOStream(sys.stdin)

yio = IOHandler()           # The one and only Yokaidi IO Handler


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

    if sys.platform != 'win32':
        readline.set_pre_input_hook(pre_input_hook)

    if len(_answers) > 0:
        line = _answers.pop(0)
    else:
        line = raw_input(prompt)

    # Remove edited line from history:
    #   oddly, get_history_item is 1-based,
    #   but remove_history_item is 0-based
    if sys.platform != 'win32':
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
        error("Wrong value")


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
            error("Wrong value")


def confirm(prompt):
    while True:
        answer = editLine("", prompt = prompt + " (y/n)? ")
        answer = answer.lower()

        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            error("Wrong value")


def renderFields(fields):
    """Print on screen tabular array represented by fields
    @param fields: list of tuple (caption, value)
    """
    maxWidth = max([len(x) for x,y in fields])
    format=C.BOLD+"%" + str(maxWidth) + "s"+C.RESET+": %s"
    for caption, value in fields:
        print >>yio.stdout, format % (caption, value)




def error(message):
    print >>yio.stderr, C.BOLD + C.RED + "Error: %s" % message + C.RESET


def warning(message):
    print >>yio.stderr, C.RED + "Warning: " + C.RESET + message


def info(message):
    print >>yio.stderr, C.CYAN + "Info: " + C.RESET + message


def addInputAnswers(*answers):
    """Add answers to tui internal answer buffer. Next call to editLine() will
    pop the first answer from the buffer instead of prompting the user.
    This is useful for unit-testing."""
    _answers.extend(answers)
# vi: ts=4 sw=4 et

