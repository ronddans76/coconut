#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------------------------------
# INFO:
# -----------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
License: Apache 2.0
Description: Sphinx configuration file for the Coconut Programming Language.
"""

# -----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

import sys
import os.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coconut.root import *  # NOQA

from coconut.constants import (
    version_str_tag,
    without_toc,
    with_toc,
)
from coconut.util import univ_open

import myst_parser  # NOQA
from sphinx_bootstrap_theme import get_html_theme_path

# -----------------------------------------------------------------------------------------------------------------------
# README:
# -----------------------------------------------------------------------------------------------------------------------

with univ_open("README.rst", "r") as readme_file:
    readme = readme_file.read()

with univ_open("index.rst", "w") as index_file:
    index_file.write(readme.replace(without_toc, with_toc))

# -----------------------------------------------------------------------------------------------------------------------
# DEFINITIONS:
# -----------------------------------------------------------------------------------------------------------------------

from coconut.constants import (  # NOQA
    project,
    copyright,
    author,
    highlight_language,
)

version = VERSION
release = version_str_tag

html_theme = "bootstrap"
html_theme_path = get_html_theme_path()
html_theme_options = {
    "navbar_fixed_top": "false",
}

master_doc = "index"
exclude_patterns = ["README.*"]

source_suffix = [".rst", ".md"]

default_role = "code"

extensions = ["myst_parser"]

myst_enable_extensions = [
    "smartquotes",
]

myst_heading_anchors = 4
