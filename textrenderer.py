class TextRenderer(object):
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
