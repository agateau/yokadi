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
        retcode = subprocess.call(["vim", name])
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
        readline.insert_text(line)
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

# vi: ts=4 sw=4 et
