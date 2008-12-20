# -*- coding: UTF-8 -*-
"""
HTML rendering of t_list output

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPLv3
"""
import tui

TASK_FIELDS = ["title", "creationDate", "dueDate", "doneDate", "description", "urgency", "status", "project", "keywords"]

class HtmlListRenderer(object):
    def __init__(self, out):
        self.out = out

        #TODO: make this fancier
        self.out.write("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
                <html><head><title>Yokadi tasks export</title>
                <meta http-equiv="Content-Type" content="text/html; charset=%s">
                </head><body><table>""" % tui.ENCODING)

    def addTaskList(self, project, taskList):
        for task in taskList:
            self.out.write("<tr>\n")
            row=list("<td>%s</td>" % unicode(task.__getattribute__(field)) for field in TASK_FIELDS if field!="keywords")
            row.append("<td>%s</td>" % task.getKeywordsAsString())
            line=u" ".join(row)
            self.out.write(line.encode(tui.ENCODING))
            self.out.write("</tr>\n")

    def end(self):
        self.out.write("</table></body></html>\n")
# vi: ts=4 sw=4 et
