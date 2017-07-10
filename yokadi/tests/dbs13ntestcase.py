"""
Serialization test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.core import db, dbs13n
from yokadi.tests.yokaditestcase import YokadiTestCase


class Dbs13nTestCase(YokadiTestCase):
    def setUp(self):
        YokadiTestCase.setUp(self)
        db.connectDatabase("", memoryDatabase=True)
        self.session = db.getSession()

    def testDictFromTask(self):
        project = db.Project(name="p")
        task = db.Task(title="t1", project=project, description="foo")
        self.session.add(task)
        self.session.flush()
        dct = dbs13n.dictFromTask(task)

        self.assertEqual(dct["title"], "t1")
        self.assertEqual(dct["description"], "foo")
        self.assertEqual(dct["project_uuid"], project.uuid)

        # Make sure the dump contains nullable fields
        self.assertIn("done_date", dct)
        self.assertIn("due_date", dct)
