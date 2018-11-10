# -*- coding: UTF-8 -*-
"""
HTML rendering of t_list output

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import xml.sax.saxutils as saxutils

TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "urgency", "status", "description", "keywords"]


HTML_HEADER = """
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'>
    <style>
        table {
            border-collapse: collapse;
        }
        td, th {
            border: 1px solid #ccc;
            padding: 0.5em;
        }
    </style>
    <title>Yokadi tasks export</title>
</head>
<body>
"""


HTML_FOOTER = "</body></html>"


def escape(text):
    return saxutils.escape(str(text))


def printRow(out, tag, lst):
    print("<tr>", file=out)
    for value in lst:
        text = escape(value) or "&nbsp;"
        print("<%s>%s</%s>" % (tag, text, tag), file=out)
    print("</tr>", file=out)


class HtmlListRenderer(object):
    def __init__(self, out, cryptoMgr):
        self.out = out
        self.cryptoMgr = cryptoMgr

        print(HTML_HEADER, file=self.out)

    def addTaskList(self, sectionName, taskList):
        """Store tasks for this section
        @param sectionName: name of the task groupement section
        @type sectionName: unicode
        @param taskList: list of tasks to display
        @type taskList: list of db.Task instances
        """

        print("<h1>%s</h1>" % escape(sectionName), file=self.out)
        print("<table width='100%'>", file=self.out)
        printRow(self.out, "th", TASK_FIELDS)
        for task in taskList:
            lst = [self.cryptoMgr.decrypt(task.title), ]
            lst.extend([getattr(task, x) for x in TASK_FIELDS if x not in ("title", "description", "keywords")])
            lst.append(self.cryptoMgr.decrypt(task.description))
            lst.append(task.getKeywordsAsString())
            printRow(self.out, "td", lst)
        print("</table>", file=self.out)

    def end(self):
        print(HTML_FOOTER, file=self.out)
# vi: ts=4 sw=4 et
