"""
VcsImpl exceptions

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.core.yokadiexception import YokadiException


class VcsImplError(YokadiException):
    pass


class NotFastForwardError(VcsImplError):
    pass


class CantCommitWithConflictsError(VcsImplError):
    pass
