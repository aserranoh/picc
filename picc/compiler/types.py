
import sys
import symbols

# Constants to identify the types
(ARRAY, ENUM, FUNCTION, INT, POINTER, STRUCT, VOID) = range(7)

class RedeclarationError(Exception): pass

class Type(object):
    incomplete = False

class IntType(Type):
    type = INT
    def __init__(self, size=1, signed=True):
        self.size = size
        self.signed = signed
        if signed:
            self.min = -2**(size * 8 - 1)
            self.max = 2**(size * 8 - 1) - 1
        else:
            self.min = 0
            self.max = 2**(size * 8) - 1

class VoidType(Type):
    type = VOID

class ArrayType(Type):
    type = ARRAY
    def __init__(self, base_type, dim):
        self.base_type = base_type
        self.dim = dim
    def __hash__(self):
        return hash((ARRAY, self.base_type, self.dim))
    def __eq__(self, other):
        try:
            return (self.type == other.type
                and self.pointed_type == other.pointed_type)
        except AttributeError:
            return NotImplemented

class EnumType(Type):
    type = ENUM
    seq = 0
    def __init__(self, name, coord):
        # The name of the enum. If the name is None, make sure to pick a
        # unique one
        self.name = name
        if name is None:
            self.name = '.{}'.format(EnumType.seq)
            EnumType.seq += 1
        self.coord = coord
        self._nextvalue = 0
        self.defined = False
        self.incomplete = True
    def __hash__(self):
        return hash((self.type, self.name))
    def __eq__(self, other):
        try:
            return self.type == other.type and self.name == other.name
        except AttributeError:
            return NotImplemented
    def __str__(self):
        return 'enum {}'.format(self.name)
    def nextvalue(self):
        val = self._nextvalue
        self._nextvalue += 1
        self.defined = True
        return val
    def newvalue(self, value):
        self._nextvalue = value + 1
        self.defined = True
    def add(self, enumerator):
        self.enumerators.append(enumerator)
        self._nextvalue = enumerator.value + 1

class FunctionType(Type):
    type = FUNCTION
    def __init__(self, result, params=[]):
        # The result type
        self.result = result
        # The list of params
        self.params = params
    def __hash__(self):
        return hash((FUNCTION, self.result) + tuple(self.params))
    def __eq__(self, other):
        try:
            return (self.type == other.type
                and self.result == other.result
                and self.params == other.params)
        except AttributeError:
            return NotImplemented

class PointerType(Type):
    type = POINTER
    def __init__(self, pointed_type):
        self.pointed_type = pointed_type
    def __hash__(self):
        return hash((POINTER, self.pointed_type))
    def __eq__(self, other):
        try:
            return (self.type == other.type
                and self.pointed_type == other.pointed_type)
        except AttributeError:
            return NotImplemented

class StructType(Type):
    type = STRUCT
    seq = 0
    def __init__(self, name, coord):
        # The name of the struct. If the name is None, make sure to pick a
        # unique one
        if name is None:
            self.name = '.{}'.format(StructType.seq)
            StructType.seq += 1
            self._isanonymous = True
        else:
            self.name = name
            self._isanonymous = False
        # A list and a dictionary with the fields
        self.fields = []
        self._dict_fields = {}
        self.defined = False
        self.coord = coord
        self.incomplete = True
    def __getitem__(self, field):
        return self._dict_fields[field]
    def __hash__(self):
        return hash((STRUCT, self.name))
    def __eq__(self, other):
        try:
            return self.type == other.type and self.name == other.name
        except AttributeError:
            return NotImplemented
    def __iter__(self):
        return iter(self.fields)
    def __str__(self):
        return 'struct {}'.format(self.name)
    def add(self, field):
        '''Add a field to the struct.
        If a field with the same name is already in the struct, raise an
        exception.
        '''
        self.defined = True
        if field.name is not None:
            if field.name in self._dict_fields:
                raise RedeclarationError()
            self.fields.append(field)
            self._dict_fields[field.name] = field
    def isanonymous(self):
        return self._isanonymous

# Instances of the basic types
char = IntType()
uchar = IntType(signed=False)
sys.modules[__name__].int = IntType()
sys.modules[__name__].long = IntType(size=2)
llong = IntType(size=4)
uint = IntType(signed=False)
ulong = IntType(size=2, signed=False)
ullong = IntType(size=4, signed=False)
void = VoidType()

class TypeGrab(object):
    '''Wrapper of Type used to retreive an instance of a set of types.'''
    def __init__(self, t):
        self.t = t
    def __hash__(self):
        return hash(self.t)
    def __eq__(self, other):
        if self.t == other:
            self.t = other
            return True
        return False

class TypesPool(object):
    def __init__(self):
        self.types = set()
        self.top = set()
        self.stack = [self.top]
    def add(self, t):
        '''Insert the type t in the pool of types.
        For the basic types and the function, pointer and array, if an equal
        type is already in the pool, that type is returned and t is not
        inserted. Otherwise, t is inserted and returned.
        For the structs and enums, they are inserted in the stack to keep track
        of the definition scopes. They are inserted even if another type with
        the same name is already defined. The type itself is returned.
        '''
        if t.type == STRUCT or t.type == ENUM:
            self.top.add(t)
        else:
            grab = TypeGrab(t)
            if grab in self.types:
                t = grab.t
            else:
                self.types.add(t)
        return t
    def defined(self, t):
        '''Check if a struct or enum with the same name is already defined.'''
        outtype = None
        grab = TypeGrab(t)
        if grab in self.top and grab.t.defined:
            outtype = grab.t
        return outtype
    def push(self):
        '''Push a new types scope to the top of the stack.'''
        self.top = {}
        self.stack.append(self.top)
    def pop(self):
        '''Remove the types scope in the top of the stack.'''
        self.stack.pop()
        self.top = self.stack[-1]

