
'''error.py - Inspect Microchip's PIC objects in COFF format.

Copyright 2016 Antonio Serrano Hernandez

This file is part of picc.

picc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

picc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with picc; see the file COPYING.  If not, see
<http://www.gnu.org/licenses/>.
'''

from __future__ import print_function
import sys

__author__ = 'Antonio Serrano Hernandez'
__copyright__ = 'Copyright (C) 2016 Antonio Serrano Hernandez'
__version__ = '0.1.0'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'

PROGNAME = sys.argv[0]

def fatal(msg):
    '''Prints a fatal error and exits.'''
    print('{prog}: fatal: {msg}'.format(prog=PROGNAME, msg=msg),
        file=sys.stderr)
    exit(1)

def fatalf(filename, msg):
    '''Prints a fatal error occurred while treating a given file and exits.'''
    print('{file}: fatal: {msg}'.format(file=filename, msg=msg),
        file=sys.stderr)
    exit(1)

def errorf(filename, msg):
    '''Prints an error message.'''
    print('{file}: error: {msg}'.format(file=filename, msg=msg),
        file=sys.stderr)

def errorfa(filename, section, offset, msg):
    '''Prints an error message.'''
    print('{file}:{section}+{offset:#x}: error: {msg}'.format(
        file=filename, section=section, offset=offset, msg=msg),
        file=sys.stderr)

def warnf(filename, msg):
    '''Prints a warning message.'''
    print('{file}: warning: {msg}'.format(file=filename, msg=msg),
        file=sys.stderr)

