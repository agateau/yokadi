#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Post installation script for win32 system
Thanks to the coin coin projet for the inspiration for this postinstall script
@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GPL v3 or newer
"""

from os.path import abspath, join
from os import mkdir
import sys

# pylint: disable-msg=E0602

# Description string
desc = "Command line oriented todo list system"
# Shortcut name
lnk = "yokadi.lnk"

# Only do things at install stage, not uninstall
if sys.argv[1] == "-install":
    # Get python.exe path
    py_path = abspath(join(sys.prefix, "python.exe"))

    # Yokadi wrapper path
    yokadi_dir = abspath(join(sys.prefix, "scripts"))
    yokadi_path = join(yokadi_dir, "yokadi")

    # TODO: create a sexy yokadi .ico file to be put in share dir

    # Find desktop
    try:
        desktop_path = get_special_folder_path("CSIDL_COMMON_DESKTOPDIRECTORY")
    except OSError:
        desktop_path = get_special_folder_path("CSIDL_DESKTOPDIRECTORY")

    # Desktop shortcut creation
    create_shortcut(py_path,  # program to launch
                    desc,
                    join(desktop_path, lnk),  # shortcut file
                    yokadi_path,  # Argument (pythohn script)
                    yokadi_dir,  # Current work dir
                    ""  # Ico file (nothing for now)
                    )

    # Tel install process that we create a file so it can removed it during uninstallation
    file_created(join(desktop_path, lnk))

    # Start menu shortcut creation
    try:
        start_path = get_special_folder_path("CSIDL_COMMON_PROGRAMS")
    except OSError:
        start_path = get_special_folder_path("CSIDL_PROGRAMS")

    # Menu folder creation
    programs_path = join(start_path, "Yokadi")
    try:
        mkdir(programs_path)
    except OSError:
        pass
    directory_created(programs_path)

    create_shortcut(py_path,  # program to launch
                    desc,
                    join(programs_path, lnk),  # Shortcut file
                    yokadi_path,  # Argument (python script)
                    yokadi_dir,  # Cuurent work dir
                    ""  # Icone
                    )
    file_created(join(programs_path, lnk))

    # End of script
    sys.exit()
