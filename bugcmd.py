import parseutils
import utils

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

def selectFromList(prompt, lst):
    for score, caption in lst:
        print "%d: %s" % (score, caption)
    minStr = str(lst[0][0])
    maxStr = str(lst[-1][0])
    while True:
        answer = raw_input(prompt + ": ")
        if minStr <= answer and answer <= maxStr:
            return int(answer)
        print "ERROR: Wrong value"


def enterInt(prompt):
    while True:
        answer = raw_input(prompt + ": ")
        if answer == "":
            return None
        try:
            value = int(answer)
            return value
        except ValueError:
            print "ERROR: Invalid value"


class BugCmd(object):
    def __init__(self):
        for name in PROPERTY_NAMES:
            utils.getOrCreateProperty(name, interactive=False)


    def do_bug_add(self, line):
        """Add a bug-type task. Will create a task and ask additional info.
        bug_add projectName [-p property1] [-p property2] Bug description
        """
        title, propertyDict = parseutils.parseTaskLine(line)
        severity = selectFromList("Severity", SEVERITY_LIST)
        likelihood = selectFromList("Likelihood", LIKELIHOOD_LIST)
        bug = enterInt("bug")

        propertyDict[BUG_PROPERTY_NAME] = bug

        if severity:
            propertyDict[SEVERITY_PROPERTY_NAME] = severity

        if likelihood:
            propertyDict[LIKELIHOOD_PROPERTY_NAME] = likelihood

        task = utils.addTask(title, propertyDict)
        if not task:
            return

        maxUrgency = LIKELIHOOD_LIST[-1][0] * SEVERITY_LIST[-1][0]
        task.urgency = 100 * likelihood * severity / maxUrgency

        print "Added bug '%s' (id=%d, urgency=%d)" % (title, task.id, task.urgency)

# vi: ts=4 sw=4 et
