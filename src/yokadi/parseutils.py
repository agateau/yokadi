# -*- coding: UTF-8 -*-
"""
Parse utilities. Used to manipulate command line text.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import re

from db import Config
from yokadioptionparser import YokadiOptionParser

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


def parseLine(line, useDefaultProject=True):
    """Parse line of form:
    project some text -k keyword1 -k keyword2=12 some other text
    @param useDefaultProject: if true, a single word will be interpreted as task description
    and the default project will be used.
    @return: a tuple of ("project", "some text some other text", {keyword1: None, keyword2:12})"""

    # First extract project name
    line = simplifySpaces(line)
    if line.split()[0][-1] == ":": # Last character of first word
        project, line = line.split(" ", 1)
        project = project[0:-1]
    elif useDefaultProject:
        project = Config.byName("DEFAULT_PROJECT").value
        print "Project name not given, using default project (%s)" % project
    else: # First word is project
        if line.count(" "):
            project, line = line.split(" ", 1)
        else:
            project = line
            line = ""

    line, keywordDict = extractKeywords(line)

    return project, line, keywordDict

def extractKeywords(line):
    """Extract keywords (-k k1 -k k2=n..) from line
    @param line: line from which keywords are extracted
    @returns: (remaining_text, {keywordDict})"""
    parser = YokadiOptionParser()
    parser.add_option("-k", dest="keyword", action="append")
    options, args = parser.parse_args(line)

    keywordDict = {}
    if options.keyword:
        for text in options.keyword:
            if "=" in text:
                keyword, value = text.split("=", 1)
                value = int(value)
            else:
                keyword, value = text, None
            keywordDict[keyword] = value

    return (u" ".join(args), keywordDict)

def createLine(projectName, title, keywordDict):
    tokens = []
    for keywordName, value in keywordDict.items():
        tokens.append(u"-k")
        if value:
            tokens.append(keywordName + "=" + str(value))
        else:
            tokens.append(keywordName)

    tokens.insert(0, projectName+":")

    tokens.append(title)
    return u" ".join(tokens)
# vi: ts=4 sw=4 et
