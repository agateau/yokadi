# -*- coding: UTF-8 -*-
"""
Parse utilities. Used to manipulate command line text.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
import re

from db import Config, TaskKeyword, ProjectKeyword, Keyword
from sqlobject import AND, NOT
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
    @return: a tuple of ("project", "some text some other text", keywordDict"""

    # First extract project name
    line = simplifySpaces(line)
    if line.count(" "):
        project, line = line.split(" ", 1)
    else:
        project = line
        line = ""

    line, keywordFilters = extractKeywords(line)

    return project, line, keywordFiltersToDict(keywordFilters)

def extractKeywords(line):
    """Extract keywords (@k1 @k2=n..) from line
    @param line: line from which keywords are extracted
    @returns: (remaining_text, keywordFilters)"""
    keywordFilters = []
    remainingText=[]
    for token in line.split():
        if token.startswith("@"):
            keywordFilters.append(KeywordFilter(token))
        else:
            remainingText.append(token)

    return (u" ".join(remainingText), keywordFilters)

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

def keywordFiltersToDict(keywordFilters):
    """Convert a list of KeywordFilter instnance to a simple keyword dictionary"""
    keywordDict={}
    for keywordFilter in keywordFilters:
        keywordDict[keywordFilter.name] = keywordFilter.value
    return keywordDict

class KeywordFilter(object):
    """Represent a filter on a keyword"""
    def __init__(self, filterLine=None, keywordClass=TaskKeyword):
        self.name=None          # Keyword name
        self.value=None         # Keyword value
        self.negative=False     # Negative filter
        self.valueOperator="="  # Operator to compare value
        self.keywordClass=keywordClass # TaskKeyword or ProjectKeyword class handler

        if filterLine:
            self.parse(filterLine)

    def __str__(self):
        """Represent keyword filter as a string. Identical to what parse() method wait for"""
        if self.negative:
            prefix="!@"
        else:
            prefix="@"
        if self.value:
            return prefix+self.name+self.valueOperator+str(self.value)
        else:
            return prefix+self.name

    def filter(self):
        """Return a filter in SQlObject format"""
        filters=[self.keywordClass.q.keywordID==Keyword.q.id,]
        if self.name:
            filters.append(Keyword.q.name==self.name)
        if self.value:
            #TODO: take care of operator - use only equal for now
            filters.append(self.keywordClass.q.value==self.value)
        if filters:
            if self.negative:
                return NOT(AND(*filters))
            else:
                return AND(*filters)

    def parse(self, line):
        """Parse given line to create a keyword filter"""
        keywordDict = {}
        operators = ("=<", ">=", "!=", "<", ">", "=")
        if " " in line:
            tui.error("No space in keyword filter !")
            return
        if line.startswith("!"):
            self.negative=True
            line=line[1:]
        if not line.startswith("@"):
            tui.error("Keyword name must be be prefixed with a @")
            return
        line=line[1:] # Squash @
        for operator in operators:
            if operator in line:
                self.name, self.value = line.split(operator, 1)
                self.valueOperator = operator
                try:
                    self.value = int(self.value)
                except ValueError:
                    tui.error("Keyword value must be an integer (got %s)" %
                              (self.value, self.name))
                    return
                break # Exit operator loop
        else:
            # No operator found, only keyword name has been provided
            self.name, self.value = line, None

# vi: ts=4 sw=4 et