"""
Functions to dump a database to a dir handled by a VcsImpl

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import json
import os
import shutil

from collections import namedtuple

from yokadi.core import db
from yokadi.core import dbs13n
from yokadi.core.yokadiexception import YokadiException
from yokadi.core.db import Task, Project, Alias, TaskKeyword
from yokadi.sync import VERSION, VERSION_FILENAME, ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME


TableInfo = namedtuple("TableInfo", ("table", "dirname", "dictFromObject"))


_TABLE_INFO = (
    TableInfo(Task, TASKS_DIRNAME, dbs13n.dictFromTask),
    TableInfo(Project, PROJECTS_DIRNAME, dbs13n.dictFromProject),
    TableInfo(Alias, ALIASES_DIRNAME, dbs13n.dictFromAlias),
)


_DIRNAME_FOR_TABLE = dict((x.table.__table__, x.dirname) for x in _TABLE_INFO)


_DICT_FCN_FOR_TABLE = dict((x.table.__table__, x.dictFromObject) for x in _TABLE_INFO)


_JSON_DUMP_ARGS = dict(indent=2, sort_keys=True)


def jsonDumps(dct):
    """Dump a dict to a string using Yokadi formatting"""
    return json.dumps(dct, **_JSON_DUMP_ARGS)


def jsonDump(dct, fp):
    """Dump a dict to a file using Yokadi formatting"""
    return json.dump(dct, fp, **_JSON_DUMP_ARGS)


def dirnameForObject(obj):
    """Returns the dirname for obj. Can return None if this is not a serialized object,
    such as a TaskKeyword object"""
    return _DIRNAME_FOR_TABLE.get(obj.__table__)


def pathForObject(obj):
    dirname = dirnameForObject(obj)
    return os.path.join(dirname, obj.uuid + '.json')


def dictFromObject(obj):
    """Returns a serializable dict version of an object"""
    fcn = _DICT_FCN_FOR_TABLE[obj.__table__]
    return fcn(obj)


def createVersionFile(dstDir):
    versionFile = os.path.join(dstDir, VERSION_FILENAME)
    with open(versionFile, "w") as fp:
        fp.write(str(VERSION))


def checkIsValidDumpDir(dstDir, vcsImpl):
    if not vcsImpl.isValidVcsDir():
        raise YokadiException("{} is not handled by {}".format(dstDir, vcsImpl.name))

    versionFile = os.path.join(dstDir, VERSION_FILENAME)
    if not os.path.exists(versionFile):
        raise YokadiException("{} does not contain a `{}` file".format(dstDir, VERSION_FILENAME))

    with open(versionFile) as fp:
        dumpVersion = int(fp.read())
    if dumpVersion != VERSION:
        raise YokadiException("Cannot use a dump dir at version {}, expected version {}."
            .format(dumpVersion, VERSION))


def clearDump(dstDir):
    for dirname in ALIASES_DIRNAME, PROJECTS_DIRNAME, TASKS_DIRNAME:
        path = os.path.join(dstDir, dirname)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


def dumpObjectDict(dct, dumpDictDir):
    """Given a dict representing an object and a complete dir where to dump
    (dumpDir/$objdir), write the JSON file"""

    # dumpDir may not exist if we cloned a database which does not contain any
    # object of the type of dct (for example, no aliases)
    os.makedirs(dumpDictDir, exist_ok=True)

    uuid = dct["uuid"]
    path = os.path.join(dumpDictDir, uuid + ".json")
    with open(path, "wt") as fp:
        json.dump(dct, fp, indent=2, sort_keys=True)


def dumpObject(obj, dumpDir):
    dirname = dirnameForObject(obj)
    dumpDictDir = os.path.join(dumpDir, dirname)
    dct = dictFromObject(obj)
    dumpObjectDict(dct, dumpDictDir)


def getLinkedObject(obj):
    """If an object is dumped as part of another object, return this other
    object or None if the object is supposed to be dumped as is"""
    if obj.__table__ is TaskKeyword.__table__:
        return obj.task
    return None


def isDumpableObject(obj):
    """Returns True if the object can be dumped, either directly or via its
    linked object"""
    if getLinkedObject(obj):
        return True
    return obj.__table__ in _DIRNAME_FOR_TABLE


def dump(dumpDir, vcsImpl=None):
    assert os.path.exists(dumpDir), "dumpDir {} does not exist".format(dumpDir)
    vcsImpl.setDir(dumpDir)
    checkIsValidDumpDir(dumpDir, vcsImpl)

    session = db.getSession()
    for project in session.query(Project).all():
        dumpObject(project, dumpDir)
    for task in session.query(Task).all():
        dumpObject(task, dumpDir)
    for alias in session.query(Alias).all():
        dumpObject(alias, dumpDir)

    if not vcsImpl.isWorkTreeClean():
        vcsImpl.commitAll("Dumped")
