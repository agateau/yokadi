"""
Synchronization exceptions

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
from yokadi.core.yokadiexception import YokadiException


class SyncError(YokadiException):
    pass


class MergeError(SyncError):
    pass
