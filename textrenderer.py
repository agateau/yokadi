TASK_LIST_FORMAT="%(id)-3s|%(title)-60s|%(status)-1s|%(creationDate)-19s"

class TextRenderer(object):
    def renderTaskListHeader(self):
        line = TASK_LIST_FORMAT % dict(id="ID", title="Title", status="S", creationDate="Date")
        print line
        print "-" * len(line)


    def renderTaskListRow(self, task):
        title = task.title
        if len(title) > 60:
            title = title[:59] + ">"

        status = task.status[0].upper()
        creationDate = task.creationDate

        print TASK_LIST_FORMAT % dict(id=str(task.id), title=title, status=status, creationDate=creationDate)


    def renderTaskDetails(self, task):
        keywords = ", ".join([x.name for x in task.keywords])
        fields = [
            ("Title", task.title),
            ("Created", task.creationDate),
            ("Status", task.status),
            ("Keywords", keywords),
            ]

        maxWidth = max([len(x) for x,y in fields])
        format="%" + str(maxWidth) + "s: %s"
        for caption, value in fields:
            print format % (caption, value)
