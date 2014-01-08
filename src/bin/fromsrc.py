# -*- coding: utf-8 -*-

"""Add parent dir to sys.path so that one can use Yokadi from an uninstalled
 source tree.

@author: Aurélien Gâteau (mail@agateau.com)
@license:GPL v3 or later
"""

import os
import sys

parentPath = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, parentPath)
