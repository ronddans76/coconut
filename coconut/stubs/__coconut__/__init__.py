#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------------------------------
# INFO:
# -----------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
License: Apache 2.0
Description: For type checking purposes only. Should never be imported.
"""

# -----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

from coconut.root import *  # NOQA

# -----------------------------------------------------------------------------------------------------------------------
# ERROR:
# -----------------------------------------------------------------------------------------------------------------------

raise ImportError("Importing the top-level __coconut__ package should never be done at runtime; __coconut__ exists for type checking purposes only. You should be importing coconut.__coconut__ instead.")
