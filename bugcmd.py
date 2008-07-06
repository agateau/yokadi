import parseutils
import utils
from db import *

SEVERITY_PROPERTY_NAME = "severity"
LIKELIHOOD_PROPERTY_NAME = "likelihood"
BUG_PROPERTY_NAME = "bug"
PROPERTY_NAMES = SEVERITY_PROPERTY_NAME, LIKELIHOOD_PROPERTY_NAME, BUG_PROPERTY_NAME

SEVERITY_LIST = [
    (1, "Documentation"),
    (2, "Localization"),
    (3, "Aesthetic issues"),
    (4, "Balancing: Enables degenerate usage strategies that harm the experience"),
    (5, "Minor usability: Impairs usability in secondary scenarios"),
    (6, "Major usability: Impairs usability in key scenarios"),
    (7, "Crash: Bug causes crash or data loss. Asserts in the Debug release"),
    ]

LIKELIHOOD_LIST = [
    (1, "Will affect almost no one"),
    (2, "Will only affect a few users"),
    (3, "Will affect average number of users"),
    (4, "Will affect most users"),
    (5, "Will affect all users"),
    ]

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
        answer = utils.editLine(line, prompt = prompt + ": ")
        if minStr <= answer and answer <= maxStr:
            return int(answer)
        print "ERROR: Wrong value"


def enterInt(prompt, default):
    if default is None:
        line = ""
    else:
        line = str(default)
    while True:
        answer = utils.editLine(line, prompt = prompt + ": ")
        if answer == "":
            return None
        try:
            value = int(answer)
            return value
        except ValueError:
            print "ERROR: Invalid value"


def computeUrgency(propertyDict):
    likelihood = propertyDict[LIKELIHOOD_PROPERTY_NAME]
    severity = propertyDict[SEVERITY_PROPERTY_NAME]
    maxUrgency = LIKELIHOOD_LIST[-1][0] * SEVERITY_LIST[-1][0]
    return 100 * likelihood * severity / maxUrgency


def editBugProperties(propertyDict):
    severity = propertyDict.get(SEVERITY_PROPERTY_NAME, None)
    likelihood = propertyDict.get(LIKELIHOOD_PROPERTY_NAME, None)
    bug = propertyDict.get(BUG_PROPERTY_NAME, None)

    severity = selectFromList("Severity", SEVERITY_LIST, severity)
    likelihood = selectFromList("Likelihood", LIKELIHOOD_LIST, likelihood)
    bug = enterInt("bug", bug)

    propertyDict[BUG_PROPERTY_NAME] = bug

    if severity:
        propertyDict[SEVERITY_PROPERTY_NAME] = severity

    if likelihood:
        propertyDict[LIKELIHOOD_PROPERTY_NAME] = likelihood


class BugCmd(object):
    def __init__(self):
        for name in PROPERTY_NAMES:
            utils.getOrCreateProperty(name, interactive=False)


    def do_bug_add(self, line):
        """Add a bug-type task. Will create a task and ask additional info.
        bug_add projectName [-p property1] [-p property2] Bug description
        """
        projectName, title, propertyDict = parseutils.parseTaskLine(line)
        editBugProperties(propertyDict)

        task = utils.addTask(projectName, title, propertyDict)
        if not task:
            return

        task.urgency = computeUrgency(propertyDict)

        print "Added bug '%s' (id=%d, urgency=%d)" % (title, task.id, task.urgency)


    def do_bug_edit(self, line):
        """Edit a bug.
        bug_edit id"""
        taskId = int(line)
        task = Task.get(taskId)

        # Create task line
        taskLine = parseutils.createTaskLine(task.project.name, task.title, task.getPropertyDict())

        # Edit
        line = utils.editLine(taskLine)
        projectName, title, propertyDict = parseutils.parseTaskLine(line)
        editBugProperties(propertyDict)

        # Update bug
        if not utils.createMissingProperties(propertyDict.keys()):
            return
        task.project = utils.getOrCreateProject(projectName)
        task.title = title
        task.setPropertyDict(propertyDict)
        task.urgency = computeUrgency(propertyDict)

# vi: ts=4 sw=4 et
