
'''links Microchip's PIC objects in COFF format.

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

import intelhex
import os
import struct
import xml.etree.ElementTree as ET
from . import coff, error

__author__ = 'Antonio Serrano Hernandez'
__copyright__ = 'Copyright (C) 2016 Antonio Serrano Hernandez'
__version__ = '0.2.2'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'

_DATA_PATH = '/usr/share/picc'
_PROCESSORS_FILENAME = 'processors.xml'
_PROCESSORS_FILE = os.path.join(_DATA_PATH, _PROCESSORS_FILENAME)

_RELOCT_CALL = 1
_RELOCT_GOTO = 2
_RELOCT_HIGH = 3
_RELOCT_LOW = 4
_RELOCT_P = 5
_RELOCT_BANKSEL = 6
_RELOCT_PAGESEL = 7
_RELOCT_ALL = 8
_RELOCT_IBANKSEL = 9
_RELOCT_F = 10
_RELOCT_TRIS = 11
_RELOCT_MOVLR = 12
_RELOCT_MOVLB = 13
_RELOCT_GOTO2 = 14
_RELOCT_FF1 = 15
_RELOCT_FF2 = 16
_RELOCT_LFSR1 = 17
_RELOCT_LFSR2 = 18
_RELOCT_BRA_RCALL = 19
_RELOCT_CONDBRA = 20
_RELOCT_UPPER = 21
_RELOCT_ACCESS = 22
_RELOCT_PAGESEL_WREG = 23
_RELOCT_PAGESEL_BITS = 24
_RELOCT_SCNSZ_LOW = 25
_RELOCT_SCNSZ_HIGH = 26
_RELOCT_SCNSZ_UPPER = 27
_RELOCT_SCNEND_LOW = 28
_RELOCT_SCNEND_HIGH = 29
_RELOCT_SCNEND_UPPER = 30
_RELOCT_SCNEND_LFSR1 = 31
_RELOCT_SCNEND_LFSR2 = 32

# The argument of the lambda functions is a RelocationContext object.

def unimplemented_patch(patch_code):
    return lambda c: error.fatalf(c.filename,
        'unimplemented relocation {}'.format(patch_code))

def bra_rcall_patch(c):
    opcode = c.opcode
    offset = int((c.value - c.address - 2)/2)
    if offset < -1024 or offset > 1023:
        error.errorfa(c.filename, c.section.name, c.offset,
            "relative jump too long (use {b}'goto'{re} or {b}'call'{re} "
            "instead)".format(b=error.BOLD, re=error.RESET))
    else:
        opcode = c.opcode | (offset & 0x07ff)
    return opcode

def condbra_patch(c):
    opcode = c.opcode
    offset = int((c.value - c.address - 2)/2)
    if offset < -128 or offset > 127:
        error.errorfa(c.filename, c.section.name, c.offset,
            "conditional branch too long (use {b}'goto'{re} instead)".format(
            b=error.BOLD, re=error.RESET))
    else:
        opcode = c.opcode | (offset & 0xff)
    return opcode

_RELOCT_DICT = {
    _RELOCT_CALL: lambda c: c.opcode | (int(c.value/2) & 0xff),
    _RELOCT_GOTO: lambda c: c.opcode | (int(c.value/2) & 0xff),
    _RELOCT_HIGH: unimplemented_patch(_RELOCT_HIGH),
    _RELOCT_LOW: unimplemented_patch(_RELOCT_LOW),
    _RELOCT_P: unimplemented_patch(_RELOCT_P),
    _RELOCT_BANKSEL: unimplemented_patch(_RELOCT_BANKSEL),
    _RELOCT_PAGESEL: unimplemented_patch(_RELOCT_PAGESEL),
    _RELOCT_ALL: unimplemented_patch(_RELOCT_ALL),
    _RELOCT_IBANKSEL: unimplemented_patch(_RELOCT_IBANKSEL),
    _RELOCT_F: lambda c: c.opcode | (c.value & 0xff),
    _RELOCT_TRIS: unimplemented_patch(_RELOCT_TRIS),
    _RELOCT_MOVLR: unimplemented_patch(_RELOCT_MOVLR),
    _RELOCT_MOVLB: unimplemented_patch(_RELOCT_MOVLB),
    _RELOCT_GOTO2: lambda c: c.opcode | ((int(c.value/2) >> 8) & 0xfff),
    _RELOCT_FF1: lambda c: c.opcode | (c.value & 0xfff),
    _RELOCT_FF2: lambda c: c.opcode | (c.value & 0xfff),
    _RELOCT_LFSR1: lambda c: c.opcode | ((c.value >> 8) & 0x0f),
    _RELOCT_LFSR2: lambda c: c.opcode | (c.value & 0xff),
    _RELOCT_BRA_RCALL: bra_rcall_patch,
    _RELOCT_CONDBRA: condbra_patch,
    _RELOCT_UPPER: unimplemented_patch(_RELOCT_UPPER),
    _RELOCT_ACCESS: lambda c: c.opcode & 0xfeff if c.value < c.picinfo.access
        else c.opcode | 0x0100,
    _RELOCT_PAGESEL_WREG: unimplemented_patch(_RELOCT_PAGESEL_WREG),
    _RELOCT_PAGESEL_BITS: unimplemented_patch(_RELOCT_PAGESEL_BITS),
    _RELOCT_SCNSZ_LOW: unimplemented_patch(_RELOCT_SCNSZ_LOW),
    _RELOCT_SCNSZ_HIGH: unimplemented_patch(_RELOCT_SCNSZ_HIGH),
    _RELOCT_SCNSZ_UPPER: unimplemented_patch(_RELOCT_SCNSZ_UPPER),
    _RELOCT_SCNEND_LOW: unimplemented_patch(_RELOCT_SCNEND_LOW),
    _RELOCT_SCNEND_HIGH: unimplemented_patch(_RELOCT_SCNEND_HIGH),
    _RELOCT_SCNEND_UPPER: unimplemented_patch(_RELOCT_SCNEND_UPPER),
    _RELOCT_SCNEND_LFSR1: unimplemented_patch(_RELOCT_SCNEND_LFSR1),
    _RELOCT_SCNEND_LFSR2: unimplemented_patch(_RELOCT_SCNEND_LFSR2),
}

class _RelocationContext(object):
    '''Gathers information to perform a relocation.'''

    def __init__(self, filename, section, offset, value, picinfo):
        self.filename = filename
        self.section = section
        self.offset = offset
        self.value = value
        self.picinfo = picinfo

    @property
    def address(self):
        return self.section.paddress + self.offset

    @property
    def opcode(self):
        return struct.unpack(
            '=H', self.section.data[self.offset:self.offset + 2])[0]

class _PicInfo(object):
    '''Holds some information about a PIC processor.'''

    def __init__(self, name, ram, access, progmem):
        '''Creates a PicInfo instance with the given information.
        
        name: the processor's name.
        ram: the size of RAM (excluding space for SFR).
        access: the size of access RAM.
        flash: the size of Flash memory (program memory).
        '''
        self.name = name
        self.ram = ram
        self.access = access
        self.progmem = progmem

class _FreeMemory(object):
    '''Represents a consecutive stream of free bytes.'''

    def __init__(self, start, size):
        self.start = start
        self.size = size

    def intersection(self, freemem):
        '''Returns a FreeMemory object intersection of these two.'''
        self_end = self.start + self.size - 1
        freemem_end = freemem.start + freemem.size - 1
        start = max(self.start, freemem.start)
        end = min(self_end, freemem_end)
        if start > end:
            i = None
        else:
            i = _FreeMemory(start, end - start + 1)
        return i

    def substract(self, freemem):
        '''Substracts freemem from this one.
        
        Precondition: freemem is contained in this _FreeMemory object.
        '''
        l = []
        freemem_end = freemem.start + freemem.size - 1
        self_end = self.start + self.size - 1
        if freemem.start > self.start:
            l.append(_FreeMemory(self.start, freemem.start - self.start))
        if freemem_end < self_end:
            l.append(_FreeMemory(freemem_end + 1, self_end - freemem_end))
        return l

    def contains(self, freemem):
        freemem_end = freemem.start + freemem.size
        self_end = self.start + self.size
        return freemem.start >= self.start and freemem_end <= self_end

    def __str__(self):
        return '({}, {})'.format(self.start, self.size)

class _MemoryAllocator(object):
    '''Allocates chunks of memory of a given memory space.'''

    def __init__(self, size):
        self.freemem = [_FreeMemory(0, size)]

    def alloc(self, size, start=None, end=None):
        '''Allocates size bytes of memory.
        
        size: number of bytes of the chunk to allocate.
        start: starting address of the chunk to allocate.
        end: end address of the chunk to allocate
        
        If only size is given, the chunk will be allocated in an arbitrary
        address, one with at least size bytes free behind.
        If both size and start are given, exactly size bytes will be allocated
        at exactly start address.
        If both size, start and end are given, size bytes will be allocated at
        some place between size and end (not included).
        '''
        address = None
        if start is not None and end is not None:
            # Search for a hole that intersects the given space whith enough
            # free bytes
            for i in range(len(self.freemem)):
                h = self.freemem[i]
                newh = h.intersection(_FreeMemory(start, end - start))
                if newh is not None and size <= newh.size:
                    address = newh.start
                    self.freemem[i:i + 1] = h.substract(
                        _FreeMemory(address, size))
                    break
        elif start is not None:
            # Search for the hole that contains the start address
            for i in range(len(self.freemem)):
                h = self.freemem[i]
                if h.contains(_FreeMemory(start, size)):
                    address = start
                    self.freemem[i:i + 1] = h.substract(
                        _FreeMemory(start, size))
                    break
        else:
            # Search for the first hole with size bytes available
            for i in range(len(self.freemem)):
                h = self.freemem[i]
                if size <= h.size:
                    address = h.start
                    # Put a new hole with the new size
                    self.freemem[i] = _FreeMemory(
                        h.start + size, h.size - size)
                    break
        return address

def _loadpicinfo(processor):
    '''Load the processor's information needed by the linker.'''
    try:
        tree = ET.parse(_PROCESSORS_FILE)
        for p in tree.getroot():
            if processor == p.attrib['name']:
                return _PicInfo(processor, int(p.attrib['ram'], 16),
                    int(p.attrib['access'], 16), int(p.attrib['progmem'], 16))
        error.fatal("info from processor {b}'{proc}'{re} not found".format(
            b=error.BOLD, re=error.RESET, proc=processor))
    except IOError as ioe:
        error.fatal('cannot load processor info: {}'.format(ioe))
    except KeyError as ke:
        error.fatal("malformed file {b}'{f}'{re}: missing attribute "
            "{attr}".format(b=error.BOLD, re=error.RESET, f=_PROCESSORS_FILE,
            attr=ke))

def _getallocator(obj, section, codemem, datamem):
    '''Returns the right allocator for the given section.'''
    allocator = None
    if section.iscode() or section.isprogramdata(): allocator = codemem
    elif section.isudata(): allocator = datamem
    return allocator

def _allocsections(objects, picinfo, codemem, datamem):
    '''Give absolute addresses to all sections.
    
    objects: the list of Coff objects to link.
    codemem: the allocator manager for the code memory.
    datamem: the allocator manager for the data memory.
    '''
    # Make three lists with the absolute sections, then with the sections that
    # must be allocated in the access ram and then with the relocatable ones
    absolute_sections = []
    access_sections = []
    relocatable_sections = []
    for o in objects:
        for s in o.sections[1:]:
            if s.isabsolute():
                absolute_sections.append((s, o))
            elif s.isaccess():
                access_sections.append((s, o))
            else:
                relocatable_sections.append((s, o))

    # Allocate absolute sections
    for s, o in absolute_sections:
        # Get the correct allocator
        allocator = _getallocator(o, s, codemem, datamem)
        if allocator.alloc(start=s.paddress, size=s.size) is None:
            if s.iscode(): typemem = 'program'
            else: typemem = 'data'
            error.errorf(o.filename,
                "No target memory available for section {b}'{s}'{re}".format(
                 b=error.BOLD, re=error.RESET, s=s.name))
    # Allocate access sections
    for s, o in access_sections:
        s.paddress = datamem.alloc(s.size, start=0, end=picinfo.access)
        if s.paddress is None:
            error.errorf(o.filename,
                "No target memory available for section {b}'{s}'{re}".format(
                 b=error.BOLD, re=error.RESET, s=s.name))
    # Allocate the relocatable sections
    for s, o in relocatable_sections:
        # Get the correct allocator
        allocator = _getallocator(o, s, codemem, datamem)
        s.paddress = allocator.alloc(s.size)
        if s.paddress is None:
            error.errorf(o.filename,
                "No target memory available for section {b}'{s}'{re}".format(
                 b=error.BOLD, re=error.RESET, s=s.name))
            s.paddress = 0

def _getexternals(objects):
    '''Compile a dictionary with all the external symbols.'''
    externals = {}
    symfiles = {}
    for o in objects:
        for s in o.symbols:
            if s.isexternal() and s.isdefined():
                if s.name in externals:
                    error.errorf(o.filename, "duplicate symbol {b}'{sym}'{re}"
                        " (first defined in {b}'{f}'{re})".format(b=error.BOLD,
                        re=error.RESET, sym=s.name, f=symfiles[s.name]))
                else:
                    externals[s.name] = s
                    symfiles[s.name] = o.filename
    return externals

def _applyrelocations(objects, externalsyms, picinfo):
    '''Patch the data of the code sections with the right addresses.'''
    # Hold a set of seen symbols to avoid repeating error messages
    undefset = set()
    noteseen = False
    # Compile the list of code sections
    code_sections = [(s, o) for o in objects for s in o.sections[1:]
        if s.iscode()]
    for s, o in code_sections:
        for r in s.relocations:
            # Get the value for patching
            symbol = r.symbol
            if not symbol.isdefined():
                # The symbol to use is an external symbol
                if symbol.name not in externalsyms:
                    # Report error only the first time
                    if symbol.name not in undefset:
                        error.errorfa(o.filename, s.name, r.address,
                            "undefined symbol {b}'{s}'{re}".format(
                            b=error.BOLD, re=error.RESET, s=symbol.name))
                        undefset.add(symbol.name)
                        if not noteseen:
                            error.notefa(o.filename, s.name, r.address,
                                'each undefined symbol is reported only once')
                            noteseen = True
                    continue
                symbol = externalsyms[symbol.name]
            value = symbol.value + r.offset
            if not symbol.section.isabsolute():
                value += symbol.section.paddress
            # The passed addr parameter must be the address of the first byte
            # of the current instruction. As addr is in fact the index of a
            # word, this value must be multiplied by two.
            context = _RelocationContext(
                o.filename, s, r.address, value, picinfo)
            s.data[r.address:r.address + 2] = struct.pack(
                '=H', _RELOCT_DICT[r.reltype](context))

def _buildhex(objects):
    '''Builds an HEX object with the binary data.'''
    ih = intelhex.IntelHex()
    for o in objects:
        for s in o.sections[1:]:
            if s.iscode() or s.isprogramdata():
                ih.puts(s.paddress, bytes(s.data))
    return ih

def link(objects):
    '''Link together several Coff objects to create a PIC program.

    objects: the list of Coff objects to link together.

    Precondition: objects has at least one element.
    '''
    # Check that all the objects are assembled for the same processor
    processor = objects[0].processor
    for o in objects[1:]:
        if o.processor != processor:
            error.warnf(o.filename, 'processor mismatch')

    # Load the configuration for the given Microcontroller
    picinfo = _loadpicinfo(processor)

    # Create memory allocator objects for data and code
    codemem = _MemoryAllocator(picinfo.progmem)
    datamem = _MemoryAllocator(picinfo.ram)

    _allocsections(objects, picinfo, codemem, datamem)
    # Get a dictionary with the external symbols
    externalsyms = _getexternals(objects)
    _applyrelocations(objects, externalsyms, picinfo)
    
    # Build the HEX object
    return _buildhex(objects)

