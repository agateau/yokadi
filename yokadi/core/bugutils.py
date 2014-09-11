# -*- coding: UTF-8 -*-
"""
Bug related commands.

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
from yokadi.ycli import tui

SEVERITY_PROPERTY_NAME = u"_severity"
LIKELIHOOD_PROPERTY_NAME = u"_likelihood"
BUG_PROPERTY_NAME = u"_bug"
PROPERTY_NAMES = SEVERITY_PROPERTY_NAME, LIKELIHOOD_PROPERTY_NAME, BUG_PROPERTY_NAME

SEVERITY_LIST = [
    (1, u"Documentation"),
    (2, u"Localization"),
    (3, u"Aesthetic issues"),
    (4, u"Balancing: Enables degenerate usage strategies that harm the experience"),
    (5, u"Minor usability: Impairs usability in secondary scenarios"),
    (6, u"Major usability: Impairs usability in key scenarios"),
    (7, u"Crash: Bug causes crash or data loss. Asserts in the Debug release"),
    ]

LIKELIHOOD_LIST = [
    (1, u"Will affect almost no one"),
    (2, u"Will only affect a few users"),
    (3, u"Will affect average number of users"),
    (4, u"Will affect most users"),
    (5, u"Will affect all users"),
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
# vi: ts=4 sw=4 et
