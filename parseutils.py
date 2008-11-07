# -*- coding: UTF-8 -*-
"""
Parse utilities. Used to manipulate command line text.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import re
from db import Config

gSimplifySpaces = re.compile("  +")
def simplifySpaces(line):
    line = gSimplifySpaces.subn(" ", line)[0]
    line = line.strip()
    return line

def parseParameters(line):
    """Parse line of form -a -b -c some text
    @return: ((a, b, c), some text)
    """
    parameters=[]
    text=[]
    line=simplifySpaces(line)
    for word in line.split():
        if word.startswith("-") and len(word)==2:
            parameters.append(word[1])
        else:
            text.append(word)
    return (parameters, " ".join(text))

def fixKeywordValue(value):
    if value != '':
        return int(value)
    else:
        return None

gKeywordRe=re.compile("-k *([^ =]+)(?:=(\d+))?")
def parseTaskLine(line):
    """Parse line of form:
    project some text -k keyword1 -k keyword2=12 some other text
    returns a tuple of ("project", "some text some other text", {keyword1: None, keyword2:12})"""

    # First extract project name
    line = simplifySpaces(line)
    if line.count(" "):
        project, line = line.split(" ", 1)
        
    else:
        project=Config.byName("DEFAULT_PROJECT").value
        print "Project name not given, using default project (%s)" % project

    # Extract keywords
    matches = gKeywordRe.findall(line)
    matches = [(x, fixKeywordValue(y)) for x,y in matches]
    keywordDict = dict(matches)

    # Erase keywords
    line = gKeywordRe.subn("", line)[0]
    line = simplifySpaces(line)
    return project, line, keywordDict


def createTaskLine(projectName, title, keywordDict):
    tokens = []
    for keywordName, value in keywordDict.items():
        tokens.append("-k")
        if value:
            tokens.append(keywordName + "=" + str(value))
        else:
            tokens.append(keywordName)

    tokens.insert(0, projectName)

    tokens.append(title)
    return " ".join(tokens)


def computeCompleteParameterPosition(text, line, begidx, endidx):
    before = simplifySpaces(line[:begidx].strip())
    return before.count(" ") + 1
# vi: ts=4 sw=4 et
