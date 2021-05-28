#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------------------------------
# INFO:
# -----------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
License: Apache 2.0
Description: Header utilities for the compiler.
"""

# -----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

from coconut.root import *  # NOQA

import os.path
from functools import partial

from coconut.root import _indent
from coconut.constants import (
    univ_open,
    hash_prefix,
    tabideal,
    default_encoding,
    template_ext,
    justify_len,
)
from coconut.terminal import internal_assert
from coconut.compiler.util import (
    get_target_info,
    split_comment,
    get_vers_for_target,
)

# -----------------------------------------------------------------------------------------------------------------------
# UTILITIES:
# -----------------------------------------------------------------------------------------------------------------------


def gethash(compiled):
    """Retrieve a hash from a header."""
    lines = compiled.splitlines()
    if len(lines) < 3 or not lines[2].startswith(hash_prefix):
        return None
    else:
        return lines[2][len(hash_prefix):]


def minify(compiled):
    """Perform basic minification of the header.

    Fails on non-tabideal indentation, strings with #s, or multi-line strings.
    (So don't do those things in the header.)
    """
    compiled = compiled.strip()
    if compiled:
        out = []
        for line in compiled.splitlines():
            new_line, comment = split_comment(line)
            new_line = new_line.rstrip()
            if new_line:
                ind = 0
                while new_line.startswith(" "):
                    new_line = new_line[1:]
                    ind += 1
                internal_assert(ind % tabideal == 0, "invalid indentation in", line)
                new_line = " " * (ind // tabideal) + new_line
            comment = comment.strip()
            if comment:
                new_line += "#" + comment
            if new_line:
                out.append(new_line)
        compiled = "\n".join(out) + "\n"
    return compiled


template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def get_template(template):
    """Read the given template file."""
    with univ_open(os.path.join(template_dir, template) + template_ext, "r") as template_file:
        return template_file.read()


def one_num_ver(target):
    """Return the first number of the target version, if it has one."""
    return target[:1]  # "2", "3", or ""


def section(name):
    """Generate a section break."""
    line = "# " + name + ": "
    return line + "-" * (justify_len - len(line)) + "\n\n"


def base_pycondition(target, ver, if_lt=None, if_ge=None, indent=None, newline=False, fallback=""):
    """Produce code that depends on the Python version for the given target."""
    internal_assert(isinstance(ver, tuple), "invalid pycondition version")
    internal_assert(if_lt or if_ge, "either if_lt or if_ge must be specified")

    if if_lt:
        if_lt = if_lt.strip()
    if if_ge:
        if_ge = if_ge.strip()

    target_supported_vers = get_vers_for_target(target)

    if all(tar_ver < ver for tar_ver in target_supported_vers):
        if not if_lt:
            return fallback
        out = if_lt

    elif all(tar_ver >= ver for tar_ver in target_supported_vers):
        if not if_ge:
            return fallback
        out = if_ge

    else:
        if if_lt and if_ge:
            out = """if _coconut_sys.version_info < {ver}:
{lt_block}
else:
{ge_block}""".format(
                ver=repr(ver),
                lt_block=_indent(if_lt, by=1),
                ge_block=_indent(if_ge, by=1),
            )
        elif if_lt:
            out = """if _coconut_sys.version_info < {ver}:
{lt_block}""".format(
                ver=repr(ver),
                lt_block=_indent(if_lt, by=1),
            )
        else:
            out = """if _coconut_sys.version_info >= {ver}:
{ge_block}""".format(
                ver=repr(ver),
                ge_block=_indent(if_ge, by=1),
            )

    if indent is not None:
        out = _indent(out, by=indent)
    if newline:
        out += "\n"
    return out


# -----------------------------------------------------------------------------------------------------------------------
# FORMAT DICTIONARY:
# -----------------------------------------------------------------------------------------------------------------------


class Comment(object):
    """When passed to str.format, allows {COMMENT.<>} to serve as a comment."""

    def __getattr__(self, attr):
        """Return an empty string for all comment attributes."""
        return ""


COMMENT = Comment()


def process_header_args(which, target, use_hash, no_tco, strict):
    """Create the dictionary passed to str.format in the header."""
    target_startswith = one_num_ver(target)
    target_info = get_target_info(target)
    pycondition = partial(base_pycondition, target)

    format_dict = dict(
        COMMENT=COMMENT,
        empty_dict="{}",
        lbrace="{",
        rbrace="}",
        target_startswith=target_startswith,
        default_encoding=default_encoding,
        hash_line=hash_prefix + use_hash + "\n" if use_hash is not None else "",
        typing_line="# type: ignore\n" if which == "__coconut__" else "",
        VERSION_STR=VERSION_STR,
        module_docstring='"""Built-in Coconut utilities."""\n\n' if which == "__coconut__" else "",
        object="" if target_startswith == "3" else "(object)",
        import_asyncio=pycondition(
            (3, 4),
            if_lt=r'''
try:
    import trollius as asyncio
except ImportError:
    class you_need_to_install_trollius: pass
    asyncio = you_need_to_install_trollius()
            ''',
            if_ge=r'''
import asyncio
            ''',
            indent=1,
        ),
        import_pickle=pycondition(
            (3,),
            if_lt=r'''
import cPickle as pickle
            ''',
            if_ge=r'''
import pickle
            ''',
            indent=1,
        ),
        import_OrderedDict=_indent(
            r'''OrderedDict = collections.OrderedDict if _coconut_sys.version_info >= (2, 7) else dict'''
            if not target
            else "OrderedDict = collections.OrderedDict" if target_info >= (2, 7)
            else "OrderedDict = dict",
            by=1,
        ),
        import_collections_abc=pycondition(
            (3, 3),
            if_lt=r'''
abc = collections
            ''',
            if_ge=r'''
import collections.abc as abc
            ''',
            indent=1,
        ),
        maybe_bind_lru_cache=pycondition(
            (3, 2),
            if_lt=r'''
try:
    from backports.functools_lru_cache import lru_cache
    functools.lru_cache = lru_cache
except ImportError: pass
            ''',
            if_ge=None,
            indent=1,
            newline=True,
        ),
        set_zip_longest=_indent(
            r'''zip_longest = itertools.zip_longest if _coconut_sys.version_info >= (3,) else itertools.izip_longest'''
            if not target
            else "zip_longest = itertools.zip_longest" if target_info >= (3,)
            else "zip_longest = itertools.izip_longest",
            by=1,
        ),
        comma_bytearray=", bytearray" if target_startswith != "3" else "",
        static_repr="staticmethod(repr)" if target_startswith != "3" else "repr",
        return_ThreadPoolExecutor=(
            # cpu_count() * 5 is the default Python 3.5 thread count
            r'''from multiprocessing import cpu_count
        return ThreadPoolExecutor(cpu_count() * 5 if max_workers is None else max_workers)''' if target_info < (3, 5)
            else '''return ThreadPoolExecutor(max_workers)'''
        ),
        zip_iter=_indent(
            r'''for items in _coconut.iter(_coconut.zip(*self.iters, strict=self.strict) if _coconut_sys.version_info >= (3, 10) else _coconut.zip_longest(*self.iters, fillvalue=_coconut_sentinel) if self.strict else _coconut.zip(*self.iters)):
    if self.strict and _coconut_sys.version_info < (3, 10) and _coconut.any(x is _coconut_sentinel for x in items):
        raise _coconut.ValueError("zip(..., strict=True) arguments have mismatched lengths")
    yield items'''
            if not target else
            r'''for items in _coconut.iter(_coconut.zip(*self.iters, strict=self.strict)):
    yield items'''
            if target_info >= (3, 10) else
            r'''for items in _coconut.iter(_coconut.zip_longest(*self.iters, fillvalue=_coconut_sentinel) if self.strict else _coconut.zip(*self.iters)):
    if self.strict and _coconut.any(x is _coconut_sentinel for x in items):
        raise _coconut.ValueError("zip(..., strict=True) arguments have mismatched lengths")
    yield items''',
            by=2,
        ),
        # disabled mocks must have different docstrings so the
        #  interpreter can tell them apart from the real thing
        def_prepattern=(
            r'''def prepattern(base_func, **kwargs):
    """DEPRECATED: use addpattern instead."""
    def pattern_prepender(func):
        return addpattern(func, **kwargs)(base_func)
    return pattern_prepender'''
            if not strict else
            r'''def prepattern(*args, **kwargs):
    """Deprecated feature 'prepattern' disabled by --strict compilation; use 'addpattern' instead."""
    raise _coconut.NameError("deprecated feature 'prepattern' disabled by --strict compilation; use 'addpattern' instead")'''
        ),
        def_datamaker=(
            r'''def datamaker(data_type):
    """DEPRECATED: use makedata instead."""
    return _coconut.functools.partial(makedata, data_type)'''
            if not strict else
            r'''def datamaker(*args, **kwargs):
    """Deprecated feature 'datamaker' disabled by --strict compilation; use 'makedata' instead."""
    raise _coconut.NameError("deprecated feature 'datamaker' disabled by --strict compilation; use 'makedata' instead")'''
        ),
        return_methodtype=pycondition(
            (3,),
            if_lt=r'''
return _coconut.types.MethodType(self.func, obj, objtype)
            ''',
            if_ge=r'''
return _coconut.types.MethodType(self.func, obj)
            ''',
            indent=2,
        ),
        def_call_set_names=(
            r'''def _coconut_call_set_names(cls):
    for k, v in _coconut.vars(cls).items():
        set_name = _coconut.getattr(v, "__set_name__", None)
        if set_name is not None:
            set_name(cls, k)'''
            if target_startswith == "2" else
            r'''def _coconut_call_set_names(cls): pass'''
            if target_info >= (3, 6) else
            r'''def _coconut_call_set_names(cls):
    if _coconut_sys.version_info < (3, 6):
        for k, v in _coconut.vars(cls).items():
            set_name = _coconut.getattr(v, "__set_name__", None)
            if set_name is not None:
                set_name(cls, k)'''
        ),
        tco_comma="_coconut_tail_call, _coconut_tco, " if not no_tco else "",
        call_set_names_comma="_coconut_call_set_names, " if target_info < (3, 6) else "",
    )

    # when anything is added to this list it must also be added to the stub file
    format_dict["underscore_imports"] = "{tco_comma}{call_set_names_comma}_coconut, _coconut_MatchError, _coconut_igetitem, _coconut_base_compose, _coconut_forward_compose, _coconut_back_compose, _coconut_forward_star_compose, _coconut_back_star_compose, _coconut_forward_dubstar_compose, _coconut_back_dubstar_compose, _coconut_pipe, _coconut_star_pipe, _coconut_dubstar_pipe, _coconut_back_pipe, _coconut_back_star_pipe, _coconut_back_dubstar_pipe, _coconut_none_pipe, _coconut_none_star_pipe, _coconut_none_dubstar_pipe, _coconut_bool_and, _coconut_bool_or, _coconut_none_coalesce, _coconut_minus, _coconut_map, _coconut_partial, _coconut_get_function_match_error, _coconut_base_pattern_func, _coconut_addpattern, _coconut_sentinel, _coconut_assert, _coconut_mark_as_match, _coconut_reiterable".format(**format_dict)

    format_dict["import_typing_NamedTuple"] = pycondition(
        (3, 6),
        if_lt=r'''
class typing{object}:
    @staticmethod
    def NamedTuple(name, fields):
        return _coconut.collections.namedtuple(name, [x for x, t in fields])
        '''.format(**format_dict),
        if_ge=r'''
import typing
        ''',
        indent=1,
    )

    return format_dict


# -----------------------------------------------------------------------------------------------------------------------
# HEADER GENERATION:
# -----------------------------------------------------------------------------------------------------------------------


def getheader(which, target="", use_hash=None, no_tco=False, strict=False):
    """Generate the specified header."""
    internal_assert(
        which.startswith("package") or which in (
            "none", "initial", "__coconut__", "sys", "code", "file",
        ),
        "invalid header type",
        which,
    )

    if which == "none":
        return ""

    target_startswith = one_num_ver(target)
    target_info = get_target_info(target)
    pycondition = partial(base_pycondition, target)

    # initial, __coconut__, package:n, sys, code, file

    format_dict = process_header_args(which, target, use_hash, no_tco, strict)

    if which == "initial" or which == "__coconut__":
        header = '''#!/usr/bin/env python{target_startswith}
# -*- coding: {default_encoding} -*-
{hash_line}{typing_line}
# Compiled with Coconut version {VERSION_STR}

{module_docstring}'''.format(**format_dict)
    elif use_hash is not None:
        raise CoconutInternalException("can only add a hash to an initial or __coconut__ header, not", which)
    else:
        header = ""

    if which == "initial":
        return header

    # __coconut__, package:n, sys, code, file

    header += section("Coconut Header")

    if target_startswith != "3":
        header += "from __future__ import print_function, absolute_import, unicode_literals, division\n"
    elif target_info >= (3, 7):
        header += "from __future__ import generator_stop, annotations\n"
    elif target_info >= (3, 5):
        header += "from __future__ import generator_stop\n"

    if which.startswith("package"):
        levels_up = int(which[len("package:"):])
        coconut_file_path = "_coconut_os_path.dirname(_coconut_os_path.abspath(__file__))"
        for _ in range(levels_up):
            coconut_file_path = "_coconut_os_path.dirname(" + coconut_file_path + ")"
        return header + '''import sys as _coconut_sys, os.path as _coconut_os_path
_coconut_file_path = {coconut_file_path}
_coconut_module_name = _coconut_os_path.splitext(_coconut_os_path.basename(_coconut_file_path))[0]
if not _coconut_module_name or not _coconut_module_name[0].isalpha() or not all (c.isalpha() or c.isdigit() for c in _coconut_module_name):
    raise ImportError("invalid Coconut package name " + repr(_coconut_module_name) + " (pass --standalone to compile as individual files rather than a package)")
_coconut_cached_module = _coconut_sys.modules.get(str(_coconut_module_name + ".__coconut__"))
if _coconut_cached_module is not None and _coconut_os_path.dirname(_coconut_cached_module.__file__) != _coconut_file_path:
    del _coconut_sys.modules[str(_coconut_module_name + ".__coconut__")]
try:
    from typing import TYPE_CHECKING as _coconut_TYPE_CHECKING
except ImportError:
    _coconut_TYPE_CHECKING = False
if _coconut_TYPE_CHECKING:
    from __coconut__ import *
    from __coconut__ import {underscore_imports}
else:
    _coconut_sys.path.insert(0, _coconut_os_path.dirname(_coconut_file_path))
    exec("from " + _coconut_module_name + ".__coconut__ import *")
    exec("from " + _coconut_module_name + ".__coconut__ import {underscore_imports}")
{sys_path_pop}
'''.format(
            coconut_file_path=coconut_file_path,
            sys_path_pop=pycondition(
                # we can't pop on Python 2 if we want __coconut__ objects to be pickleable
                (3,),
                if_lt=None,
                if_ge=r'''
_coconut_sys.path.pop(0)
                ''',
                indent=1,
                newline=True,
            ),
            **format_dict
        ) + section("Compiled Coconut")

    if which == "sys":
        return header + '''import sys as _coconut_sys
from coconut.__coconut__ import *
from coconut.__coconut__ import {underscore_imports}
'''.format(**format_dict)

    # __coconut__, code, file

    header += "import sys as _coconut_sys\n"

    if target_info >= (3, 7):
        header += PY37_HEADER
    elif target_startswith == "3":
        header += PY3_HEADER
    elif target_info >= (2, 7):
        header += PY27_HEADER
    elif target_startswith == "2":
        header += PY2_HEADER
    else:
        header += PYCHECK_HEADER

    header += get_template("header").format(**format_dict)

    if which == "file":
        header += "\n" + section("Compiled Coconut")

    return header
