# -*- coding: UTF-8 -*-
"""
Bug related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import parseutils
import dbutils
import tui
from completers import ProjectCompleter

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

def computeUrgency(keywordDict):
    likelihood = keywordDict[LIKELIHOOD_PROPERTY_NAME]
    severity = keywordDict[SEVERITY_PROPERTY_NAME]
    maxUrgency = LIKELIHOOD_LIST[-1][0] * SEVERITY_LIST[-1][0]
    return 100 * likelihood * severity / maxUrgency


def editBugKeywords(keywordDict):
    severity = keywordDict.get(SEVERITY_PROPERTY_NAME, None)
    likelihood = keywordDict.get(LIKELIHOOD_PROPERTY_NAME, None)
    bug = keywordDict.get(BUG_PROPERTY_NAME, None)

    severity = tui.selectFromList("Severity", SEVERITY_LIST, severity)
    likelihood = tui.selectFromList("Likelihood", LIKELIHOOD_LIST, likelihood)
    bug = tui.enterInt("bug", bug)

    keywordDict[BUG_PROPERTY_NAME] = bug

    if severity:
        keywordDict[SEVERITY_PROPERTY_NAME] = severity

    if likelihood:
        keywordDict[LIKELIHOOD_PROPERTY_NAME] = likelihood


class BugCmd(object):
    def __init__(self):
        for name in PROPERTY_NAMES:
            dbutils.getOrCreateKeyword(name, interactive=False)


    def do_bug_add(self, line):
        """Add a bug-type task. Will create a task and ask additional info.
        bug_add <project_name> [-k <keyword1>] [-k <keyword2>] <Bug description>
        """
        projectName, title, keywordDict = parseutils.parseTaskLine(line)
        editBugKeywords(keywordDict)

        task = dbutils.addTask(projectName, title, keywordDict)
        if not task:
            return

        task.urgency = computeUrgency(keywordDict)

        print "Added bug '%s' (id=%d, urgency=%d)" % (title, task.id, task.urgency)

    complete_bug_add = ProjectCompleter(1)


    def do_bug_edit(self, line):
        """Edit a bug.
        bug_edit <id>"""
        task = dbutils.getTaskFromId(line)

        # Create task line
        taskLine = parseutils.createTaskLine(task.project.name, task.title, task.getKeywordDict())

        # Edit
        line = tui.editLine(taskLine)
        projectName, title, keywordDict = parseutils.parseTaskLine(line)
        editBugKeywords(keywordDict)

        # Update bug
        if not dbutils.createMissingKeywords(keywordDict.keys()):
            return
        task.project = dbutils.getOrCreateProject(projectName)
        task.title = title
        task.setKeywordDict(keywordDict)
        task.urgency = computeUrgency(keywordDict)

# vi: ts=4 sw=4 et
