#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------------------------------
# INFO:
# -----------------------------------------------------------------------------------------------------------------------

"""
Authors: Evan Hubinger, Ishaan Verma
License: Apache 2.0
Description: Defines arguments for the Coconut CLI.
"""

# -----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

from coconut.root import *  # NOQA

import argparse

from coconut._pyparsing import PYPARSING_INFO

from coconut.constants import (
    documentation_url,
    default_recursion_limit,
    main_sig,
    style_env_var,
    default_style,
    vi_mode_env_var,
    prompt_vi_mode,
    py_version_str,
    default_jobs,
)

# -----------------------------------------------------------------------------------------------------------------------
# VERSION:
# -----------------------------------------------------------------------------------------------------------------------

cli_version = "Version " + VERSION_STR + " running on Python " + py_version_str + " and " + PYPARSING_INFO

cli_version_str = main_sig + cli_version

# -----------------------------------------------------------------------------------------------------------------------
# MAIN:
# -----------------------------------------------------------------------------------------------------------------------

arguments = argparse.ArgumentParser(
    prog="coconut",
    description="docs: " + documentation_url,
)

# any changes made to these arguments must be reflected in DOCS.md
arguments.add_argument(
    "source",
    metavar="source",
    type=str,
    nargs="?",
    help="path to the Coconut file/folder to compile",
)

arguments.add_argument(
    "dest",
    metavar="dest",
    type=str,
    nargs="?",
    help="destination directory for compiled files (defaults to the source directory)",
)

arguments.add_argument(
    "--and",
    metavar=("source", "dest"),
    type=str,
    nargs="+",
    action="append",
    help="add an additional source/dest pair to compile (dest is optional)",
)

arguments.add_argument(
    "-v", "-V", "--version",
    action="version",
    version=cli_version_str,
    help="print Coconut and Python version information",
)

arguments.add_argument(
    "-t", "--target",
    metavar="version",
    type=str,
    help="specify target Python version (defaults to universal)",
)

arguments.add_argument(
    "-i", "--interact",
    action="store_true",
    help="force the interpreter to start (otherwise starts if no other command is given) (implies --run)",
)

arguments.add_argument(
    "-p", "--package",
    action="store_true",
    help="compile source as part of a package (defaults to only if source is a directory)",
)

arguments.add_argument(
    "-a", "--standalone", "--stand-alone",
    action="store_true",
    help="compile source as standalone files (defaults to only if source is a single file)",
)

arguments.add_argument(
    "-l", "--line-numbers", "--linenumbers",
    action="store_true",
    help="force enable line number comments (--line-numbers are enabled by default unless --minify is passed)",
)

arguments.add_argument(
    "--no-line-numbers", "--nolinenumbers",
    action="store_true",
    help="disable line number comments (opposite of --line-numbers)",
)

arguments.add_argument(
    "-k", "--keep-lines", "--keeplines",
    action="store_true",
    help="include source code in comments for ease of debugging",
)

arguments.add_argument(
    "-w", "--watch",
    action="store_true",
    help="watch a directory and recompile on changes",
)

arguments.add_argument(
    "-r", "--run",
    action="store_true",
    help="execute compiled Python",
)

arguments.add_argument(
    "-n", "--no-write", "--nowrite",
    action="store_true",
    help="disable writing compiled Python",
)

arguments.add_argument(
    "-d", "--display",
    action="store_true",
    help="print compiled Python",
)

arguments.add_argument(
    "-q", "--quiet",
    action="store_true",
    help="suppress all informational output (combine with --display to write runnable code to stdout)",
)

arguments.add_argument(
    "-s", "--strict",
    action="store_true",
    help="enforce code cleanliness standards",
)

arguments.add_argument(
    "--no-tco", "--notco",
    action="store_true",
    help="disable tail call optimization",
)

arguments.add_argument(
    "--no-wrap-types", "--nowraptypes",
    action="store_true",
    help="disable wrapping type annotations in strings and turn off 'from __future__ import annotations' behavior",
)

arguments.add_argument(
    "-c", "--code",
    metavar="code",
    type=str,
    help="run Coconut passed in as a string (can also be piped into stdin)",
)

arguments.add_argument(
    "--incremental",
    action="store_true",
    help="enable incremental compilation mode (caches previous parses to improve recompilation performance for slightly modified files)",
)

arguments.add_argument(
    "-j", "--jobs",
    metavar="processes",
    type=str,
    help="number of additional processes to use (defaults to " + ascii(default_jobs) + ") (0 is no additional processes; 'sys' uses machine default)",
)

arguments.add_argument(
    "-f", "--force",
    action="store_true",
    help="force re-compilation even when source code and compilation parameters haven't changed",
)

arguments.add_argument(
    "--minify",
    action="store_true",
    help="reduce size of compiled Python",
)

arguments.add_argument(
    "--jupyter", "--ipython",
    type=str,
    nargs=argparse.REMAINDER,
    help="run Jupyter/IPython with Coconut as the kernel (remaining args passed to Jupyter)",
)

arguments.add_argument(
    "--mypy",
    type=str,
    nargs=argparse.REMAINDER,
    help="run MyPy on compiled Python (remaining args passed to MyPy) (implies --package --line-numbers)",
)

arguments.add_argument(
    "--argv", "--args",
    type=str,
    nargs=argparse.REMAINDER,
    help="set sys.argv to source plus remaining args for use in the Coconut script being run",
)

arguments.add_argument(
    "--tutorial",
    action="store_true",
    help="open Coconut's tutorial in the default web browser",
)

arguments.add_argument(
    "--docs", "--documentation",
    action="store_true",
    help="open Coconut's documentation in the default web browser",
)

arguments.add_argument(
    "--style",
    metavar="name",
    type=str,
    help="set Pygments syntax highlighting style (or 'list' to list styles) (defaults to "
    + style_env_var + " environment variable if it exists, otherwise '" + default_style + "')",
)

arguments.add_argument(
    "--vi-mode", "--vimode",
    action="store_true",
    help="enable vi mode in the interpreter (currently set to " + ascii(prompt_vi_mode) + ") (can be modified by setting " + vi_mode_env_var + " environment variable)",
)

arguments.add_argument(
    "--recursion-limit", "--recursionlimit",
    metavar="limit",
    type=int,
    help="set maximum recursion depth in compiler (defaults to " + ascii(default_recursion_limit) + ") (when increasing --recursion-limit, you may also need to increase --stack-size; setting them to approximately equal values is recommended)",
)

arguments.add_argument(
    "--stack-size", "--stacksize",
    metavar="kbs",
    type=int,
    help="run the compiler in a separate thread with the given stack size in kilobytes",
)

arguments.add_argument(
    "--site-install", "--siteinstall",
    action="store_true",
    help="set up coconut.api to be imported on Python start",
)

arguments.add_argument(
    "--site-uninstall", "--siteuninstall",
    action="store_true",
    help="revert the effects of --site-install",
)

arguments.add_argument(
    "--verbose",
    action="store_true",
    help="print verbose debug output",
)

if DEVELOP:
    arguments.add_argument(
        "--trace",
        action="store_true",
        help="print verbose parsing data (only available in coconut-develop)",
    )

    arguments.add_argument(
        "--profile",
        action="store_true",
        help="collect and print timing info (only available in coconut-develop)",
    )
