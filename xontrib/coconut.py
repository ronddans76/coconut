#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------------------------------
# INFO:
# -----------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
License: Apache 2.0
Description: Coconut xontrib to enable Coconut code in xonsh.
"""

# -----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
# ----------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

from coconut.root import *  # NOQA

from coconut.integrations import _load_xontrib_, _unload_xontrib_  # NOQA

# -----------------------------------------------------------------------------------------------------------------------
# MAIN:
# -----------------------------------------------------------------------------------------------------------------------

try:
    __xonsh__
except NameError:
    pass
else:
    _load_xontrib_(__xonsh__)
