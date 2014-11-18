#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Setup script used to build and install Yokadi

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GPL v3 or newer
"""

from distutils.core import setup
import sys
import os
from os.path import abspath, isdir, dirname, join

# yokadi root path
root = abspath(dirname(__file__))

# Additional files
data_files = []
data_files.append(["share/yokadi",
                   ["version", "README.markdown", "NEWS", "LICENSE"]])

# Doc
data_files.append(["share/yokadi/doc",
                   ["doc/%s" % f for f in os.listdir(join(root, "doc"))]])

# Man
data_files.append(["share/man/man1",
                   ["man/%s" % f for f in os.listdir(join(root, "man"))]])

# Update scripts
data_files.append(["share/yokadi/update",
                   ["update/%s" % f for f in os.listdir(join(root, "update"))]])

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

requirements = ['sqlalchemy', 'dateutils']
if sys.version_info < (2, 7):
    requirements.append('argparse')

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
      install_requires=requirements,
      scripts=scripts,
      data_files=data_files
      )
