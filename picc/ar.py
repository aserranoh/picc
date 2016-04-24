
'''Extract COFF file objects from an ar file.

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

import io

from . import coff, error

__author__ = 'Antonio Serrano Hernandez'
__copyright__ = 'Copyright (C) 2016 Antonio Serrano Hernandez'
__version__ = '0.2.2'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'

_AR_MAGIC_SIZE = 8
_AR_MAGIC = '!<arch>\n'
_AR_HEADER_SIZE = 60

def _getlongname(table, index):
    i = index
    while table[i] != '/': i += 1
    return table[index:i]

def extract(stream):
    '''Extract the COFF objects from this ar file.'''
    objects = []
    stream.seek(_AR_MAGIC_SIZE)
    try:
        hdr = stream.read(_AR_HEADER_SIZE).decode('ascii')
        while len(hdr) == _AR_HEADER_SIZE:
            filename = hdr[:16].rstrip()
            timestamp = hdr [16:28]
            uid = hdr[28:34]
            gid = hdr[34:40]
            mode = hdr[40:48]
            size = int(hdr[48:58])
            magic = hdr[58:]
            # Check if this register is the table of long names
            if filename == '//':
                namestable = stream.read(size)
                if len(namestable) != size:
                    error.fatalf(stream.name, 'truncated ar long names table')
                namestable = namestable.decode('ascii')
            else:
                # This is a COFF object
                if filename[0] == '/':
                    filename = _getlongname(namestable, int(filename[1:]))
                bytestream = io.BytesIO(stream.read(size))
                bytestream.name = stream.name
                objects.append(coff.readcoff(bytestream))
                # If size is odd, read a padding byte
                if size % 2:
                    stream.read(1)
            hdr = stream.read(_AR_HEADER_SIZE).decode('ascii')
        if len(hdr):
            error.fatalf(stream.name, 'truncated ar header')
        return objects
    except (UnicodeDecodeError, ValueError, IndexError) as e:
        error.fatalf(stream.name, str(e))

def isar(stream):
    '''Check if the given filename corresponds to an ar file.'''
    current = stream.tell()
    res = False
    try:
        magic = stream.read(_AR_MAGIC_SIZE).decode('ascii')
        res = (magic == _AR_MAGIC)
    except UnicodeDecodeError: pass
    stream.seek(current)
    return res

