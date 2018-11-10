# -*- coding: UTF-8 -*-
"""
HTML rendering of t_list output

@author: Aurélien Gâteau <mail@agateau.com>
@author: Sébastien Renard <sebastien.renard@digitalfox.org>
@license: GPL v3 or later
"""
import xml.sax.saxutils as saxutils

TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "urgency", "status", "description", "keywords"]


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

        # TODO: make this fancier
        print("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
                <html>
                <head>
                    <style>
                    td, th {
                        border: 1px solid #ccc;
                    }
                    </style>
                    <title>Yokadi tasks export</title>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                </head>
                <body>
                """, file=self.out)

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
        print("</body></html>", file=self.out)
# vi: ts=4 sw=4 et
