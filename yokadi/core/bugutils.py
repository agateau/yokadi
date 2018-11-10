# -*- coding: UTF-8 -*-
"""
Bug related commands.

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.ycli import tui

SEVERITY_PROPERTY_NAME = "_severity"
LIKELIHOOD_PROPERTY_NAME = "_likelihood"
BUG_PROPERTY_NAME = "_bug"
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
    return int(100 * likelihood * severity / maxUrgency)


def editBugKeywords(keywordDict):
    severity = keywordDict.get(SEVERITY_PROPERTY_NAME, None)
    likelihood = keywordDict.get(LIKELIHOOD_PROPERTY_NAME, None)
    bug = keywordDict.get(BUG_PROPERTY_NAME, None)

    severity = tui.selectFromList(SEVERITY_LIST, prompt="Severity", default=severity)
    likelihood = tui.selectFromList(LIKELIHOOD_LIST, prompt="Likelihood", default=likelihood)
    bug = tui.enterInt(prompt="bug", default=bug)

    keywordDict[BUG_PROPERTY_NAME] = bug

    if severity:
        keywordDict[SEVERITY_PROPERTY_NAME] = severity

    if likelihood:
        keywordDict[LIKELIHOOD_PROPERTY_NAME] = likelihood
# vi: ts=4 sw=4 et
