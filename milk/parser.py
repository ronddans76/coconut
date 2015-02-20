#!/usr/bin/env python

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# INFO:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
Date Created: 2014
Description: The CoconutScript Parser.
"""

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# IMPORTS:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

from __future__ import with_statement, print_function, absolute_import, unicode_literals, division

from .util import *
from pyparsing import *

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# UTILITIES:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CoconutException(ParseFatalException):
    """Base Coconut Exception."""
    def __init__(self, value):
        """Creates The Coconut Exception."""
        self.value = value
    def __repr__(self):
        """Displays The Coconut Exception."""
        return self.value
    def __str__(self):
        """Wraps repr."""
        return repr(self)

def attach(item, action):
    """Attaches A Parse Action To An Item."""
    return item.copy().addParseAction(action)

def fixto(item, output):
    """Forces An Item To Result In A Specific Output."""
    return attach(item, replaceWith(output))

def addspace(item):
    """Condenses And Adds Space To The Tokenized Output."""
    def callback(tokens):
        """Callback Function Constructed By addspace."""
        return " ".join(tokens)
    return attach(item, callback)

def condense(item):
    """Condenses The Tokenized Output."""
    def callback(tokens):
        """Callback Function Constructed By condense."""
        return "".join(tokens)
    return attach(item, callback)

def parenwrap(lparen, item, rparen):
    """Wraps An Item In Optional Parentheses."""
    return condense(lparen.suppress() + item + rparen.suppress() | item)

class tracer(object):
    """Debug Tracer."""
    last = None

    def __init__(self, on=True, verbose=False):
        """Creates The Tracer."""
        self.on = on
        self.verbose = verbose

    def trace(self, original, location, tokens, message=None):
        """Tracer Parse Action."""
        if self.on:
            if len(tokens) == 1:
                token = repr(tokens[0])
            else:
                token = str(tokens)
            if self.verbose or token != self.last:
                self.last = token
                out = ""
                if message is not None:
                    out += "["+message+"] "
                if len(tokens) == 1:
                    out += repr(tokens[0])
                else:
                    out += str(tokens)
                print(out)
        return tokens

    def bind(self, item, message=None):
        """Traces A Parse Element."""
        if message is None:
            callback = self.trace
        else:
            def callback(original, location, tokens):
                """Callback Function Constructed By tracer."""
                return self.trace(original, location, tokens, message)
        return attach(item, callback)

TRACER = tracer(False)
trace = TRACER.bind

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PROCESSORS:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def anyint_proc(tokens):
    """Replaces Underscored Integers."""
    if len(tokens) == 1:
        item, base = tokens[0].split("_")
        return 'int("'+item+'", '+base+")"
    else:
        raise CoconutException("Invalid anyint token")

def list_proc(tokens):
    """Removes The Last Character From A List."""
    out = []
    for x in xrange(0, len(tokens)):
        if x%2 == 0:
            out.append(tokens[x])
        else:
            out[-1] += tokens[x]
    return " ".join(out)

def itemlist(item, sep):
    """Creates A List Containing An Item."""
    return attach(item + ZeroOrMore(sep + item) + Optional(sep).suppress(), list_proc)

def item_proc(tokens):
    """Processes Items."""
    out = tokens.pop(0)
    for trailer in tokens:
        if isinstance(trailer, str):
            out += trailer
        elif len(trailer) == 2:
            if trailer[0] == "$":
                out = "__coconut__.curry("+out+", "+trailer[1]+")"
            elif trailer[0] == "..":
                out = "__coconut__.compose("+out+", "+trailer[1]+")"
            else:
                raise CoconutException("Invalid special trailer: "+repr(trailer[0]))
        else:
            raise CoconutException("Invalid trailer tokens: "+repr(trailer))
    return out

def infix_proc(tokens):
    """Processes Infix Calls."""
    if len(tokens) == 1:
        return tokens[0]
    else:
        return "__coconut__.infix("+infix_proc(tokens[:-2])+", "+tokens[-2]+", "+tokens[-1]+")"

def pipe_proc(tokens):
    """Processes Pipe Calls."""
    if len(tokens) == 1:
        return tokens[0]
    else:
        return "__coconut__.pipe("+", ".join(tokens)+")"


def lambda_proc(tokens):
    """Processes Lambda Calls."""
    if len(tokens) == 2:
        return "lambda "+tokens[0]+": "+tokens[1]
    else:
        raise CoconutException("Invalid lambda tokens: "+repr(tokens))

def assign_proc(tokens):
    """Processes Assignments."""
    if len(tokens) == 3:
        if tokens[1] == "=>":
            return tokens[0]+" = __coconut__.pipe("+tokens[0]+", ("+tokens[2]+"))"
        elif tokens[1] == "..=":
            return tokens[0]+" = __coconut__.compose("+tokens[0]+", ("+tokens[2]+"))"
        else:
            return tokens
    else:
        raise CoconutException("Invalid assignment tokens: "+repr(tokens))

def func_proc(tokens):
    """Processes Mathematical Function Definitons."""
    if len(tokens) == 2:
        return "def "+tokens[0]+": return "+tokens[1]
    else:
        raise CoconutException("Invalid mathematical function definition tokens: "+repr(tokens))

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PARSER:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
HEADER = readfile(openfile(os.path.join(_directory, "__coconut__.py"), "r"))

class processor(object):
    """The CoconutScript Pre-Processor."""
    openstr = "\u204b"
    closestr = "\xb6"
    linebreak = "\n"
    white = " \t\f"
    downs = "([{"
    ups = ")]}"
    holds = "'\"`"
    raw = "`"
    startcomment = "#"
    endline = "\n\r"
    escape = "\\"
    tablen = 4
    verbosity = 10

    def __init__(self):
        """Creates A New Pre-Processor."""
        self.init()
        self.clean()

    def clean(self):
        """Resets References."""
        self.refs = []

    def pre(self, inputstring, strip=False):
        """Performs Pre-Processing."""
        inputstring = str(inputstring)
        if strip:
            inputstring = inputstring.strip()
        return self.indproc(self.strproc(inputstring))

    def wrapstr(self, text, raw, multiline):
        """Wraps A String."""
        self.refs.append((text, raw, multiline))
        return '"'+str(len(self.refs)-1)+'"'

    def wrapcomment(self, text):
        """Wraps A Comment."""
        self.refs.append(text)
        return "#"+str(len(self.refs)-1)

    def getpart(self, iterstring, point):
        """Gets A Part Of A String For An Error Message."""
        out = ""
        i = point-self.verbosity
        while i < point+self.verbosity:
            if i and i < len(iterstring):
                out += iterstring[i]
            i += 1
        return "..."+repr(out)+"..."

    def strproc(self, inputstring):
        """Processes Strings."""
        out = []
        found = None
        hold = None
        x = 0
        while x <= len(inputstring):
            if x == len(inputstring):
                c = self.linebreak
            else:
                c = inputstring[x]
            if hold is not None:
                if len(hold) == 1:
                    if c in self.endline:
                        out.append(self.wrapcomment(hold[0])+c)
                        hold = None
                    else:
                        hold[0] += c
                elif hold[2] is not None:
                    if c == self.escape:
                        hold[0] += hold[2]+c
                        hold[2] = None
                    elif c == hold[1][0]:
                        hold[2] += c
                    elif len(hold[2]) > len(hold[1]):
                        raise CoconutException("Invalid number of string closes in "+self.getpart(inputstring, x))
                    elif hold[2] == hold[1]:
                        out.append(self.wrapstr(hold[0], hold[1][0] in self.raw, True))
                        hold = None
                        x -= 1
                    else:
                        hold[0] += hold[2]+c
                        hold[2] = None
                elif hold[0].endswith(self.escape) and not hold[0].endswith(self.escape*2):
                    hold[0] += c
                elif c == hold[1]:
                    out.append(self.wrapstr(hold[0], hold[1] in self.raw, False))
                    hold = None
                elif c == hold[1][0]:
                    hold[2] = c
                else:
                    hold[0] += c
            elif found is not None:
                if c == found[0]:
                    found += c
                elif len(found) == 1:
                    hold = [c, found, None]
                    found = None
                elif len(found) == 2:
                    out.append(self.wrapstr("", False, False))
                    found = None
                    x -= 1
                elif len(found) == 3:
                    hold = [c, found, None]
                    found = None
                else:
                    raise CoconutException("Invalid number of string starts in "+self.getpart(inputstring, x))
            elif c in self.startcomment:
                hold = [""]
            elif c in self.holds:
                found = c
            else:
                out.append(c)
            x += 1
        if hold is not None or found is not None:
            raise CoconutException("Unclosed string in "+self.getpart(inputstring, x))
        return "".join(out)

    indchar = None
    def leading(self, inputstring):
        """Counts Leading Whitespace."""
        count = 0
        for c in inputstring:
            if c not in self.white:
                break
            elif self.indchar is None:
                self.indchar = c
            elif self.indchar != c:
                raise CoconutException("Illegal mixing of tabs and spaces in "+repr(inputstring))
            count += 1
        return count

    def change(self, inputstring):
        """Determines The Parenthetical Change Of Level."""
        count = 0
        hold = None
        for c in inputstring:
            if hold:
                if c == self.escape:
                    hold[1] = not hold[1]
                elif hold[1]:
                    hold[1] = False
                elif c == hold[0]:
                    hold = None
            elif c in self.startcomment:
                break
            elif c in self.holds:
                hold = [c, False]
            elif c in self.downs:
                count -= 1
            elif c in self.ups:
                count += 1
        return count

    def indproc(self, inputstring):
        """Processes Indentation."""
        lines = inputstring.splitlines()
        new = []
        levels = []
        count = 0
        current = None
        for line in lines:
            if not line or line.startswith(self.startcomment):
                new.append(line)
            elif line[-1] in self.white:
                raise CoconutException("Illegal trailing whitespace in "+repr(line))
            elif count < 0:
                new[-1] += line
            else:
                check = self.leading(line)
                if current is None:
                    if check:
                        raise CoconutException("Illegal initial indent in "+repr(line))
                    else:
                        current = 0
                elif check > current:
                    levels.append(current)
                    current = check
                    line = self.openstr+line
                elif check in levels:
                    point = levels.index(check)+1
                    line = self.closestr*(len(levels[point:])+1)+line
                    levels = levels[:point]
                    current = levels.pop()
                elif current != check:
                    raise CoconutException("Illegal dedent to unused indentation level in "+repr(line))
                new.append(line)
            count += self.change(line)
        if count != 0:
            raise CoconutException("Unclosed parenthetical in "+repr(new[-1]))
        new.append(self.closestr*len(levels))
        return self.linebreak.join(new)

    def reindent(self, inputstring):
        """Reconverts Indent Tokens Into Indentation."""
        out = []
        level = 0
        hold = None
        for line in inputstring.splitlines():
            if hold is None and not line.startswith(self.startcomment):
                while line.startswith(self.openstr) or line.startswith(self.closestr):
                    if line[0] == self.openstr:
                        level += 1
                    elif line[0] == self.closestr:
                        level -= 1
                    line = line[1:]
                line = " "*self.tablen*level + line
            for c in line:
                if hold:
                    if c == self.escape:
                        hold[1] = not hold[1]
                    elif hold[1]:
                        hold[1] = False
                    elif c == hold[0]:
                        hold = None
                elif c in self.holds:
                    hold = [c, False]
            if hold is None:
                line = line.rstrip()
            out.append(line)
        return self.linebreak.join(out)

    def post(self, tokens, header=True):
        """Performs Post-Processing."""
        if len(tokens) == 1:
            out = ""
            if header:
                out += HEADER
            out += self.reindent(tokens[0].strip()).strip()+self.linebreak
            return out
        else:
            raise CoconutException("Multiple tokens leftover: "+repr(tokens))

    def string_repl(self, tokens):
        """Replaces String References."""
        if len(tokens) == 1:
            tokens[0] = self.refs[int(tokens[0])]
            if isinstance(tokens[0], tuple):
                tokens[0], raw, multiline = tokens[0]
                if tokens[0]:
                    if tokens[0][-1] == '"':
                        tokens[0] = tokens[0][:-1]+'\\"'
                    if tokens[0][0] == '"':
                        tokens[0] = "\\"+tokens[0]
                if multiline:
                    tokens[0] = '"""'+tokens[0]+'"""'
                else:
                    tokens[0] = '"'+tokens[0]+'"'
                if raw:
                    return "r"+tokens[0]
                else:
                    return "u"+tokens[0]
            else:
                raise CoconutException("String marker points to comment")
        else:
            raise CoconutException("Invalid string marker")

    def comment_repl(self, tokens):
        """Replaces Comment References."""
        if len(tokens) == 1:
            tokens[0] = self.refs[int(tokens[0])]
            if isinstance(tokens[0], tuple):
                raise CoconutException("Comment marker points to string")
            else:
                return "#"+tokens[0]
        else:
            raise CoconutException("Invalid comment marker")

    def init(self):
        """Initializes The Strings And Comments."""
        self.string_ref <<= trace(attach(self.string_marker, self.string_repl), "string_ref")
        self.comment <<= trace(attach(self.comment_marker, self.comment_repl), "comment")

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# GRAMMAR:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    ParserElement.setDefaultWhitespaceChars(white)

    comma = Literal(",")
    dot = Literal(".")
    star = Literal("*")
    dubstar = Literal("**")
    lparen = Literal("(")
    rparen = Literal(")")
    at = Literal("@")
    arrow = fixto(Literal("->") | Literal("\u2192"), "->")
    heavy_arrow = fixto(Literal("=>") | Literal("\u21d2"), "=>")
    colon = Literal(":")
    semicolon = Literal(";")
    equals = Literal("=")
    lbrack = Literal("[")
    rbrack = Literal("]")
    lbrace = Literal("{")
    rbrace = Literal("}")
    plus = Literal("+")
    minus = Literal("-")
    bang = fixto(Literal("!") | Literal("\xac"), "!")
    slash = Literal("/")
    dubslash = fixto(Literal("//") | Literal("\u20eb"), "//")
    pipeline = fixto(Literal("|>") | Literal("\u21a6"), "|>")
    amp = fixto(Literal("&") | Literal("\u2227") | Literal("\u2229"), "&")
    caret = fixto(Literal("^") | Literal("\u22bb") | Literal("\u2295"), "^")
    bar = fixto(Literal("|") | Literal("\u2228") | Literal("\u222a"), "|")
    percent = Literal("%")
    dotdot = Literal("..")
    dollar = Literal("$")
    ellipses = fixto(Literal("...") | Literal("\u2026"), "...")
    lshift = fixto(Literal("<<") | Literal("\xab"), "<<")
    rshift = fixto(Literal(">>") | Literal("\xbb"), ">>")
    tilde = fixto(Literal("~") | Literal("\xac"), "~")
    underscore = Literal("_")
    pound = Literal("#")
    backslash = Literal("\\")

    mul_star = fixto(star | Literal("\xd7"), "*")
    exp_dubstar = fixto(star | Literal("\xd7\xd7") | Literal("\u2191"), "**")
    neg_minus = fixto(minus | Literal("\u207b"), "-")
    sub_minus = fixto(minus | Literal("\u2212"), "-")
    div_slash = fixto(slash | Literal("\xf7"), "/")
    div_dubslash = fixto(dubslash | Combine(Literal("\xf7"), slash), "//")

    NAME = Regex("(?![0-9])\\w+")
    dotted_name = condense(NAME + ZeroOrMore(dot + NAME))

    integer = Word(nums)
    binint = Word("01")
    octint = Word("01234567")
    hexint = Word(hexnums)
    anyint = Word(nums, alphanums)

    basenum = Combine(integer + dot + Optional(integer)) | integer
    sci_e = CaselessLiteral("e") | fixto(Literal("\u23e8"), "E")
    numitem = Combine(basenum + sci_e + integer) | basenum

    NUMBER = trace(attach(Combine(anyint + underscore + integer), anyint_proc)
              | Combine(CaselessLiteral("0b") + binint)
              | Combine(CaselessLiteral("0o") + octint)
              | Combine(CaselessLiteral("0x") + hexint)
              | numitem
              , "NUMBER")

    string_ref = Forward()
    comment = Forward()

    string_marker = Combine(Literal('"').suppress() + integer + Literal('"').suppress())
    comment_marker = Combine(pound.suppress() + integer)

    bit_b = CaselessLiteral("b")
    STRING = Combine(Optional(bit_b) + string_ref)
    lineitem = Combine(Optional(comment) + Literal(linebreak))
    NEWLINE = condense(OneOrMore(lineitem))
    STARTMARKER = StringStart()
    ENDMARKER = StringEnd()
    INDENT = Literal(openstr) + Optional(NEWLINE)
    DEDENT = Literal(closestr) + Optional(NEWLINE)

    augassign = (heavy_arrow
                 | Combine(plus + equals)
                 | Combine(sub_minus + equals)
                 | Combine(mul_star + equals)
                 | Combine(exp_dubstar + equals)
                 | Combine(div_slash + equals)
                 | Combine(percent + equals)
                 | Combine(amp + equals)
                 | Combine(bar + equals)
                 | Combine(caret + equals)
                 | Combine(lshift + equals)
                 | Combine(rshift + equals)
                 | Combine(div_dubslash + equals)
                 | Combine(dotdot + equals)
                 )

    lt = Literal("<")
    gt = Literal(">")
    eq = Combine(equals + equals)
    le = fixto(Combine(lt + equals) | Literal("\u2264"), "<=")
    ge = fixto(Combine(gt + equals) | Literal("\u2265"), ">=")
    ne = fixto(Combine(bang + equals) | Literal("\u2260"), "!=")

    comp_op = (le | ge | ne | lt | gt | eq
               | addspace(Keyword("not") + Keyword("in"))
               | Keyword("in")
               | addspace(Keyword("is") + Keyword("not"))
               | Keyword("is")
               )

    test = Forward()
    expr = Forward()
    comp_for = Forward()

    vardef = NAME
    tfpdef = condense(vardef + Optional(colon + test))
    callarg = test
    default = Optional(condense(equals + test))

    argslist = Optional(itemlist(condense(dubstar + tfpdef | star + tfpdef | tfpdef + default), comma))
    varargslist = Optional(itemlist(condense(dubstar + vardef | star + vardef | vardef + default), comma))
    callargslist = Optional(itemlist(condense(dubstar + callarg | star + callarg | callarg + default), comma))

    parameters = condense(lparen + argslist + rparen)

    testlist = itemlist(test, comma)
    yield_arg = addspace(Keyword("from") + test) | testlist
    yield_expr = addspace(Keyword("yield") + Optional(yield_arg))
    star_expr = condense(star + expr)
    test_star_expr = star_expr | test
    testlist_star_expr = itemlist(test_star_expr, comma)
    testlist_comp = addspace(test_star_expr + comp_for) | testlist_star_expr
    dictorsetmaker = addspace(condense(test + colon) + test + comp_for
                      ^ itemlist(condense(test + colon) + test, comma)
                      ^ test + comp_for
                      ^ testlist
                      )

    op_atom = trace(lparen + (
        fixto(exp_dubstar, "__coconut__.operator.__pow__")
        | fixto(mul_star, "__coconut__.operator.__mul__")
        | fixto(div_slash, "__coconut__.operator.__truediv__")
        | fixto(div_dubslash, "__coconut__.operator.__floordiv__")
        | fixto(percent, "__coconut__.operator.__mod__")
        | fixto(plus, "__coconut__.operator.__add__")
        | fixto(sub_minus, "__coconut__.operator.__sub__")
        | fixto(neg_minus, "__coconut__.operator.__neg__")
        | fixto(amp, "__coconut__.operator.__and__")
        | fixto(caret, "__coconut__.operator.__xor__")
        | fixto(bar, "__coconut__.operator.__or__")
        | fixto(lshift, "__coconut__.operator.__lshift__")
        | fixto(rshift, "__coconut__.operator.__rshift__")
        | fixto(lt, "__coconut__.operator.__lt__")
        | fixto(gt, "__coconut__.operator.__gt__")
        | fixto(eq, "__coconut__.operator.__eq__")
        | fixto(le, "__coconut__.operator.__le__")
        | fixto(ge, "__coconut__.operator.__ge__")
        | fixto(ne, "__coconut__.operator.__ne__")
        | fixto(tilde, "__coconut__.operator.__inv__")
        | fixto(pipeline, "__coconut__.pipe")
        | fixto(dotdot, "__coconut__.compose")
        ) + rparen, "op_atom")

    func_atom = NAME | op_atom | condense(lparen + Optional(yield_expr | testlist_comp) + rparen)
    keyword_atom = Keyword("None") | Keyword("True") | Keyword("False")
    atom = (keyword_atom
            | ellipses
            | condense(lbrack + Optional(testlist_comp) + rbrack)
            | condense(lbrace + Optional(dictorsetmaker) + rbrace)
            | NUMBER
            | OneOrMore(STRING)
            | func_atom
            )
    sliceop = condense(colon + Optional(test))
    subscript = test ^ condense(Optional(test) + sliceop + Optional(sliceop))
    subscriptlist = itemlist(subscript, comma)
    simple_trailer = condense(lbrack + subscriptlist + rbrack) | condense(dot + NAME)
    trailer = trace(Group(dollar + lparen.suppress() + callargslist + rparen.suppress())
               | condense(lparen + callargslist + rparen)
               | Group(dotdot + func_atom)
               | simple_trailer
               , "trailer")

    assignlist = Forward()
    assign_item = NAME + ZeroOrMore(simple_trailer) | lparen + assignlist + rparen | lbrack + assignlist + rbrack
    assignlist <<= itemlist(Optional(star) + assign_item, comma)

    atom_item = trace(attach(atom + ZeroOrMore(trailer), item_proc), "atom_item")

    factor = Forward()
    power = trace(condense(atom_item + Optional(exp_dubstar + factor)), "power")
    unary = plus | neg_minus | tilde

    factor <<= trace(condense(unary + factor) | power, "factor")

    mulop = mul_star | div_slash | div_dubslash | percent
    term = addspace(factor + ZeroOrMore(mulop + factor))
    arith = plus | sub_minus
    arith_expr = addspace(term + ZeroOrMore(arith + term))

    infix_expr = attach(arith_expr + ZeroOrMore(backslash.suppress() + test + backslash.suppress() + arith_expr), infix_proc)

    shift = lshift | rshift
    shift_expr = addspace(loop_expr + ZeroOrMore(shift + infix_expr))
    and_expr = addspace(shift_expr + ZeroOrMore(amp + shift_expr))
    xor_expr = addspace(and_expr + ZeroOrMore(caret + and_expr))
    or_expr = addspace(xor_expr + ZeroOrMore(bar + xor_expr))

    pipe_expr = attach(or_expr + ZeroOrMore(pipeline.suppress() + or_expr), pipe_proc)

    expr <<= trace(pipe_expr, "expr")
    comparison = addspace(expr + ZeroOrMore(comp_op + expr))
    not_test = addspace(ZeroOrMore(Keyword("not")) + comparison)
    and_test = addspace(not_test + ZeroOrMore(Keyword("and") + not_test))
    or_test = addspace(and_test + ZeroOrMore(Keyword("or") + and_test))
    test_item = or_test
    test_nocond = Forward()
    lambdef_params = lparen.suppress() + varargslist + rparen.suppress()

    lambdef = trace(attach(lambdef_params + arrow.suppress() + test, lambda_proc), "lambdef")
    lambdef_nocond = trace(attach(lambdef_params + arrow.suppress() + test_nocond, lambda_proc), "lambdef_nocond")

    test <<= lambdef | trace(addspace(test_item + Optional(Keyword("if") + test_item + Keyword("else") + test)), "test")
    test_nocond <<= lambdef_nocond | trace(test_item, "test_item")
    exprlist = itemlist(star_expr | expr, comma)

    suite = Forward()

    argument = condense(NAME + equals + test) | addspace(NAME + Optional(comp_for))
    classdef = condense(addspace(Keyword("class") + NAME) + Optional(parameters) + suite)
    comp_iter = Forward()
    comp_for <<= addspace(Keyword("for") + exprlist + Keyword("in") + test_item + Optional(comp_iter))
    comp_if = addspace(Keyword("if") + test_nocond + Optional(comp_iter))
    comp_iter <<= comp_for | comp_if

    pass_stmt = Keyword("pass")
    break_stmt = Keyword("break")
    continue_stmt = Keyword("continue")
    return_stmt = addspace(Keyword("return") + Optional(testlist))
    yield_stmt = yield_expr
    raise_stmt = addspace(Keyword("raise") + Optional(test + Optional(Keyword("from") + test)))
    flow_stmt = break_stmt | continue_stmt | return_stmt | raise_stmt | yield_stmt

    dotted_as_name = addspace(dotted_name + Optional(Keyword("as") + NAME))
    import_as_name = addspace(NAME + Optional(Keyword("as") + NAME))
    import_as_names = itemlist(import_as_name, comma)
    dotted_as_names = itemlist(dotted_as_name, comma)
    import_name = addspace(Keyword("import") + parenwrap(lparen, dotted_as_names, rparen))
    import_from = addspace(Keyword("from") + condense(ZeroOrMore(dot) + dotted_name | OneOrMore(dot))
                   + Keyword("import") + (star | parenwrap(lparen, import_as_names, rparen)))
    import_stmt = import_from | import_name

    namelist = parenwrap(lparen, itemlist(NAME, comma), rparen)
    global_stmt = addspace(Keyword("global") + namelist)
    nonlocal_stmt = addspace(Keyword("nonlocal") + namelist)
    del_stmt = addspace(Keyword("del") + namelist)
    with_item = addspace(test + Optional(Keyword("as") + NAME))
    assert_stmt = addspace(Keyword("assert") + parenwrap(lparen, testlist, rparen))
    else_stmt = condense(Keyword("else") + suite)
    if_stmt = condense(addspace(Keyword("if") + condense(test + suite))
                       + ZeroOrMore(addspace(Keyword("elif") + condense(test + suite)))
                       + Optional(else_stmt)
                       )
    while_stmt = addspace(Keyword("while") + condense(test + suite + Optional(else_stmt)))
    for_stmt = addspace(Keyword("for") + exprlist + Keyword("in") + condense(testlist + suite + Optional(else_stmt)))
    except_clause = addspace(Keyword("except") + test + Optional(Keyword("as") + NAME))
    try_stmt = condense(Keyword("try") + suite + (
        Keyword("finally") + suite
        | (
            OneOrMore(except_clause + suite) + Optional(Keyword("except") + suite)
            | Keyword("except") + suite
            ) + Optional(else_stmt) + Optional(Keyword("finally") + suite)
        ))
    with_stmt = addspace(Keyword("with") + condense(parenwrap(lparen, itemlist(with_item, comma), rparen) + suite))

    decorator = condense(at + test + NEWLINE)
    decorators = OneOrMore(decorator)
    base_funcdef = addspace(condense(NAME + parameters) + Optional(arrow + test))
    funcdef = addspace(Keyword("def") + condense(base_funcdef + suite))
    decorated = condense(decorators + (classdef | funcdef))

    compound_stmt = trace(if_stmt | while_stmt | for_stmt | try_stmt | with_stmt | funcdef | classdef | decorated, "compound_stmt")

    expr_stmt = trace(addspace(attach(assignlist + augassign + (yield_expr | testlist), assign_proc)
                         | attach(base_funcdef + equals.suppress() + (yield_expr | testlist_star_expr), func_proc)
                         | ZeroOrMore(assignlist + equals) + (yield_expr | testlist_star_expr)
                         ), "expr_stmt")

    keyword_stmt = del_stmt | pass_stmt | flow_stmt | import_stmt | global_stmt | nonlocal_stmt | assert_stmt
    small_stmt = trace(keyword_stmt ^ expr_stmt, "small_stmt")
    simple_stmt = trace(condense(itemlist(small_stmt, semicolon) + NEWLINE), "simple_stmt")
    stmt = trace(compound_stmt | simple_stmt, "stmt")
    suite <<= trace(condense(colon + NEWLINE + INDENT + OneOrMore(stmt) + DEDENT) | addspace(colon + simple_stmt), "suite")

    single_input = trace(NEWLINE | stmt, "single_input")
    file_input = trace(condense(ZeroOrMore(single_input)), "file_input")
    eval_input = trace(condense(testlist + NEWLINE), "eval_input")

    single_parser = condense(STARTMARKER + single_input + ENDMARKER)
    file_parser = condense(STARTMARKER + file_input + ENDMARKER)
    eval_parser = condense(STARTMARKER + eval_input + ENDMARKER)

    def parse_single(self, inputstring):
        """Processes Console Input."""
        out = self.post(self.single_parser.parseString(self.pre(inputstring)))
        self.clean()
        return out

    def parse_file(self, inputstring):
        """Processes File Input."""
        out = self.post(self.file_parser.parseString(self.pre(inputstring)))
        self.clean()
        return out

    def parse_eval(self, inputstring):
        """Processes Eval Input."""
        out = self.post(self.eval_parser.parseString(self.pre(inputstring, True)))
        self.clean()
        return out

    def parse_debug(self, inputstring):
        """Processes Debug Input."""
        out = self.post(self.file_parser.parseString(self.pre(inputstring, True)), False)
        self.clean()
        return out

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# MAIN:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

PROCESSOR = processor()

def parse_single(inputstring):
    """Processes Console Input."""
    return PROCESSOR.parse_single(inputstring)

def parse_file(inputstring):
    """Processes File Input."""
    return PROCESSOR.parse_file(inputstring)

def parse_eval(inputstring):
    """Processes Eval Input."""
    return PROCESSOR.parse_eval(inputstring)

def parse_debug(inputstring):
    """Processes Debug Input."""
    return PROCESSOR.parse_debug(inputstring)

if __name__ == "__main__":
    print(parse_file(readfile(openfile(DIRECTORY, "r"))))
