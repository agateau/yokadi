import parseutils
import utils

class ProjectCompleter(object):
    def __init__(self, position):
        self.position = position


    def __call__(self, text, line, begidx, endidx):
        if parseutils.computeCompleteParameterPosition(text, line, begidx, endidx) == self.position:
            return utils.getProjectNamesStartingWith(text)
        else:
            return []

# vi: ts=4 sw=4 et
