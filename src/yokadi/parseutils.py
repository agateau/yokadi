# -*- coding: UTF-8 -*-
"""
Parse utilities. Used to manipulate command line text.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
import re

from db import Config
import tui

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


def parseLine(line):
    """Parse line of form:
    project some text @keyword1 @keyword2=12 some other text
    @return: a tuple of ("project", "some text some other text", {keyword1: None, keyword2:12})"""

    # First extract project name
    line = simplifySpaces(line)
    if line.count(" "):
        project, line = line.split(" ", 1)
    else:
        project = line
        line = ""

    line, keywordDict = extractKeywords(line)

    return project, line, keywordDict

def extractKeywords(line):
    """Extract keywords (@k1 @k2=n..) from line
    @param line: line from which keywords are extracted
    @returns: (remaining_text, {keywordDict})"""
    keywordDict = {}
    remainingText=[]
    for token in line.split():
        if token.startswith("@"):
            token=token[1:]
            if "=" in token:
                keyword, value = token.split("=", 1)
                try:
                    value = int(value)
                except ValueError:
                    tui.error("Keyword value must be an integer (got %s). Removing value for %s keyword" %
                              (value, keyword))
                    value = None
            else:
                keyword, value = token, None
            keywordDict[keyword] = value
        else:
            remainingText.append(token)

    return (u" ".join(remainingText), keywordDict)

def createLine(projectName, title, keywordDict):
    tokens = []
    for keywordName, value in keywordDict.items():
        if value:
            tokens.append("@" + keywordName + "=" + str(value))
        else:
            tokens.append("@" + keywordName)

    if projectName:
        tokens.insert(0, projectName)

    tokens.append(title)
    return u" ".join(tokens)
# vi: ts=4 sw=4 et
