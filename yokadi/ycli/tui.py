# -*- coding: UTF-8 -*-
"""
Helper functions to build CLI applications

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""

import os
import readline
import subprocess
import sys
import tempfile
import time
import unicodedata
import re
import locale
import shutil
from collections import namedtuple
from getpass import getpass

from yokadi.ycli import colors
from yokadi.core.yokadiexception import YokadiException

# Number of seconds between checks for end of process
PROC_POLL_INTERVAL = 0.5
# Number of seconds between checks for file modification
MTIME_POLL_INTERVAL = 10

# Filter out bad characters for filenames
NON_SIMPLE_ASCII = re.compile("[^a-zA-Z0-9]+")
MULTIPLE_DASH = re.compile("-+")

_answers = []

stdout = sys.stdout
stderr = sys.stderr


_isInteractive = sys.stdin.isatty()


def isInteractive():
    if _answers:
        # We are in a test, interaction is being simulated
        return True
    return _isInteractive


def _checkIsInteractive():
    if not isInteractive():
        raise YokadiException("This command cannot be used in non-interactive mode")


def editText(text, onChanged=None, lockManager=None, prefix="yokadi-", suffix=".md"):
    """Edit text with external editor
    @param onChanged: function parameter that is call whenever edited data change. Data is given as a string
    @param lockManager: function parameter that is called to 'acquire', 'update' or 'release' an editing lock
    @param prefix: temporary file prefix.
    @param suffix: temporary file suffix.
    @return: newText"""
    _checkIsInteractive()
    encoding = locale.getpreferredencoding()

    def readFile(name):
        with open(name, encoding=encoding) as data:
            return str(data.read())

    def waitProcess(proc):
        start = time.time()
        while (time.time() - start) < MTIME_POLL_INTERVAL:
            proc.poll()
            if proc.returncode is not None:
                return
            time.sleep(PROC_POLL_INTERVAL)

    prefix = NON_SIMPLE_ASCII.sub("-", prefix)
    prefix = MULTIPLE_DASH.sub("-", prefix)
    prefix = unicodedata.normalize('NFKD', prefix)

    (fd, name) = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    if text is None:
        text = ""
    try:
        if lockManager:
            lockManager.acquire()
        fl = open(name, "w", encoding=encoding)
        fl.write(text)
        fl.close()
        editor = os.environ.get("EDITOR", "vi")
        proc = subprocess.Popen([editor, name])
        mtime = os.stat(name).st_mtime
        while proc.returncode is None:
            waitProcess(proc)
            if proc.returncode is None and lockManager is not None:
                lockManager.update()
            if proc.returncode is None and onChanged is not None:
                newMtime = os.stat(name).st_mtime
                if newMtime > mtime:
                    mtime = newMtime
                    onChanged(readFile(name))
        if proc.returncode != 0:
            raise Exception("The command {} failed. It exited with code {}.".format(proc.args, proc.returncode))
        return readFile(name)
    finally:
        os.close(fd)
        os.unlink(name)
        if lockManager:
            lockManager.release()


def reinjectInRawInput(line):
    """Next call to input() will have line set as default text
    @param line: The default text
    """
    assert isinstance(line, str)

    # Set readline.pre_input_hook to feed it with our line
    # (Code copied from yagtd)
    def pre_input_hook():
        readline.insert_text(line)
        readline.redisplay()

        # Unset the hook again
        readline.set_pre_input_hook(None)

    if sys.platform != 'win32':
        readline.set_pre_input_hook(pre_input_hook)


def editLine(line, prompt="edit> ", echo=True):
    """Edit a line using readline
    @param prompt: change prompt
    @param echo: whether to echo user text or not"""
    _checkIsInteractive()
    if line:
        reinjectInRawInput(line)

    if len(_answers) > 0:
        line = _answers.pop(0)
    else:
        try:
            if echo:
                line = input(prompt)
            else:
                line = getpass(prompt)
        except EOFError:
            line = ""

    # Remove edited line from history:
    #   oddly, get_history_item is 1-based,
    #   but remove_history_item is 0-based
    if sys.platform != 'win32':
        length = readline.get_current_history_length()
        if length > 0:
            readline.remove_history_item(length - 1)

    return line


def selectFromList(lst, default=None, prompt="Select", valueForString=int):
    """
    Takes a list of tuples (value, caption), returns the value of the selected
    entry.
    @param default indicates the default value and may be None
    @param prompt customize the prompt
    @param valueForString a function to turn a string into a valid value
    """
    if default is not None:
        default = str(default)
    possibleValues = {x[0] for x in lst}
    for value, caption in lst:
        print("{}: {}".format(value, caption))

    while True:
        line = editLine(default, prompt=prompt + ": ")
        try:
            value = valueForString(line)
        except Exception:
            error("Wrong value")
            continue

        if value in possibleValues:
            return value
        else:
            error("Wrong value")


def enterInt(default=None, prompt="Enter a number"):
    if default is None:
        line = ""
    else:
        line = str(default)
    while True:
        answer = editLine(line, prompt=prompt + ": ")
        if answer == "":
            return None
        try:
            value = int(answer)
            return value
        except ValueError:
            error("Wrong value")


def confirm(prompt):
    if not isInteractive():
        return True
    while True:
        answer = editLine("", prompt=prompt + " (y/n)? ")
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
    maxWidth = max([len(x) for x, y in fields])
    format = colors.BOLD + "%" + str(maxWidth) + "s" + colors.RESET + ": %s"
    for caption, value in fields:
        print(format % (caption, value), file=stdout)


def warnDeprecated(old, new):
    """Warn user that a command is now deprecated
    and incitate him to use the new one
    @param old: the old one (str)
    @param new: the new one (str)"""
    warning("Command '%s' is deprecated, use '%s' instead" % (old, new))
    info("Command %s has been executed" % new)


def error(message):
    print(colors.BOLD + colors.RED + "Error: %s" % message + colors.RESET, file=stderr)


def warning(message):
    print(colors.RED + "Warning: " + colors.RESET + message, file=stderr)


def info(message):
    print(colors.CYAN + "Info: " + colors.RESET + message, file=stderr)


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
    """Gets the terminal width"""
    size = shutil.get_terminal_size()
    return size.columns


ColorBlock = namedtuple("ColorBlock", ("pos", "color"))


class TextColorizer:
    def __init__(self):
        self._dct = {}

    def setColorAt(self, pos, color):
        self._dct[pos] = color

    def setResetAt(self, pos):
        self._dct[pos] = colors.RESET

    def crop(self, width):
        self._dct = {pos: color for pos, color in self._dct.items() if pos < width}

    def render(self, text):
        """
        Apply color blocks to text
        """
        start = 0
        out = []
        blockList = sorted(self._dct.items())
        for pos, color in blockList:
            out.append(text[start:pos] + color)
            start = pos
        # Add remaining text, if any
        out.append(text[start:])
        return "".join(out)
# vi: ts=4 sw=4 et
