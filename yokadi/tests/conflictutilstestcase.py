"""
Test cases for conflictutils

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import textwrap

from yokadi.ycli.conflictutils import prepareConflictText
from yokadi.tests.yokaditestcase import YokadiTestCase


class ConflictUtilsTestCase(YokadiTestCase):
    def testPrepareConflictText(self):
        data = (
            ("foo", "bar", "L> foo\nR> bar\n"),
            (
                textwrap.dedent("""\
                    Common
                    Local1
                    More common
                    Local2
                    Local3
                    Even more common"""),
                textwrap.dedent("""\
                    Common
                    Remote1
                    More common
                    Remote2
                    Even more common"""),
                textwrap.dedent("""\
                    Common
                    L> Local1
                    R> Remote1
                    More common
                    R> Remote2
                    L> Local2
                    L> Local3
                    Even more common
                    """),
            )
        )

        for local, remote, expected in data:
            output = prepareConflictText(local, remote)
            self.assertEqual(output, expected)
