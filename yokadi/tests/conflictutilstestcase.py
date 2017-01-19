"""
Test cases for conflictutils

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import textwrap

from yokadi.ycli.conflictutils import prepareConflictText, CONFLICT_BEGIN, CONFLICT_MIDDLE, CONFLICT_END
from yokadi.tests.yokaditestcase import YokadiTestCase


class ConflictUtilsTestCase(YokadiTestCase):
    def testPrepareConflictText(self):
        data = (
            (
                "foo",
                "bar",
                textwrap.dedent("""\
                    {begin}
                    foo
                    {mid}
                    bar
                    {end}
                    """.format(begin=CONFLICT_BEGIN, mid=CONFLICT_MIDDLE, end=CONFLICT_END)),
            ),
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
                    {begin}
                    Local1
                    {mid}
                    Remote1
                    {end}
                    More common
                    {begin}
                    {mid}
                    Remote2
                    {end}
                    {begin}
                    Local2
                    Local3
                    {mid}
                    {end}
                    Even more common
                    """.format(begin=CONFLICT_BEGIN, mid=CONFLICT_MIDDLE, end=CONFLICT_END)),
            ),
        )

        for local, remote, expected in data:
            output = prepareConflictText(local, remote)
            self.assertEqual(output, expected)
