import re


gSimplifySpaces = re.compile("  +")
def simplifySpaces(line):
    line = gSimplifySpaces.subn(" ", line)[0]
    line = line.strip()
    return line


gKeywordRe=re.compile("-k *([^ =]+)(?:=(\d+))?")
def parseTaskLine(line):
    """Parse line of form:
    project some text -k keyword1 -k keyword2=12 some other text
    returns a tuple of ("project", "some text some other text", {keyword1: None, keyword2:12})"""
    def fixKeywordValue(value):
        if value != '':
            return int(value)
        else:
            return None

    # First extract project name
    line = simplifySpaces(line)
    if line.count(" "):
        project, line = line.split(" ", 1)
        
    else:
        #TODO: if project name is not given use a default project (first one or configured one)
        print "Project name not given, using 'default' projet"
        project="default"

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
