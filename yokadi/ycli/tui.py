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
import time
import unicodedata
import re
import locale
from getpass import getpass

from yokadi.ycli import colors as C

# Number of seconds between checks for end of process
PROC_POLL_INTERVAL = 0.5
# Number of seconds between checks for file modification
MTIME_POLL_INTERVAL = 10

# Filter out bad characters for filenames
NON_SIMPLE_ASCII = re.compile("[^a-zA-Z0-9]+")
MULTIPLE_DASH = re.compile("-+")

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


def editText(text, onChanged=None, lockManager=None, prefix="yokadi-"):
    """Edit text with external editor
    @param onChanged: function parameter that is call whenever edited data change. Data is given as a string
    @param lockManager: function parameter that is called to 'acquire', 'update' or 'release' an editing lock
    @param prefix: temporary file prefix.
    @return: newText"""
    encoding = locale.getpreferredencoding()
    def readFile(name):
        with open(name, encoding=encoding) as data:
            return str(data.read())

    def waitProcess(proc):
        start = time.time()
        while (time.time() - start) < MTIME_POLL_INTERVAL:
            proc.poll()
            if not proc.returncode is None:
                return
            time.sleep(PROC_POLL_INTERVAL)
    prefix = NON_SIMPLE_ASCII.sub("-", prefix)
    prefix = MULTIPLE_DASH.sub("-", prefix)
    prefix = unicodedata.normalize('NFKD', prefix)

    (fd, name) = tempfile.mkstemp(suffix=".md", prefix=prefix)
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
            raise Exception()
        return readFile(name)
    finally:
        os.close(fd)
        os.unlink(name)
        if lockManager:
            lockManager.release()


def reinjectInRawInput(line):
    """Next call to raw_input() will have line set as default text
    @param line: The default text
    """

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


def selectFromList(prompt, lst, default):
    for score, caption in lst:
        print("%d: %s" % (score, caption))
    minStr = str(lst[0][0])
    maxStr = str(lst[-1][0])
    if default is None:
        line = ""
    else:
        line = str(default)
    while True:
        answer = editLine(line, prompt=prompt + ": ")
        if minStr <= answer and answer <= maxStr:
            return int(answer)
        error("Wrong value")


def enterInt(prompt, default):
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
    format = C.BOLD + "%" + str(maxWidth) + "s" + C.RESET + ": %s"
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
    print(C.BOLD + C.RED + "Error: %s" % message + C.RESET, file=stderr)


def warning(message):
    print(C.RED + "Warning: " + C.RESET + message, file=stderr)


def info(message):
    print(C.CYAN + "Info: " + C.RESET + message, file=stderr)


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
    width = 120
    if os.name == "posix":
        result = subprocess.Popen(["tput", "cols"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
        result = result.strip()
        if result.isdigit():
            width = int(result)
    return width

# vi: ts=4 sw=4 et
