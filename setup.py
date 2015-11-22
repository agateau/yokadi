#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Setup script used to build and install Yokadi

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GPL v3 or newer
"""

from distutils.core import setup
import sys
import os
from fnmatch import fnmatch
from os.path import abspath, isdir, dirname, join

# yokadi root path
root = abspath(dirname(__file__))

def createFileList(sourceDir, *patterns):
    """
    List files from sourceDir which match one of the pattern in patterns
    Returns the path including sourceDir
    """
    for name in os.listdir(sourceDir):
        for pattern in patterns:
            if fnmatch(name, pattern):
                yield join(sourceDir, name)

# Additional files
data_files = []
data_files.append(["share/yokadi",
                  ["version", "README.md", "NEWS", "LICENSE"]])

# Doc
data_files.append(["share/yokadi/doc", createFileList("doc", "*.md")])

# Man
data_files.append(["share/man/man1", createFileList("man", "*.1")])

# Update scripts
data_files.append(["share/yokadi/update", createFileList("update", "*.py", "update*to*")])

# Icon
for size in os.listdir("icon"):
    if not isdir(join("icon", size)):
        continue
    data_files.append(["share/icons/hicolor/%s/apps" % size,
        ["icon/%s/yokadi.png" % size]])

data_files.append(["share/applications", ["icon/yokadi.desktop"]])

# Scripts
scripts = ["bin/yokadi", "bin/yokadid"]

# Version
try:
    version = open(join(root, "version"), encoding='utf-8').readline().rstrip().rstrip("\n")
except Exception as e:
    print("Warning, cannot read version file (%s)" % e)
    print("Defaulting to 'snapshot'")
    version = "snaphot"

# Windows post install script
if "win" in " ".join(sys.argv[1:]):
    scripts.append("w32_postinst.py")

# Go for setup
setup(name="yokadi",
      version=version,
      description="Command line oriented todo list system",
      author="The Yokadi Team",
      author_email="ml-yokadi@sequanux.org",
      url="http://yokadi.github.com/",
      packages=[
        "yokadi",
        "yokadi.core",
        "yokadi.tests",
        "yokadi.ycli",
        "yokadi.yical",
      ],
      install_requires=[
        "sqlalchemy",
        "dateutil",
      ],
      scripts=scripts,
      data_files=data_files
      )
