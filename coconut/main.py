#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------------------------------------------------
# INFO:
#-----------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
License: Apache 2.0
Description: Starts the Coconut command line utility.
"""

#-----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
#-----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

import sys
import os.path


def add_coconut_to_path():
    """Adds coconut to sys.path if it isn't there already."""
    try:
        import coconut  # NOQA
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


add_coconut_to_path()
from coconut.root import *  # NOQA

from coconut.command import Command

#-----------------------------------------------------------------------------------------------------------------------
# MAIN:
#-----------------------------------------------------------------------------------------------------------------------


def main():
    """Starts Coconut."""
    Command().start()


def main_run():
    """Starts Coconut with the --run and --quiet options."""
    sys.argv = sys.argv[:1] + ["-rq"] + sys.argv[1:]
    main()


if __name__ == "__main__":
    main()
