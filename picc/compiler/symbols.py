
import types

class UndeclaredError(Exception): pass

# Constants to identify the type of symbols
SYMBOL, ENUMERATOR = range(2)

class BaseSymbol(object):
    def __init__(self, name, coord):
        self.name = name
        self.coord = coord

class Symbol(BaseSymbol):
    '''A symbol of the program.'''
    symtype = SYMBOL
    def __init__(self, name=None, type_=None, coord=None):
        BaseSymbol.__init__(self, name, coord)
        self.type = type_

class EnumeratorSymbol(BaseSymbol):
    symtype = ENUMERATOR
    '''An enumerator constant.'''
    def __init__(self, name, value, coord):
        BaseSymbol.__init__(self, name, coord)
        self.value = value

class StructSymbol(Symbol):
    '''A declaration in a struct.'''
    def __init__(self, name, type_, bitsize, coord):
        Symbol.__init__(self, name, type_, coord)
        self.bitsize = bitsize

class FuncParamSymbol(Symbol): pass

class Symtable(object):
    def __init__(self):
        self._top = {}
        self._stack = [self._top]
    def __getitem__(self, name):
        for table in reversed(self._stack):
            try:
                return table[name]
            except: continue
        raise KeyError(name)
    def add(self, symbol):
        self._top[symbol.name] = symbol
    def defined(self, name):
        try:
            return self._top[name]
        except:
            raise UndeclaredError()
    def push(self):
        '''Push a new symtable to the top of the stack.'''
        self._top = {}
        self._stack.append(self._top)
    def pop(self):
        '''Remove the symtable in the top of the stack.'''
        self._stack.pop()
        self._top = self._stack[-1]

