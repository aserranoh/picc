
'''Inspect Microchip's PIC objects in COFF format.

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

import datetime
import struct
from . import error

__author__ = 'Antonio Serrano Hernandez'
__copyright__ = 'Copyright (C) 2016 Antonio Serrano Hernandez'
__version__ = '0.2.1'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'

_BASE_TYPES = {0: 'T_NULL'}
_C_EXT = 2
_C_FILE = 103
_C_SECTION = 109
_DERIVED_TYPES = {0: 'DT_NON'}
_HDR_SIZE = 20
_LINENO_SIZE = 16
_MAGIC = 0x1240
_PROCESSORS = {
    0x2550: '18f2550',
    0xd616: '18f26j13',
}
_RELOC_SIZE = 12
_RELOC_TYPES = {
    1: 'RELOCT_CALL',
    2: 'RELOCT_GOTO',
    3: 'RELOCT_HIGH',
    4: 'RELOCT_LOW',
    5: 'RELOCT_P',
    6: 'RELOCT_BANKSEL',
    7: 'RELOCT_PAGESEL',
    8: 'RELOCT_ALL',
    9: 'RELOCT_IBANKSEL',
    10: 'RELOCT_F',
    11: 'RELOCT_TRIS',
    12: 'RELOCT_MOVLR',
    13: 'RELOCT_MOVLB',
    14: 'RELOCT_GOTO2/CALL2',
    15: 'RELOCT_FF1',
    16: 'RELOCT_FF2',
    17: 'RELOCT_LFSR1',
    18: 'RELOCT_LFSR2',
    19: 'RELOCT_BRA/RCALL',
    20: 'RELOCT_CONDBRA',
    21: 'RELOCT_UPPER',
    22: 'RELOCT_ACCESS',
    23: 'RELOCT_PAGESEL_WREG',
    24: 'RELOCT_PAGESEL_BITS',
    25: 'RELOCT_SCNSZ_LOW',
    26: 'RELOCT_SCNSZ_HIGH',
    27: 'RELOCT_SCNSZ_UPPER',
    28: 'RELOCT_SCNEND_LOW',
    29: 'RELOCT_SCNEND_HIGH',
    30: 'RELOCT_SCNEND_UPPER',
    31: 'RELOCT_SCNEND_LFSR1',
    32: 'RELOCT_SCNEND_LFSR2',
}
_SHDR_SIZE = 40
_STORAGE_CLASSES = {
    2: 'C_EXT',
    3: 'C_STAT',
    6: 'C_LABEL',
    103: 'C_FILE',
    107: 'C_EOF',
    108: 'C_LIST',
    109: 'C_SECTION',
}
_STYP_ABS       = 0x01000
_STYP_ACCESS    = 0x08000
_STYP_BSS       = 0x00080
_STYP_DATA_ROM  = 0x00100
_STYP_TEXT      = 0x00020
_STYP_FLAGS = [_STYP_TEXT, _STYP_BSS, _STYP_DATA_ROM, _STYP_ACCESS, _STYP_ABS]
_STYP_FLAGS_STR = {
    _STYP_TEXT:     '  Executable code.',
    _STYP_BSS:      '  Uninitialized data.',
    _STYP_DATA_ROM: '  Initialized data for ROM.',
    _STYP_ACCESS:   '  Available using access bit.',
    _STYP_ABS:      '  Absolute.'
}
_SYMENT_SIZE = 20

class Section(object):
    '''Represents a section in the COFF object file.'''

    def __init__(self, name, paddress, vaddress, flags):
        self.name = name
        self.paddress = paddress
        self.vaddress = vaddress
        self.flags = flags
        self.data = []
        self.relocations = []
        self.linenumbers = []

    def isabsolute(self):
        return self.flags & _STYP_ABS

    def iscode(self):
        return self.flags & _STYP_TEXT

    def isaccess(self):
        return self.flags & _STYP_ACCESS

    def isudata(self):
        return self.flags & _STYP_BSS

    def isprogramdata(self):
        return self.flags & _STYP_DATA_ROM

    @property
    def size(self):
        return self._size if hasattr(self, '_size') else len(self.data)

    @size.setter
    def size(self, value):
        self._size = value

    def __str__(self):
        # Build the header
        text = ['Section Header',
                '\nName                    ', self.name,
                '\nPhysical address        ', hex(self.paddress),
                '\nVirtual address         ', hex(self.vaddress),
                '\nSize of Section         ', str(self.size),
                '\nNumber of Relocations   ', str(len(self.relocations)),
                '\nNumber of Line Numbers  ', str(len(self.linenumbers)),
                '\nFlags                   ', hex(self.flags), '\n']
        for f in _STYP_FLAGS:
            if f & self.flags:
                text.append(_STYP_FLAGS_STR[f])
                text.append('\n')

        # Add the data if type text or program data
        index = 0
        if self.iscode():
            text.append('\nData\n')
            while index < len(self.data):
                text.append('{:06x}:  {:02x}{:02x}\n'.format(
                    index + self.paddress, self.data[index + 1],
                    self.data[index]))
                index += 2
        elif self.isprogramdata():
            text.append('\nData\n')
            for b in self.data:
                text.append('{:06x}:  {:04x}\n'.format(
                    index + self.paddress, b))
                index += 1

        # Add relocation and line number tables
        if len(self.relocations) > 0:
            text.append('\nRelocations Table\n')
            text.append(
                'Address    Offset     Type                      Symbol\n')
            for r in self.relocations:
                text.append(str(r))
                text.append('\n')
        if len(self.linenumbers) > 0:
            text.append('\nLine Number Table\n')
            text.append('Line     Address  Symbol\n')
            for l in self.linenumbers:
                text.append(str(l))
                text.append('\n')
        return ''.join(text)

class Relocation(object):
    '''Represents a relocation entry in the COFF file.'''

    def __init__(self, address, symbol, offset, reltype):
        self.address = address
        self.symbol = symbol
        self.offset = offset
        self.reltype = reltype

    def __str__(self):
        return '{:<#10x} {:<10} {:<#4x} {:20} {}'.format(self.address, self.offset,
            self.reltype, _RELOC_TYPES[self.reltype], self.symbol.name)

class Symbol(object):
    '''Represents a program's symbol.'''

    def __init__(self, name, value, section, base_type, derived_type,
                 storage_class):
        self.name = name
        self.value = value
        self.section = section
        self.base_type = base_type
        self.derived_type = derived_type
        self.storage_class = storage_class
        self.auxsymbols = []

    def addauxsymbol(self, auxsymbol):
        self.auxsymbols.append(auxsymbol)

    def isexternal(self):
        return self.storage_class == _C_EXT

    def isdefined(self):
        return isinstance(self.section, Section)

    def __str__(self):
        if type(self.section) == int:
            if self.section < 0:
                section = 'DEBUG'
            elif self.section == 0:
                section = 'UNDEFINED'
        else:
            section = self.section.name
        return '{:24} {!s:16} {:<#10x} {:8} {:12} {:9} {}'.format(
            self.name, section, self.value, _BASE_TYPES[self.base_type],
            _DERIVED_TYPES[self.derived_type],
            _STORAGE_CLASSES[self.storage_class], len(self.auxsymbols))

class FileAuxSymbol(object):
    '''Represents additional information for a symbol of type C_FILE.'''

    def __init__(self, filename, incline, flags):
        self.filename = filename
        self.incline = incline
        self.flags = flags

    def isexternal(self):
        return False

    def __str__(self):
        return ('      file = {}\n'
                '      line included = {}\n'
                '      flags = {}').format(self.filename, self.incline,
                    self.flags)

class SectionAuxSymbol(object):
    '''Represents additional information for a symbol of type C_SECTION.'''

    def __init__(self, sectionlen, numreloc, numlinenumbers):
        self.sectionlen = sectionlen
        self.numreloc = numreloc
        self.numlinenumbers = numlinenumbers

    def isexternal(self):
        return False

    def __str__(self):
        return('      length = {}\n'
               '      number of relocations = {}\n'
               '      number of line numbers = {}').format(self.sectionlen,
                   self.numreloc, self.numlinenumbers)

class LineNumber(object):
    '''Represents a Line Number entry in a COFF file.'''

    def __init__(self, srcsymbol, linenumber, paddr, flags, fcnsymbol):
        self.srcsymbol = srcsymbol
        self.linenumber = linenumber
        self.paddr = paddr
        self.flags = flags
        self.fcnsymbol = fcnsymbol

    def __str__(self):
        return '{:<8d} {:<#8x} {}'.format(self.linenumber, self.paddr,
            self.srcsymbol.auxsymbols[0].filename)

class Coff(object):
    '''Represents a COFF object in the Microchip format.'''

    def __init__(self, filename, timestamp, flags, magic=None, version=None,
                 processor=None, rom_width=None, ram_width=None):
        '''Initialize this object with some values from the headers.'''
        self.filename = filename
        self.timestamp = timestamp
        self.flags = flags
        self.magic = magic
        self.version = version
        self.processor = processor
        self.rom_width = rom_width
        self.ram_width = ram_width
        # Initialize other fields
        self.strtable = None
        self.symbols = []
        self.sections = [None]

    def getstrfromoffset(self, offset):
        '''Returns a string from the string table pointed by offset.'''
        # Substract 4 from the offset. This is because the offset includes the
        # 4 bytes of the strtable len, at the beginning of the string table.
        # However, this field has been stripped in the Coff object
        offset -= 4
        end = offset
        if offset >= len(self.strtable):
            raise Exception('string table offset passed the end')
        while self.strtable[end] != '\0':
            end += 1
        return self.strtable[offset:end]

    def getstring(self, stroffset):
        '''Returns a string according to the parameter stroffset.
        
        If the first 4 characters of stroffset are the character 0, that
        parameter is interpreted as a long value pointing to the string table.
        Otherwise, stroffset is the proper string.
        '''
        zeroes, offset = struct.unpack('=LL', stroffset)
        if not zeroes:
            s = self.getstrfromoffset(offset)
        else:
            s = stroffset.decode('ascii').rstrip('\0')
        return s

    def addsymbol(self, symbol):
        '''Adds a new symbol to the symbols table.'''
        self.symbols.append(symbol)

    def addsection(self, section):
        self.sections.append(section)

    def __str__(self):
        # Add the header
        text = ['COFF File and Optional Headers',
                '\nCOFF version         ', hex(_MAGIC),
                '\nProcessor Type       ', self.processor,
                '\nTime Stamp           ', self.timestamp.strftime('%c'),
                # The null section must be substracted from the total number
                '\nNumber of Sections   ', str(len(self.sections) - 1),
                '\nNumber of Symbols    ', str(len(self.symbols)),
                '\nCharacteristics      ', str(self.flags), '\n', '\n']

        # Add the sections
        for s in self.sections[1:]:
            text.append(str(s))
            text.append('\n')

        # Add the symbols table
        text.append('Symbol Table')
        text.append(('\nIdx  Name                     Section          '
                     'Value      Type     DT           Class     NumAux\n'))
        index = 1
        for s in self.symbols:
            if isinstance(s, Symbol):
                text.append('{:04} {}\n'.format(index, str(s)))
            else:
                text.append(str(s))
                text.append('\n')
            index += 1
        return ''.join(text)

def _readstrtable(obj, stream, offset):
    '''Read the string table, located at the end of the COFF file.

    obj: the Coff object.
    stream: the opened file that points to the COFF file.
    offset: the offset inside that file where the string table starts.
    '''
    # Save the current file pointer
    cur = stream.tell()
    # Go to the string table and read it
    stream.seek(offset)
    # Read the size of the table
    try:
        size, = struct.unpack('=l', stream.read(4))
        size -= 4
        obj.strtable = stream.read(size).decode('ascii')
    except struct.error:
        error.fatalf(obj.filename, 'truncated string table size')
    except UnicodeDecodeError:
        error.fatalf(obj.filename, 'non ASCII characters in string table')

    if len(obj.strtable) != size:
        error.fatalf(obj.filename, 'truncated string table')
    if obj.strtable[-1] != '\0':
        error.fatalf(obj.filename,
            'last character of string table is not NULL')
    # Restore the original file pointer
    stream.seek(cur)

def _readsymtable(obj, stream, offset, num):
    '''Read the symbols table.
    
    obj: the Coff objet being built.
    stream: the opened file that points to the COFF file.
    offset: the offset inside that file where the symbols table starts.
    num: the number of symbols in the symbols table.
    '''
    # Save the current file pointer
    cur = stream.tell()
    # Go to the symbols table and read each entry
    stream.seek(offset)
    entry = 0
    try:
        while entry < num:
            (_n, n_value, n_scnum, n_btype, n_dtype, n_sclass, n_numaux
                ) = struct.unpack('=8sLhHHbb', stream.read(_SYMENT_SIZE))
            # Get the proper name of the symbol (maybe the string table must be
            # checked)
            name = obj.getstring(_n)

            # Create the symbol entry
            s = Symbol(name, n_value, n_scnum, n_btype, n_dtype, n_sclass)
            obj.addsymbol(s)
            # Read the aux symbols
            entry += 1
            for i in range(n_numaux):
                if n_sclass == _C_FILE:
                    x_offset, x_incline, x_flags = struct.unpack('=LLB11x',
                        stream.read(_SYMENT_SIZE))
                    filename = obj.getstrfromoffset(x_offset)
                    auxs = FileAuxSymbol(filename, x_incline, x_flags)
                elif n_sclass == _C_SECTION:
                    x_scnlen, x_nreloc, x_nlinno = struct.unpack('=LHH12x',
                        stream.read(_SYMENT_SIZE))
                    auxs = SectionAuxSymbol(x_scnlen, x_nreloc, x_nlinno)
                s.addauxsymbol(auxs)
                obj.addsymbol(auxs)
                entry += 1
        # Restore the original file pointer
        stream.seek(cur)
    except struct.error:
        error.fatalf(obj.filename,
            'truncated symbol at position {}'.format(entry))
    except UnicodeDecodeError:
        error.fatalf(obj.filename, 'in symbol at position {}: non ASCII '
            'characters in symbol name'.format(entry))
    except Exception as e:
        error.fatalf(obj.filename, 'in symbol at position {}: {}'.format(
            entry, e))

def _readreloc(obj, section, stream, ptr, num):
    '''Read the relocation table for a section.

    obj: the parent Coff object.
    section: current section being read.
    stream: the file stream from where the data is read.
    ptr: the absolute offset in the coff file where the table begins.
    num: number of realocation entries.
    '''
    stream.seek(ptr)
    try:
        reloc_num = 0
        for i in range(num):
            (r_vaddr, r_symndx, r_offset, r_type
                ) = struct.unpack('=LLhH', stream.read(_RELOC_SIZE))
            symbol = obj.symbols[r_symndx]
            section.relocations.append(
                Relocation(r_vaddr, symbol, r_offset, r_type))
            reloc_num += 1
    except struct.error:
        error.fatalf(obj.filename, "in section {b}'{name}'{re}: truncated "
            "relocation info at position {pos}".format(
            b=error.BOLD, re=error.RESET, name=section.name, pos=reloc_num))
    except IndexError:
        error.fatalf(obj.filename,
            "in section {b}'{name}'{re}: relocation info at position {pos} "
            "points to nonexistent symbol with index {idx}".format(
            b=error.BOLD, re=error.RESET, name=section.name, pos=reloc_num,
            idx=r_symndx))

def _readlinenumbers(obj, section, stream, ptr, num):
    '''Read the line numbers table for a section.

    obj: the parent Coff object.
    section: current section being read.
    stream: the file stream from where the data is read.
    ptr: the absolute offset in the coff file where the table begins.
    num: number of line numbers entries.
    '''
    stream.seek(ptr)
    try:
        linenum_count = 0
        for i in range(num):
            (l_srcndx, l_lnno, l_paddr, l_flags, l_fcnndx
                ) = struct.unpack('=LHLHL', stream.read(_LINENO_SIZE))
            # This is just for error handling purposes
            symindex = l_srcndx
            src_symbol = obj.symbols[l_srcndx]
            # This is just for error handling purposes
            symindex = l_fcnndx
            fcn_symbol = obj.symbols[l_fcnndx]
            section.linenumbers.append(
                LineNumber(src_symbol, l_lnno, l_paddr, l_flags, fcn_symbol))
            linenum_count += 1
    except struct.error:
        error.fatalf(obj.filename, "in section {b}'{name}'{re}: truncated line"
            " number info at position {pos}".format(b=error.BOLD,
            re=error.RESET, name=section.name, pos=linenum_count))
    except IndexError:
        error.fatalf(obj.filename, "in section {b}'{name}'{re}: line number "
            "info at position {pos} points to nonexistent symbol with index "
            "{idx}".format(b=error.BOLD, re=error.RESET, name=section.name,
            pos=linenum_count, idx=symindex))

def readcoff(stream):
    '''Read the contents of a COFF file.

    stream: from where the COFF file is read.
    Return a Coff object with the contents of the COFF file.
    '''
    filename = stream.name
    try:
        # Read filehdr
        where = 'header'
        (f_magic, f_nscns, f_timdat, f_symptr, f_nsyms, f_opthdr, f_flags
            ) = struct.unpack('=HHLLLHH', stream.read(_HDR_SIZE))

        # Check that it's a COFF file
        if f_magic != _MAGIC:
            error.fatalf(filename, 'not a Microchip COFF file')
        timestamp = datetime.datetime.fromtimestamp(f_timdat)
    
        # Read optional header, if any
        if f_opthdr:
            where = 'optional header'
            (magic, vstamp, proc_type, rom_width_bits, ram_width_bits
                ) = struct.unpack('=HH2xHLL2x', stream.read(f_opthdr))
            obj = Coff(filename, timestamp, f_flags, magic, vstamp,
                _PROCESSORS[proc_type], rom_width_bits, ram_width_bits)
        else:
            obj = Coff(filename, timestamp, f_flags)

        # Read the strings table
        _readstrtable(obj, stream, f_symptr + _SYMENT_SIZE * f_nsyms)

        # Read the symbols table
        _readsymtable(obj, stream, f_symptr, f_nsyms)

        # Read the sections
        section_num = 0
        for i in range(f_nscns):
            where = 'section header at position {}'.format(section_num)
            (_s_name, s_paddr, s_vaddr, s_size, s_scnptr, s_relptr, s_lnnoptr,
                s_nreloc, s_nlnno, s_flags
                ) = struct.unpack('=8sLLLLLLHHL', stream.read(_SHDR_SIZE))
            name = obj.getstring(_s_name)
            section = Section(name, s_paddr, s_vaddr, s_flags)
            # For the code sections, check that the size of the data is even
            if section.iscode() and s_size % 2 != 0:
                error.fatalf(filename, "in section {b}'{name}'{re}: code "
                    "section data size must be multiple of 2".format(
                    b=error.BOLD, re=error.RESET, name=name))
            # For the udata section, set size attribure. For the others, read
            # the raw data
            if section.isudata():
                section.size = s_size
            elif section.iscode() or section.isprogramdata():
                cur = stream.tell()
                stream.seek(s_scnptr)
                where = 'data from section {}'.format(name)
                section.data = bytearray(stream.read(s_size))
                # Read the relocation table for this section
                _readreloc(obj, section, stream, s_relptr, s_nreloc)
                # Read the line numbers table for this section
                _readlinenumbers(obj, section, stream, s_lnnoptr, s_nlnno)
                # Restore the file pointer
                stream.seek(cur)
            else:
                error.fatalf(filename, "in section {b}'{name}'{re}: "
                    "unimplemented section type".format(
                    b=error.BOLD, re=error.RESET, name=name))
            obj.addsection(section)
            section_num += 1

        # Patch the names of the sections in the symbols table
        symbol_num = 0
        for s in obj.symbols:
            if isinstance(s, Symbol) and s.section > 0:
                # May throw IndexError
                s.section = obj.sections[s.section]
            symbol_num += 1
        return obj
    except struct.error:
        error.fatalf(filename, 'truncated {}'.format(where))
    except UnicodeDecodeError:
        error.fatalf(filename, 'in section at position {}: non ASCII '
            'characters in section name'.format(section_num))
    except IndexError:
        error.fatalf(filename, "in symbol '{b}'{name}'{re}': points to "
            "nonexistent section with index {idx}".format(
            b=error.BOLD, re=error.RESET, name=s.name, idx=s.section))
    except Exception as e:
        error.fatalf(filename, 'in section at position {}: {}'.format(
            section_num, e))

