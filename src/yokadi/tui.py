# -*- coding: UTF-8 -*-
"""
Helper functions to build CLI applications

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import os
import readline
import subprocess
import sys
import tempfile
import locale

import colors as C

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

stdout = IOStream(sys.stdout)
stderr = IOStream(sys.stderr)


def editText(text):
    """Edit text with external editor
    @return: newText"""
    (fd, name) = tempfile.mkstemp(suffix=".txt", prefix="yokadi-")
    try:
        fl = file(name, "w")
        fl.write(text.encode(ENCODING))
        fl.close()
        editor = os.environ.get("EDITOR", "vi")
        retcode = subprocess.call([editor, name])
        if retcode != 0:
            raise Exception()
        return unicode(file(name).read(), ENCODING)
    finally:
        os.close(fd)
        os.unlink(name)


def reinjectInRawInput(line):
    """Next call to raw_input() will have line set as default text
    @param line: The default text
    """

    # Set readline.pre_input_hook to feed it with our line
    # (Code copied from yagtd)
    def pre_input_hook():
        readline.insert_text(line.encode(ENCODING))
        readline.redisplay()

        # Unset the hook again
        readline.set_pre_input_hook(None)

    if sys.platform != 'win32':
        readline.set_pre_input_hook(pre_input_hook)


def editLine(line, prompt="edit> "):
    """Edit a line using readline"""
    if line:
       reinjectInRawInput(line)

    if len(_answers) > 0:
        line = _answers.pop(0)
    else:
        try:
            line = raw_input(prompt)
        except EOFError:
            line=""

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
        print >>stdout, format % (caption, value)

def warnDeprecated(old, new):
    """Warn user that a command is now deprecated
    and incitate him to use the new one
    @param old: the old one (str)
    @param new: the new one (str)"""
    warning("Command '%s' is deprecated, use '%s' instead" % (old, new))
    info("Command %s has been executed" % new)


def error(message):
    print >>stderr, C.BOLD + C.RED + "Error: %s" % message + C.RESET


def warning(message):
    print >>stderr, C.RED + "Warning: " + C.RESET + message


def info(message):
    print >>stderr, C.CYAN + "Info: " + C.RESET + message


def addInputAnswers(*answers):
    """Add answers to tui internal answer buffer. Next call to editLine() will
    pop the first answer from the buffer instead of prompting the user.
    This is useful for unit-testing."""
    _answers.extend(answers)


def clearInputAnswers():
    """Remove all added answers. Useful to avoid making a test depend on a "y"
    added by another test.
    """
    global _answers
    _answers = []


def getTermWidth():
    """Gets the terminal width. Works only on Unix system.
    @return: terminal width or "120" is system not supported
    Kindly borrowed from pysql code"""
    if os.name=="posix":
        result=os.popen("tput cols").readline().strip()
        if result:
            return int(result)
    else:
        # Unsupported system, use default 120
        return 120

# vi: ts=4 sw=4 et
