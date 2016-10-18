#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------------------------------------------------
# INFO:
#-----------------------------------------------------------------------------------------------------------------------

"""
Authors: Evan Hubinger, Fred Buchanan
License: Apache 2.0
Description: Handles interfacing with watchdog to make --watch work.
"""

#-----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
#-----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

from coconut.root import *  # NOQA

from coconut.exceptions import CoconutException

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer  # NOQA
except ImportError:
    raise CoconutException("--watch flag requires watchdog library",
                           extra="run 'pip install coconut[watch]' to fix")

#-----------------------------------------------------------------------------------------------------------------------
# CLASSES:
#-----------------------------------------------------------------------------------------------------------------------


class RecompilationWatcher(FileSystemEventHandler):

    def __init__(self, recompile):
        self.recompile = recompile

    def on_modified(self, event):
        self.recompile(event.src_path)
