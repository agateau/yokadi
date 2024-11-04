#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Setup script used to build and install Yokadi

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GPL v3 or newer
"""

from setuptools import setup
import sys
import os
from fnmatch import fnmatch
from os.path import isdir, dirname, join

sys.path.insert(0, dirname(__file__))
import yokadi  # noqa: E402


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
                  ["README.md", "CHANGELOG.md", "LICENSE"]])

# Doc
data_files.append(["share/yokadi/doc", createFileList("doc", "*.md")])

# Man
data_files.append(["share/man/man1", createFileList("man", "*.1")])

# Editor scripts
data_files.append(["share/yokadi/editors/vim/ftdetect", ["editors/vim/ftdetect/yokadimedit.vim"]])
data_files.append(["share/yokadi/editors/vim/syntax", ["editors/vim/syntax/yokadimedit.vim"]])

# Icon
for size in os.listdir("icon"):
    if not isdir(join("icon", size)):
        continue
    data_files.append(["share/icons/hicolor/%s/apps" % size, ["icon/%s/yokadi.png" % size]])

data_files.append(["share/applications", ["icon/yokadi.desktop"]])

# Scripts
scripts = ["bin/yokadi", "bin/yokadid"]

# Windows post install script
if "win" in " ".join(sys.argv[1:]):
    scripts.append("w32_postinst.py")

# Go for setup
setup(
    name="yokadi",
    version=yokadi.__version__,
    description="Command line oriented todo list system",
    author="The Yokadi Team",
    author_email="ml-yokadi@sequanux.org",
    url="http://yokadi.github.io/",
    packages=[
        "yokadi",
        "yokadi.core",
        "yokadi.tests",
        "yokadi.update",
        "yokadi.ycli",
        "yokadi.yical",
    ],
    # distutils does not support install_requires, but pip needs it to be
    # able to automatically install dependencies
    install_requires=[
        "sqlalchemy ~= 2.0.32",
        "python-dateutil ~= 2.8.2",
        "colorama ~= 0.4.6",
        "pyreadline3 ~= 3.4.1 ; platform_system == 'Windows'",
    ],
    scripts=scripts,
    data_files=data_files
)
