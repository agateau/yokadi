"""
Handling of common command line arguments

@author: Aurelien Gateau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import sys
import yokadi
from yokadi.core import basepaths
from yokadi.ycli import tui


def addArgs(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--datadir', dest='dataDir', help='Database dir (default: %s)' % basepaths.getDataDir(),
                       metavar='DATADIR')
    group.add_argument('-d', '--db', dest='dbPath',
                       help='TODO database (default: {}). This option is deprecated and will be removed in the next'
                       ' version of Yokadi. Use --datadir instead.'
                       .format(os.path.join('$DATADIR', basepaths.DB_NAME)),
                       metavar='FILE')
    parser.add_argument('-v', '--version', dest='version', action='store_true', help='Display Yokadi current version')


def processDataDirArg(dataDir):
    if dataDir:
        dataDir = os.path.abspath(dataDir)
        if not os.path.isdir(dataDir):
            tui.error("Directory '{}' does not exist".format(dataDir))
            sys.exit(1)
    else:
        dataDir = basepaths.getDataDir()
        os.makedirs(dataDir, exist_ok=True)
    return dataDir


def processDbPathArg(dbPath, dataDir):
    if not dbPath:
        return basepaths.getDbPath(dataDir)
    dbPath = os.path.abspath(dbPath)
    dbDir = os.path.dirname(dbPath)
    tui.warning('--db option is deprecated and will be removed in the next version, use --datadir instead')
    if not os.path.isdir(dbDir):
        tui.error("Directory '{}' does not exist".format(dbDir))
        sys.exit(1)
    return dbPath


def warnYokadiDbEnvVariable():
    if os.getenv('YOKADI_DB'):
        tui.warning('The YOKADI_DB environment variable is deprecated and will be removed in the next version, use the'
                    ' --datadir command-line option instead')


def processArgs(args):
    if args.version:
        print('Yokadi - {}'.format(yokadi.__version__))
        sys.exit(0)
    warnYokadiDbEnvVariable()
    dataDir = processDataDirArg(args.dataDir)
    dbPath = processDbPathArg(args.dbPath, dataDir)
    return dataDir, dbPath
