#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------------------------------------------------
# INFO:
#-----------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
License: Apache 2.0
Description: Utilities for use in the compiler.
"""

#-----------------------------------------------------------------------------------------------------------------------
# IMPORTS:
#-----------------------------------------------------------------------------------------------------------------------

from __future__ import print_function, absolute_import, unicode_literals, division

from coconut.root import *  # NOQA

import traceback
from functools import partial
from contextlib import contextmanager

from coconut.pyparsing import (
    replaceWith,
    ZeroOrMore,
    Optional,
    SkipTo,
    CharsNotIn,
    ParseElementEnhance,
    ParseException,
    ParseResults,
    Combine,
    _trim_arity,
    _ParseResultsWithOffset,
)

from coconut.terminal import logger, complain
from coconut.constants import (
    opens,
    closes,
    openindent,
    closeindent,
    default_whitespace_chars,
    get_target_info,
)
from coconut.exceptions import (
    CoconutException,
    CoconutInternalException,
    internal_assert,
)


#-----------------------------------------------------------------------------------------------------------------------
# COMPUTATION GRAPH:
#-----------------------------------------------------------------------------------------------------------------------


def evaluate_tokens(tokens):
    """Evaluate the given tokens in the computation graph."""
    if isinstance(tokens, ComputationNode):
        return tokens.evaluate()
    elif isinstance(tokens, ParseResults):
        toklist, name, asList, modal = tokens.__getnewargs__()
        new_toklist = [evaluate_tokens(toks) for toks in toklist]
        new_tokdict = {}
        for name, occurrences in tokens._ParseResults__tokdict.items():
            new_occurences = []
            for value, position in occurrences:
                new_value = evaluate_tokens(value)
                new_occurences.append(_ParseResultsWithOffset(new_value, position))
            new_tokdict[name] = occurrences
        new_tokens = ParseResults(new_toklist, name, asList, modal)
        new_tokens._ParseResults__accumNames.update(tokens._ParseResults__accumNames)
        new_tokens._ParseResults__tokdict.update(new_tokdict)
        return new_tokens
    elif isinstance(tokens, (list, tuple)):
        return [evaluate_tokens(inner_toks) for inner_toks in tokens]
    elif isinstance(tokens, str):
        return tokens
    else:
        raise CoconutInternalException("invalid computation graph tokens", tokens)


class ComputationNode(object):
    """A single node in the computation graph."""
    __slots__ = ("action", "loc", "tokens", "index_of_original", "result")
    list_of_originals = []
    no_result = object()

    def __new__(cls, action, original, loc, tokens, simple=False):
        """Create a ComputionNode to return from a parse action."""
        if simple and len(tokens) == 1:
            return tokens[0]  # could be a ComputationNode, so we can't have an __init__
        else:
            self = super(ComputationNode, cls).__new__(cls)
            self.result = cls.no_result
            self.action, self.loc, self.tokens = action, loc, tokens
            try:
                self.index_of_original = self.list_of_originals.index(original)
            except ValueError:
                self.index_of_original = len(self.list_of_originals)
                self.list_of_originals.append(original)
            return self

    @property
    def original(self):
        """Get the original from the originals memo."""
        return self.list_of_originals[self.index_of_original]

    @property
    def name(self):
        """Get the name of the action."""
        return self.action.__name__

    def evaluate(self):
        """Get the result of evaluating the computation graph at this node."""
        if self.result is self.no_result:
            self.compute_result()
        internal_assert(self.result is not self.no_result, "got no result computing action " + self.name + " of graph", self.tokens)
        return self.result

    def compute_result(self):
        """Evaluate the computation graph at this node and assign the result to self.result."""
        evaluated_toks = evaluate_tokens(self.tokens)
        if logger.tracing:  # repr(self.tokens) is very expensive, so we should only call it if we are actually tracing
            logger.log_trace(self.name, self.original, self.loc, evaluated_toks, repr(self.tokens))
        try:
            self.result = _trim_arity(self.action)(
                self.original,
                self.loc,
                evaluated_toks,
            )
        except CoconutException:
            raise
        except (Exception, AssertionError):
            traceback.print_exc()
            raise CoconutInternalException("error computing action " + self.name + " of tokens", evaluated_toks)

    def __repr__(self):
        """Get a representation of the entire computation graph below this node."""
        inner_repr = "\n".join("\t" + line for line in repr(self.tokens).splitlines())
        return self.name + "(\n" + inner_repr + "\n)"


class CombineNode(Combine):
    """Modified Combine to work with the computation graph."""
    __slots__ = ()

    def _action(self, original, loc, tokens):
        """Implement the parse action for Combine."""
        combined_tokens = super(CombineNode, self).postParse(original, loc, tokens)
        internal_assert(len(combined_tokens) == 1, "Combine produced multiple tokens", combined_tokens)
        return combined_tokens[0]

    def postParse(self, original, loc, tokens):
        """Create a ComputationNode for Combine."""
        return ComputationNode(self._action, original, loc, tokens, simple=True)


def add_action(item, action):
    """Set the parse action for the given item."""
    return item.copy().addParseAction(action)


def attach(item, action, simple=None):
    """Set the parse action for the given item to create a node in the computation graph."""
    if simple is None:
        simple = getattr(action, "simple", False)
    return add_action(item, partial(ComputationNode, action, simple=simple))


def unpack(tokens):
    """Evaluate and unpack the given computation graph."""
    logger.log_tag("unpack", tokens)
    result = evaluate_tokens(tokens)
    if isinstance(result, str):
        return result
    else:
        internal_assert(len(result) == 1, "multiple tokens leftover", result)
        return result[0]


def parse(grammar, text):
    """Parse text using grammar."""
    return unpack(grammar.parseWithTabs().parseString(text))


def all_matches(grammar, text):
    """Find all matches for grammar in text."""
    for tokens, start, stop in grammar.parseWithTabs().scanString(text):
        yield unpack(tokens), start, stop


def match_in(grammar, text):
    """Determine if there is a match for grammar in text."""
    for result in grammar.parseWithTabs().scanString(text):
        return True
    return False


#-----------------------------------------------------------------------------------------------------------------------
# UTILITIES:
#-----------------------------------------------------------------------------------------------------------------------


def get_target_info_len2(target, lowest=False):
    """By default, gets the highest version supported by the target before the next target.
    If lowest is passed, instead gets the lowest version supported by the target."""
    target_info = get_target_info(target)
    if not target_info:
        return (2, 6) if lowest else (2, 7)
    elif len(target_info) == 1:
        if target_info == (2,):
            return (2, 6) if lowest else (2, 7)
        elif target_info == (3,):
            return (3, 2) if lowest else (3, 4)
        else:
            raise CoconutInternalException("invalid target info", target_info)
    elif len(target_info) == 2:
        return target_info
    else:
        return target_info[:2]


def join_args(*arglists):
    """Join split argument tokens."""
    return ", ".join(arg for args in arglists for arg in args if arg)


def paren_join(items, sep):
    """Join items by sep with parens around individual items but not the whole."""
    return items[0] if len(items) == 1 else "(" + (") " + sep + " (").join(items) + ")"


skip_whitespace = SkipTo(CharsNotIn(default_whitespace_chars)).suppress()


def longest(*args):
    """Match the longest of the given grammar elements."""
    internal_assert(len(args) >= 2, "longest expected at least two args")
    matcher = args[0] + skip_whitespace
    for elem in args[1:]:
        matcher ^= elem + skip_whitespace
    return matcher


def addskip(skips, skip):
    """Add a line skip to the skips."""
    if skip < 1:
        complain(CoconutInternalException("invalid skip of line " + str(skip)))
    elif skip in skips:
        complain(CoconutInternalException("duplicate skip of line " + str(skip)))
    else:
        skips.add(skip)
    return skips


def count_end(teststr, testchar):
    """Count instances of testchar at end of teststr."""
    count = 0
    x = len(teststr) - 1
    while x >= 0 and teststr[x] == testchar:
        count += 1
        x -= 1
    return count


def paren_change(inputstring, opens=opens, closes=closes):
    """Determine the parenthetical change of level (num closes - num opens)."""
    count = 0
    for c in inputstring:
        if c in opens:  # open parens/brackets/braces
            count -= 1
        elif c in closes:  # close parens/brackets/braces
            count += 1
    return count


def ind_change(inputstring):
    """Determine the change in indentation level (num opens - num closes)."""
    return inputstring.count(openindent) - inputstring.count(closeindent)


def fixto(item, output):
    """Force an item to result in a specific output."""
    return add_action(item, replaceWith(output))


def addspace(item):
    """Condense and adds space to the tokenized output."""
    return attach(item, " ".join, simple=True)


def condense(item):
    """Condense the tokenized output."""
    return attach(item, "".join, simple=True)


def maybeparens(lparen, item, rparen):
    """Wrap an item in optional parentheses."""
    return item | lparen.suppress() + item + rparen.suppress()


def tokenlist(item, sep, suppress=True):
    """Create a list of tokens matching the item."""
    if suppress:
        sep = sep.suppress()
    return item + ZeroOrMore(sep + item) + Optional(sep)


def itemlist(item, sep, suppress_trailing=True):
    """Create a list of items seperated by seps."""
    return condense(item + ZeroOrMore(addspace(sep + item)) + Optional(sep.suppress() if suppress_trailing else sep))


def exprlist(expr, op):
    """Create a list of exprs seperated by ops."""
    return addspace(expr + ZeroOrMore(op + expr))


def rem_comment(line):
    """Remove a comment from a line."""
    return line.split("#", 1)[0].rstrip()


def should_indent(code):
    """Determines whether the next line should be indented."""
    last = rem_comment(code.splitlines()[-1])
    return last.endswith(":") or last.endswith("\\") or paren_change(last) < 0


def split_comment(line):
    """Split line into base and comment."""
    base = rem_comment(line)
    return base, line[len(base):]


def split_leading_indent(line, max_indents=None):
    """Split line into leading indent and main."""
    indent = ""
    while line.lstrip() != line or (
        (max_indents is None or max_indents > 0)
        and line.startswith((openindent, closeindent))
    ):
        if max_indents is not None and line.startswith((openindent, closeindent)):
            max_indents -= 1
        indent += line[0]
        line = line[1:]
    return indent, line


def split_trailing_indent(line, max_indents=None):
    """Split line into leading indent and main."""
    indent = ""
    while line.rstrip() != line or (
        (max_indents is None or max_indents > 0)
        and (line.endswith(openindent) or line.endswith(closeindent))
    ):
        if max_indents is not None and (line.endswith(openindent) or line.endswith(closeindent)):
            max_indents -= 1
        indent = line[-1] + indent
        line = line[:-1]
    return line, indent


def split_leading_trailing_indent(line, max_indents=None):
    """Split leading and trailing indent."""
    leading_indent, line = split_leading_indent(line, max_indents)
    line, trailing_indent = split_trailing_indent(line, max_indents)
    return leading_indent, line, trailing_indent


ignore_transform = object()


def transform(grammar, text):
    """Transform text by replacing matches to grammar."""
    results = []
    intervals = []
    for result, start, stop in all_matches(grammar, text):
        if result is not ignore_transform:
            results.append(result)
            intervals.append((start, stop))

    if not results:
        return None

    split_indices = [0]
    split_indices.extend(start for start, _ in intervals)
    split_indices.extend(stop for _, stop in intervals)
    split_indices.sort()
    split_indices.append(None)

    out = []
    for i in range(len(split_indices) - 1):
        if i % 2 == 0:
            start, stop = split_indices[i], split_indices[i + 1]
            out.append(text[start:stop])
        else:
            out.append(results[i // 2])
    if i // 2 < len(results) - 1:
        raise CoconutInternalException("unused transform results", results[i // 2 + 1:])
    if stop is not None:
        raise CoconutInternalException("failed to properly split text to be transformed")
    return "".join(out)


class Wrap(ParseElementEnhance):
    """PyParsing token that wraps the given item in the given context manager."""

    def __init__(self, item, wrapper):
        super(Wrap, self).__init__(item)
        self.errmsg = item.errmsg + " (Wrapped)"
        self.wrapper = wrapper

    def parseImpl(self, instring, loc, *args, **kwargs):
        """Wrapper around ParseElementEnhance.parseImpl."""
        with self.wrapper(self, instring, loc):
            return super(Wrap, self).parseImpl(instring, loc, *args, **kwargs)


def disable_inside(item, *elems, **kwargs):
    """Prevent elems from matching inside of item.

    Returns (item with elem disabled, *new versions of elems).
    """
    _invert = kwargs.get("_invert", False)
    internal_assert(set(kwargs.keys()) <= set(("_invert",)), "excess keyword arguments passed to disable_inside")

    level = [0]  # number of wrapped items deep we are; in a list to allow modification

    @contextmanager
    def manage_item(self, instring, loc):
        level[0] += 1
        try:
            yield
        finally:
            level[0] -= 1

    yield Wrap(item, manage_item)

    @contextmanager
    def manage_elem(self, instring, loc):
        if level[0] == 0 if not _invert else level[0] > 0:
            yield
        else:
            raise ParseException(instring, loc, self.errmsg, self)

    for elem in elems:
        yield Wrap(elem, manage_elem)


def disable_outside(item, *elems):
    """Prevent elems from matching outside of item.

    Returns (item with elem disabled, *new versions of elems).
    """
    for wrapped in disable_inside(item, *elems, **{"_invert": True}):
        yield wrapped
