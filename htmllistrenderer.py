# -*- coding: UTF-8 -*-
"""
HTML rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "description", "urgency", "status", "project", "keywords"]

class HtmlListRenderer(object):
    def __init__(self, out):
        self.out = out

        #TODO: make this fancier
        self.out.write("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
                <html>
                <head>
                    <title>Yokadi tasks export</title>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                </head>
                <body>
                <table>
                """)

    def addTaskList(self, project, taskList):
        for task in taskList:
            self.out.write("<tr>\n")
            row = ["<td>%s</td>" % unicode(getattr(task, field)) for field in TASK_FIELDS if field!="keywords"]
            row.append("<td>%s</td>" % task.getKeywordsAsString())
            line=u" ".join(row)
            self.out.write(line.encode("utf-8"))
            self.out.write("</tr>\n")

    def end(self):
        self.out.write("</table></body></html>\n")
# vi: ts=4 sw=4 et
