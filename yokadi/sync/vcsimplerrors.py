from yokadi.core.yokadiexception import YokadiException


class VcsImplError(YokadiException):
    pass


class NotFastForwardError(VcsImplError):
    pass
