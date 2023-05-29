#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------------------------------
# INFO:
# -----------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
License: Apache 2.0
Description: Endpoints for Coconut's external integrations.
"""

# -----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

from coconut.root import *  # NOQA

from types import MethodType

from coconut.constants import (
    coconut_kernel_kwargs,
    enabled_xonsh_modes,
)
from coconut.util import memoize_with_exceptions

# -----------------------------------------------------------------------------------------------------------------------
# IPYTHON:
# -----------------------------------------------------------------------------------------------------------------------


def embed(kernel=False, depth=0, **kwargs):
    """If _kernel_=False (default), embeds a Coconut Jupyter console
    initialized from the current local namespace. If _kernel_=True,
    launches a Coconut Jupyter kernel initialized from the local
    namespace that can then be attached to. _kwargs_ are as in
    IPython.embed or IPython.embed_kernel based on _kernel_."""
    from coconut.icoconut.embed import embed, embed_kernel, extract_module_locals
    if kernel:
        mod, locs = extract_module_locals(1 + depth)
        embed_kernel(module=mod, local_ns=locs, **kwargs)
    else:
        embed(stack_depth=3 + depth, **kwargs)


def load_ipython_extension(ipython):
    """Loads Coconut as an IPython extension."""
    # add Coconut built-ins
    from coconut import __coconut__
    newvars = {}
    for var, val in vars(__coconut__).items():
        if not var.startswith("__"):
            newvars[var] = val
    ipython.push(newvars)

    # import here to avoid circular dependencies
    from coconut import api
    from coconut.exceptions import CoconutException
    from coconut.terminal import logger

    magic_state = api.get_state()
    api.setup(state=magic_state, **coconut_kernel_kwargs)

    # add magic function
    def magic(line, cell=None):
        """Provides %coconut and %%coconut magics."""
        try:
            if cell is None:
                code = line
            else:
                # first line in block is cmd, rest is code
                line = line.strip()
                if line:
                    api.cmd(line, default_target="sys", state=magic_state)
                code = cell
            compiled = api.parse(code, state=magic_state)
        except CoconutException:
            logger.print_exc()
        else:
            ipython.run_cell(compiled, shell_futures=False)
    ipython.register_magic_function(magic, "line_cell", "coconut")


# -----------------------------------------------------------------------------------------------------------------------
# XONSH:
# -----------------------------------------------------------------------------------------------------------------------

class CoconutXontribLoader(object):
    """Implements Coconut's _load_xontrib_."""
    loaded = False
    compiler = None
    runner = None
    timing_info = []

    @memoize_with_exceptions(128)
    def memoized_parse_xonsh(self, code):
        return self.compiler.parse_xonsh(code, keep_state=True)

    def compile_code(self, code):
        """Memoized self.compiler.parse_xonsh."""
        # hide imports to avoid circular dependencies
        from coconut.exceptions import CoconutException
        from coconut.terminal import format_error
        from coconut.util import get_clock_time
        from coconut.terminal import logger

        parse_start_time = get_clock_time()
        quiet, logger.quiet = logger.quiet, True
        success = False
        try:
            # .strip() outside the memoization
            compiled = self.memoized_parse_xonsh(code.strip())
        except CoconutException as err:
            err_str = format_error(err).splitlines()[0]
            compiled = code + "  #" + err_str
        else:
            success = True
        finally:
            logger.quiet = quiet
            self.timing_info.append(("parse", get_clock_time() - parse_start_time))

        return compiled, success

    def new_try_subproc_toks(self, ctxtransformer, node, *args, **kwargs):
        """Version of try_subproc_toks that handles the fact that Coconut
        code may have different columns than Python code."""
        mode = ctxtransformer.mode
        if self.loaded:
            ctxtransformer.mode = "eval"
        try:
            return ctxtransformer.__class__.try_subproc_toks(ctxtransformer, node, *args, **kwargs)
        finally:
            ctxtransformer.mode = mode

    def new_parse(self, parser, code, mode="exec", *args, **kwargs):
        """Coconut-aware version of xonsh's _parse."""
        if self.loaded and mode in enabled_xonsh_modes:
            code, _ = self.compile_code(code)
        return parser.__class__.parse(parser, code, mode=mode, *args, **kwargs)

    def new_ctxvisit(self, ctxtransformer, node, inp, ctx, mode="exec", *args, **kwargs):
        """Version of ctxvisit that ensures looking up original lines in inp
        using Coconut line numbers will work properly."""
        if self.loaded and mode in enabled_xonsh_modes:
            from xonsh.tools import get_logical_line

            # hide imports to avoid circular dependencies
            from coconut.terminal import logger
            from coconut.compiler.util import extract_line_num_from_comment

            compiled, success = self.compile_code(inp)

            if success:
                original_lines = tuple(inp.splitlines())
                used_lines = set()
                new_inp_lines = []
                last_ln = 1
                for compiled_line in compiled.splitlines():
                    ln = extract_line_num_from_comment(compiled_line, default=last_ln + 1)
                    try:
                        line, _, _ = get_logical_line(original_lines, ln - 1)
                    except IndexError:
                        logger.log_exc()
                        line = original_lines[-1]
                    if line in used_lines:
                        line = ""
                    else:
                        used_lines.add(line)
                    new_inp_lines.append(line)
                    last_ln = ln
                inp = "\n".join(new_inp_lines)

            inp += "\n"

        return ctxtransformer.__class__.ctxvisit(ctxtransformer, node, inp, ctx, mode, *args, **kwargs)

    def __call__(self, xsh, **kwargs):
        # hide imports to avoid circular dependencies
        from coconut.util import get_clock_time

        start_time = get_clock_time()

        if self.compiler is None:
            from coconut.compiler import Compiler
            self.compiler = Compiler(**coconut_kernel_kwargs)
            self.compiler.warm_up()

        if self.runner is None:
            from coconut.command.util import Runner
            self.runner = Runner(self.compiler)

        self.runner.update_vars(xsh.ctx)

        main_parser = xsh.execer.parser
        main_parser.parse = MethodType(self.new_parse, main_parser)

        ctxtransformer = xsh.execer.ctxtransformer
        ctxtransformer.try_subproc_toks = MethodType(self.new_try_subproc_toks, ctxtransformer)
        ctxtransformer.ctxvisit = MethodType(self.new_ctxvisit, ctxtransformer)

        ctx_parser = ctxtransformer.parser
        ctx_parser.parse = MethodType(self.new_parse, ctx_parser)

        self.timing_info.append(("load", get_clock_time() - start_time))
        self.loaded = True

        return self.runner.vars

    def unload(self, xsh):
        if not self.loaded:
            # hide imports to avoid circular dependencies
            from coconut.terminal import logger
            logger.warn("attempting to unload Coconut xontrib but it was never loaded")
        self.loaded = False


_load_xontrib_ = CoconutXontribLoader()

_unload_xontrib_ = _load_xontrib_.unload
