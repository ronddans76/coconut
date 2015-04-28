#!/usr/bin/env python

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# INFO:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

"""
Author: Evan Hubinger
Date Created: 2014
Description: Coconut Language Installer.
"""

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# IMPORTS:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

from __future__ import with_statement, print_function, absolute_import, unicode_literals, division

import sys
import os.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coconut.util import *
import setuptools

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# MAIN:
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

with openfile("README.rst", "r") as opened:
    readme = readfile(opened)

setuptools.setup(
    name="coconut",
    version=VERSION,
    description="The Coconut Programming Language.",
    long_description=readme,
    url="https://github.com/evhub/coconut",
    author="Evan Hubinger",
    author_email="evanjhub@gmail.com",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Other",
        "Programming Language :: Other Scripting Engines",
        "Framework :: IPython",
        "Development Status :: 3 - Alpha"
        ],
    keywords=["functional programming language"],
    packages=setuptools.find_packages(),
    install_requires=["pyparsing"],
    entry_points={"console_scripts":[
        "coconut = coconut.__main__:main"
        ]}
    )
