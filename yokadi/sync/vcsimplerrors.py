from yokadi.core.yokadiexception import YokadiException


class VcsImplError(YokadiException):
    @classmethod
    def fromSubprocessError(cls, err):
        msg = "Command {} failed with error code {}. Output:\n{}" \
            .format(err.cmd, err.returncode, err.output)
        return cls(msg)


class NotFastForwardError(VcsImplError):
    pass
