VERSION = 1
VERSION_FILENAME = "version"
PROJECTS_DIRNAME = "projects"
TASKS_DIRNAME = "tasks"
DB_SYNC_BRANCH = "db-synced"


from .pull import pull
from .dump import dump, initDumpRepository
from .gitvcsimpl import GitVcsImpl


def push(dumpDir, vcsImpl=None):
    if vcsImpl is None:
        vcsImpl = GitVcsImpl()
    vcsImpl.setDir(dumpDir)
    vcsImpl.push()
