#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Setup script used to build and install Yokadi

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

from distutils.core import setup
import sys
from os.path import dirname, join

# Additional files
data_files=[]
data_files.append(["share/yokadi",
                   ["version", "README.markdown", "ChangeLog", "ChangeLog-Synthesis", "LICENSE"]])

# Scripts
scripts=["src/bin/yokadi", "src/bin/yokadid", "src/bin/xyokadi"]

# Version
try:
    version=file(join(dirname(__file__), "version")).readline().rstrip().rstrip("\n")
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
      packages=["yokadi"],
      scripts=scripts,
      data_files=data_files
      )