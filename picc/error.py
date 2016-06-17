
'''Print error messages.

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
__version__ = '0.2.2'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'

PROGNAME = sys.argv[0]

# Use colors if in a terminal
if sys.stdout.isatty():
    RED = '\033[31m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
else:
    RED = ''
    YELLOW = ''
    CYAN = ''
    BOLD = ''
    RESET = ''

errors = 0

class Error(object):
    def __init__(self):
        self.errcount = 0
    def error(self, msg, coord):
        msg = msg.replace('#', BOLD)
        msg = msg.replace('$', RESET)
        print('{b}{file}:{line}:{col}: {r}error: {re}{msg}'.format(
            b=BOLD, file=coord.file, line=coord.line, col=coord.column, r=RED,
            re=RESET, msg=msg), file=sys.stderr)
        self.errcount += 1
    def note(self, msg, coord):
        msg = msg.replace('#', BOLD)
        msg = msg.replace('$', RESET)
        print('{b}{file}:{line}:{col}: {c}note: {re}{msg}'.format(
            b=BOLD, file=coord.file, line=coord.line, col=coord.column,
            c=CYAN, re=RESET, msg=msg), file=sys.stderr)
    def warn(self, msg, coord):
        msg = msg.replace('#', BOLD)
        msg = msg.replace('$', RESET)
        print('{b}{file}:{line}:{col}: {y}warning: {re}{msg}'.format(
            b=BOLD, file=coord.file, line=coord.line, col=coord.column,
            y=YELLOW, re=RESET, msg=msg), file=sys.stderr)

def fatal(msg):
    '''Prints a fatal error and exits.'''
    print('{b}{prog}: {r}fatal:{re} {msg}'.format(prog=PROGNAME, msg=msg,
        b=BOLD, r=RED, re=RESET), file=sys.stderr)
    sys.exit(1)

def fatalf(filename, msg):
    '''Prints a fatal error occurred while treating a given file and exits.'''
    print('{b}{file}: {r}fatal:{re} {msg}'.format(file=filename, msg=msg,
        b=BOLD, r=RED, re=RESET), file=sys.stderr)
    sys.exit(1)

def errorf(filename, msg):
    '''Prints an error message.'''
    global errors
    print('{b}{file}: {r}error:{re} {msg}'.format(file=filename, msg=msg,
        b=BOLD, r=RED, re=RESET), file=sys.stderr)
    errors += 1

def errorfa(filename, section, offset, msg):
    '''Prints an error message.'''
    global errors
    print('{b}{file}:{section}+{offset:#x}: {r}error:{re} {msg}'.format(
        file=filename, section=section, offset=offset, msg=msg, b=BOLD, r=RED,
        re=RESET), file=sys.stderr)
    errors += 1

def warnf(filename, msg):
    '''Prints a warning message.'''
    print('{b}{file}: {y}warning:{re} {msg}'.format(file=filename, msg=msg,
        b=BOLD, y=YELLOW, re=RESET), file=sys.stderr)

def notefa(filename, section, offset, msg):
    '''Prints a note.'''
    print('{b}{file}:{section}+{offset:#x}: {c}note:{re} {msg}'.format(
        file=filename, section=section, offset=offset, msg=msg, b=BOLD, c=CYAN,
        re=RESET), file=sys.stderr)

