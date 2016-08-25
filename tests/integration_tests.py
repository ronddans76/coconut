#!/usr/bin/env python
"""
Authors: Fred Buchanan
License: Apache 2.0
Description: Integration tests for coconut
"""

from __future__ import print_function, absolute_import, unicode_literals, division

import unittest
import sys
import os
import subprocess
import shutil


class OldCocoTest(unittest.TestCase):


    def compile_extras(self,extraCommands = []):
        src = os.path.join(self.src,"extras.coco")

        cmd = ["coconut"] + extraCommands + [src,self.bin]
        subprocess.check_call(cmd)

    def compile_runner(self,extraCommands = []):
        src = os.path.join(self.src,"src","runner.coco")

        cmd = ["coconut"] + extraCommands + [src,self.bin]
        subprocess.check_call(cmd)

    def compile_agnostic(self,extraCommands = []):
        src = os.path.join(self.src,"src","agnostic")
        bin = os.path.join(self.bin,"cocotest")

        cmd = ["coconut"] + extraCommands + [src,bin]
        subprocess.check_call(cmd)

    def compile_2(self,extraCommands = []):
        src = os.path.join(self.src,"src","python2")
        bin = os.path.join(self.bin,"cocotest")

        cmd = ["coconut","--target","2"] + extraCommands + [src,bin]
        subprocess.check_call(cmd)

    def compile_3(self,extraCommands = []):
        src = os.path.join(self.src,"src","python3")
        bin = os.path.join(self.bin,"cocotest")

        cmd = ["coconut","--target","3"] + extraCommands + [src,bin]
        subprocess.check_call(cmd)

    def compile_35(self,extraCommands = []):
        src = os.path.join(self.src,"src","python35")
        bin = os.path.join(self.bin,"cocotest")

        cmd = ["coconut","--target","35"] + extraCommands + [src,bin]
        subprocess.check_call(cmd)

    def run_source(self):
        subprocess.check_call(["python",os.path.join(self.bin,"runner.py")])

    def compile_source(self,agnosticTarget = None, stict = False, minify = False, line_numbers = False, keep_lines = False):

        agnosticCommands = []
        extraCommands = []
        if agnosticTarget != None:
            agnosticCommands += ["--target",agnosticTarget]
        if stict:
            extraCommands += ["--stict"]
        if line_numbers:
            extraCommands += ["--line-numbers"]
        if keep_lines:
            extraCommands += ["--keep-lines"]

        self.compile_runner(extraCommands+agnosticCommands)
        self.compile_agnostic(extraCommands+agnosticCommands)
        
        if sys.version_info >= (3,):
            self.compile_3(extraCommands)
        if sys.version_info >= (3,5):
            self.compile_35(extraCommands)
        if (sys.version_info >= (2,)) & (sys.version_info < (3,)):
            self.compile_2(extraCommands)

    def clean(self):
        shutil.rmtree(self.bin)

    def setUp(self):
        self.src = os.path.join(os.path.abspath(os.path.dirname(__file__)),"src")
        self.bin = os.path.join(os.path.abspath(os.path.dirname(__file__)),"bin")

    def tearDown(self):
        try:
            self.clean()
        except FileNotFoundError:
            pass

    def test_normal(self):
        self.compile_source()
        self.run_source()
        self.clean()

    def test_strict(self):
        self.compile_source(stict = True)
        self.run_source()
        self.clean()

    def test_minify(self):
        self.compile_source(minify = True)
        self.run_source()
        self.clean()

    def test_line_numbers(self):
        self.compile_source(line_numbers = True)
        self.run_source()
        self.clean()

    def test_keep_lines(self):
        self.compile_source(keep_lines = True)
        self.run_source()
        self.clean()
        
    def test_version_target(self):
        version = "".join([str(sys.version_info.major),str(sys.version_info.minor)])
        self.compile_source(agnosticTarget = version)
        self.run_source()
        self.clean()
        
    def test_extra(self):
        self.compile_extras()
        subprocess.check_call(["python",os.path.join(self.bin,"extras.py")])
        self.clean()

if __name__ == '__main__':
    unittest.main()

