VERSION = 1
VERSION_FILENAME = "version"
PROJECTS_DIRNAME = "projects"
TASKS_DIRNAME = "tasks"

from .pull import pull
from .dump import dump
from .gitvcsimpl import GitVcsImpl


def push(dumpDir, vcsImpl=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dumpDir)
    vcsImpl.push()
