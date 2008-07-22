import os
import readline
import subprocess
import tempfile

def editText(text):
    """Edit text with external editor
    returns a tuple (success, newText)"""
    (fd, name) = tempfile.mkstemp(suffix=".txt", prefix="yokadi-")
    try:
        fl = file(name, "w")
        fl.write(text)
        fl.close()
        editor = os.environ.get("EDITOR", "vi")
        retcode = subprocess.call([editor, name])
        if retcode != 0:
            return (False, text)
        newText = file(name).read()
        return (True, newText)
    finally:
        os.close(fd)
        os.unlink(name)


def editLine(line, prompt="edit> "):
    """Edit a line using readline"""
    # Init readline
    # (Code copied from yagtd)
    def pre_input_hook():
        readline.insert_text(line.encode("utf-8"))
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

    return line


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
        print "ERROR: Wrong value"


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
            print "ERROR: Invalid value"
# vi: ts=4 sw=4 et
