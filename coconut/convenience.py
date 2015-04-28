#!/usr/bin/env python

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# INFO:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
Date Created: 2014
Description: Coconut Convenience Functions.
"""

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# IMPORTS:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

from __future__ import with_statement, print_function, absolute_import, unicode_literals, division

from .util import *
from .parser import processor, CoconutException
from .compiler import cli

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# COMPILING:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

COMPILER = cli()

def cmd(args, interact=False):
    """Processes Command-Line Arguments."""
    if isinstance(args, (str, bytes)):
        args = args.split()
    return COMPILER.cmd(COMPILER.commandline.parse_args(args), interact)

def version(which="num"):
    """Gets The Coconut Version."""
    if which == "num":
        return VERSION
    elif which == "name":
        return VERSION_NAME
    elif which == "full":
        return VERSION_STR
    elif which == "-v":
        return COMPILER.version
    else:
        raise CoconutException("invalid version type "+repr(which)+"; valid versions are 'num', 'name', 'full', and '-v'")

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PARSING:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_PARSER():
    """Gets COMPILER.processor."""
    if COMPILER.processor is None:
        COMPILER.setup()
    return COMPILER.processor

def parse(code, mode="file"):
    """Parses Coconut Code."""
    PARSER = get_PARSER()
    if mode == "single":
        return PARSER.parse_single(code)
    elif mode == "file":
        return PARSER.parse_file(code)
    elif mode == "module":
        return PARSER.parse_module(code)
    elif mode == "block":
        return PARSER.parse_block(code)
    elif mode == "eval":
        return PARSER.parse_eval(code)
    elif mode == "debug":
        return PARSER.parse_debug(code)
    else:
        raise CoconutException("invalid parse mode "+repr(mode)+"; valid modes are 'single', 'file', 'module', 'block', 'eval', and 'debug'")
