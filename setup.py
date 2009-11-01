#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Setup script used to build and install Yokadi

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GPL v3 or newer
"""

from distutils.core import setup
import sys
import os
from os.path import abspath, dirname, join

# yokadi root path
root=abspath(dirname(__file__))

# Additional files
data_files=[]
data_files.append(["share/yokadi",
                   ["version", "README.markdown", "NEWS", "LICENSE"]])

# Doc
data_files.append(["share/yokadi/doc",
                   ["doc/%s" % f for f in os.listdir(join(root, "doc"))]])

# Update scripts
data_files.append(["share/yokadi/update",
                   ["update/%s" % f for f in os.listdir(join(root, "update"))]])

# Scripts
scripts=["src/bin/yokadi", "src/bin/yokadid", "src/bin/xyokadi"]

# Version
try:
    version=file(join(root, "version")).readline().rstrip().rstrip("\n")
except Exception, e:
    print "Warning, cannot read version file (%s)" % e
    print "Defaulting to 'snapshot'"
    version="snaphot"

# Windows post install script
if "win" in " ".join(sys.argv[1:]):
    scripts.append("w32_postinst.py")

#Go for setup 
setup(name="yokadi",
      version=version,
      description="Command line oriented todo list system",
      author="The Yokadi Team",
      author_email="ml-yokadi@sequanux.org",
      url="http://yokadi.github.com/",
      package_dir={"yokadi" : "src/yokadi"},
      packages=["yokadi", "yokadi.tests"],
      scripts=scripts,
      data_files=data_files
      )
