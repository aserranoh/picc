
import inspect
import pycparser.c_ast as c_ast
import re
import symbols
import types

# Declares constants for the type_specifiers.
# They are used to speed up comparisons between type_specifiers.
# The first three are char, int and void (are types strictly speaking), this
# way checking if a type_specifier ts is a type suffices doing ts <= VOID.
CHAR, INT, VOID, LONG, SHORT, SIGNED, UNSIGNED = range(7)

# Map the names of the type_specifiers to their constans
TYPE_SPECIFIERS_FROMSTR = {
    'char': CHAR,
    'int': INT,
    'void': VOID,
    'long': LONG,
    'short': SHORT,
    'signed': SIGNED,
    'unsigned': UNSIGNED,
}

# Matrix of incompatible type_specifiers in a declaration.
# The list is indexed by the type_specifiers constants. Each position contains
# a list with the incompatible type_specifiers with a given type_specifier.
TYPE_SPECIFIERS_COLLISIONS = [
    [VOID, CHAR, INT, SHORT, LONG],                   # CHAR
    [VOID, CHAR, INT],                                # INT
    [VOID, INT, CHAR, SHORT, LONG, SIGNED, UNSIGNED], # VOID
    [VOID, CHAR, SHORT],                              # LONG
    [VOID, CHAR, SHORT, LONG],                        # SHORT
    [VOID, UNSIGNED, SIGNED],                         # SIGNED
    [VOID, UNSIGNED, SIGNED],                         # UNSIGNED
]

# List that contains the string representation of each type_specifier
# (the type_specifiers are the indexes of the list).
TYPE_SPECIFIERS_TOSTR = [
    'char', 'int', 'void', 'long', 'short', 'signed', 'unsigned']

# Regular expression to parse integer constants
RE_INTCONST = re.compile(r'''
    (?P<value>
        (?P<dec> [1-9]) [0-9]*
        | (?P<oct> 0) [0-7]*
        | (?P<hex> 0[xX]) [0-9a-fA-F]+)
    (?P<suffix> [uUlL]*) $
    ''', re.X)

OPADDR = range(1)

OPERATORS = {
    '&': OPADDR,
}

# Dictionary used to generate ConstantExpression objects form operators
CONSTANT_EXPR = {
    '-': lambda e: ConstantExpression(value=-e.value, expr_type=e.expr_type)
}

def generate_accept_method(cls):
    '''Generate the accept method for a given class.'''
    visit_method_name = 'visit_{}'.format(cls.__name__.lower())
    return lambda self, visitor: getattr(visitor, visit_method_name)(self)

# Make all the nodes in c_ast acceptors
for name, cls in inspect.getmembers(c_ast, inspect.isclass):
    cls.accept = generate_accept_method(cls)

class Expression(object):
    def isconstant(self):
        return False

class ArrayRefExpression(c_ast.ArrayRef, Expression):
    def __init__(self, name, subscript, coord):
        c_ast.ArrayRef(name, subscript, coord)
        # INVARIANT: name.expr_type is PointerType
        self.expr_type = name.expr_type.pointed_type

class AssignmentExpression(c_ast.Assignment, Expression):
    def __init__(self, op, lvalue, rvalue, coord):
        c_ast.Assignment(op, lvalue, rvalue, coord)
        self.expr_type = lvalue.expr_type

class ConstantExpression(c_ast.Constant, Expression):
    def __init__(self, type_=None, value=None, symbol=None, expr_type=None,
                 coord=None):
        c_ast.Constant.__init__(self, type_, value, coord)
        self.symbol = symbol
        self.expr_type = expr_type
    def isconstant(self):
        return True

class IDExpression(c_ast.ID, Expression):
    def __init__(self, name, coord):
        c_ast.ID.__init__(self, name, coord)
        self.expr_type = name.type

class StructRefExpression(c_ast.StructRef, Expression):
    def __init__(self, name, type_, field, coord):
        c_ast.StructRef(name, type_, field, coord)
        self.expr_type = name.expr_type[field.name]

class ASTVisitor(object): pass

class DeclarationVisitor(ASTVisitor):
    '''Visit the declarations in the Abstract Syntax Tree.
    Fill the symbol tables and the pool of types.
    '''
    def __init__(self, symtable, typespool, expression_visitor, err):
        self.symtable = symtable
        self.typespool = typespool
        # The last symbol declared in this visitor
        self.symbol = None
        # The last type declared in this visitor
        self.type = None
        # Visitor for expressions that may appear in declarations
        self.ev = expression_visitor
        # Objet to report errors
        self.err = err
        # Flag that tells if we are declaring a struct
        self.struct_scope = False
        # Flag that tells if we are declaring a function
        self.funcdec_scope = False
    def visit_arraydecl(self, o):
        '''Declare an array type.'''
        o.type.accept(self)
        size = None
        # o.dim may be None, if the array is abstract
        if o.dim is not None:
            o.dim.accept(self.ev)
            e = self.ev.expression
            # Check that the expression for the size of the array is constant
            if not e.isconstant():
                self.err.error("variably modified #'{}'$ at file scope".format(
                    self.declname), o.coord)
            # Check that the size of the array is 0 < size < ulong.max
            elif e.value <= 0:
                self.err.error("size of array #'{}'$ is {}".format(self.declname,
                    'negative' if e.value < 0 else 'zero'), o.coord)
            elif e.value > types.long.max:
                self.err.error("size of array #'{}'$ is too large".format(
                    self.declname), o.coord)
            else:
                size = e.value
        self.type = self.typespool.add(types.ArrayType(self.type, size))
    def visit_decl(self, o):
        '''Declaration of a new symbol.'''
        # Keep the decl name for use in the error messages
        self.declname = o.name
        # Process the symbol's type
        o.type.accept(self)
        # Check the type of delcaration we are dealing with
        if self.struct_scope:
            # Obtain the bitsize if any
            bitsize = None
            if o.bitsize is not None:
                o.bitsize.accept(self.ev)
                e = self.ev.expression
                # Get the name and the coords, in case is an anonymous field
                if o.name is None:
                    name, coord = '<anonymous>', o.bitsize.coord
                else:
                    name, coord = o.name, o.coord
                if e.isconstant():
                    if e.value < 0:
                        self.err.error("negative width in bit-field"
                            " #'{}'$".format(name), coord)
                    elif not e.value and o.name is not None:
                        self.err.error("zero width for bit-field "
                            "#'{}'$".format(name), coord)
                    elif e.value > types.int.size * 8:
                        self.err.error("width of #'{}'$ exceeds its "
                            "type".format(name), coord)
                    else:
                        bitsize = e.value
                else:
                    self.err.error("bit-field #'{}'$ width not an integer "
                        "constant".format(name), coord)
                # Check if the type for the bitfield is acceptable
                if self.type.type != types.INT:
                    # TODO: allow enums but check that all the enums fit in the
                    # width of the bitfield
                    self.err.error("bit-field #'{}'$ has invalid type".format(
                        name), coord)
            self.symbol = symbols.StructSymbol(
                o.name, self.type, bitsize, o.coord)
        elif self.funcdec_scope:
            self.symbol = symbols.FuncParamSymbol(o.name, coord=o.coord)
        else:
            self.symbol = symbols.Symbol(o.name, self.type, o.coord)
            self.symtable.add(self.symbol)
    def _define_enum_or_struct(self, type_, define, coord):
        '''Try to insert an enum or struct to the pool of types.
        The enum or struct are not inserted in the pool of types if we are
        not defining it (only declaring it) and there's already a definition
        of this enum/struct in the pool.
        '''
        # Search a possible enum/struct already defined
        t = self.typespool.defined(type_)
        # Give an error if we are defining it and is already defined
        if t is not None:
            if not define:
                type_ = t
            else:
                self.err.error("redefinition of #'{}'$".format(str(t)), coord)
                self.err.note('originally defined here', t.coord)
                self.typespool.add(type_)
        else:
            self.typespool.add(type_)
        return type_
    def visit_enum(self, o):
        '''Declare an enum type.'''
        # Create the type
        enum = types.EnumType(o.name, o.coord)
        # Try to insert the enum in the pool of types
        enum = self._define_enum_or_struct(enum, o.values is not None, o.coord)
        self.type = enum
        # Visit the enumerators
        if o.values is not None:
            o.values.accept(self)
            enum.incomplete = False
    def visit_enumerator(self, o):
        '''Declare an enumerator constant.'''
        # Error if a symbol with the same name exists
        try:
            s = self.symtable.defined(o.name)
            if s.symtype == symbols.ENUMERATOR:
                self.err.error("redeclaration of enumerator #'{}'$".format(
                    o.name), o.coord)
            else:
                self.err.error(
                    "#'{}'$ redeclared as different kind of symbol".format(
                    o.name), o.coord)
            self.err.note("previous declaration of #'{}'$ was here".format(
                o.name), s.coord)
        except symbols.UndeclaredError: pass
        # Compute the value of the enumerator
        if o.value is None:
            value = self.type.nextvalue()
        else:
            o.value.accept(self.ev)
            e = self.ev.expression
            value = 0
            if e is not None:
                # The expression with the enumerator value must be constant
                if e.isconstant():
                    value = e.value
                    self.type.newvalue(value)
                else:
                    self.err.error("enumerator value for #'{}'$ is not an "
                        "integer constant".format(o.name), o.coord)
        # Create the enumerator and add it to the symtable
        s = symbols.EnumeratorSymbol(o.name, value, o.coord)
        self.symtable.add(s)
    def visit_enumeratorlist(self, o):
        for e in o.enumerators:
            e.accept(self)
    def visit_funcdecl(self, o):
        '''Declare a function type.'''
        # Visit the function's result type
        o.type.accept(self)
        restype = self.type
        # Visit the params
        if o.args is not None:
            o.args.accept(self)
            f = types.FunctionType(self.type, self.params)
        else:
            f = types.FunctionType(self.type)
        self.type = self.typespool.add(f)
    def visit_id(self, o):
        self.symbol = symbols.FuncParamSymbol(o.name, coord=o.coord)
    def _type_specifier_collisions(self, ts, reflist, coord):
        '''Check for incompatible type_specifiers.
        ts: the type_specifier.
        reflist: the list of type_specifiers where to look for
                 incompatibilities.
        coord: the position of ts in the code (for the error messages).
        '''
        for t in reflist:
            if t in TYPE_SPECIFIERS_COLLISIONS[ts]:
                # t with ts collide. Show an error message:
                # 1) Both are types
                if ts <= VOID and t <= VOID:
                    self.err.error('two or more data types in declaration '
                        'specifiers', coord)
                # 2) Both aren't types but they're the same
                elif ts == t:
                    self.err.error("duplicate '#{}$'".format(
                        TYPE_SPECIFIERS_TOSTR[t]), coord)
                # 3) Not types and different
                else:
                    self.err.error("both '#{}$' and '#{}$' in declaration "
                        "specifiers".format(TYPE_SPECIFIERS_TOSTR[t],
                        TYPE_SPECIFIERS_TOSTR[ts]), coord)
                # Exit after the first collision
                break
    def visit_identifiertype(self, o):
        '''Declaration of a type from a list of type_specifiers.'''
        type_ = None
        sign = UNSIGNED
        short = False
        long_ = 0
        # Get the type_specifiers identifiers, to speed up comparisons
        type_specifiers = [TYPE_SPECIFIERS_FROMSTR[name] for name in o.names]
        for i, ts in enumerate(type_specifiers):
            # Check for errors
            self._type_specifier_collisions(ts, type_specifiers[:i], o.coord)
            # Update the data to generate the type
            if ts == SIGNED or ts == UNSIGNED: sign = ts
            elif ts == LONG:
                if long_ > 1:
                    self.err.error("#'long long long'$ is too long for PICC",
                        o.coord)
                else: long_ += 1
            elif ts == SHORT: short = True
            elif ts == CHAR: type_ = types.int
            elif ts == VOID: type_ = types.void
            else: type_ = types.int
        # Build the int type
        if type_ is None or type_ == types.int:
            if long_ == 1:
                type_ = types.long if sign == SIGNED else types.ulong
            elif long_ == 2:
                type_ = (types.long if sign == SIGNED else types.ullong)
            else:
                type_ = types.int if sign == SIGNED else types.uint
        self.type = type_
    def visit_paramlist(self, o):
        '''Process de declarations of the parameters of a function.'''
        # Change to function declaration scope
        self.funcdec_scope = True
        # Visit the parameters
        self.params = []
        for p in o.params:
            p.accept(self)
            self.params.append(self.symbol)
        # Change back to normal scope
        self.funcdec_scope = False
    def visit_ptrdecl(self, o):
        '''Declare a pointer to some type.'''
        # Visit the pointed type
        o.type.accept(self)
        # Create a pointer to this pointed type
        self.type = self.typespool.add(types.PointerType(self.type))
    def _add_field(self, struct, field):
        '''Add the given field to the given struct.
        Show an error if a field with the same name is already declared.'''
        try:
            struct.add(field)
        except types.RedeclarationError:
            self.err.error("duplicate member #'{}'$".format(field.name),
                field.coord)
    def visit_struct(self, o):
        '''Add the struct to the pool of types.'''
        # Create the type struct
        struct = types.StructType(o.name, o.coord)
        # Try to insert the struct in the pool of types
        struct = self._define_enum_or_struct(struct, o.decls is not None,
            o.coord)
        # Process the declarations in the struct
        if o.decls is not None:
            # Switch to struct scope
            self.struct_scope = True
            for d in o.decls:
                d.accept(self)
                # Error if field of an incomplete type
                if self.type.incomplete:
                    self.err.error("field #'{}'$ has incomplete type".format(
                        self.symbol.name), d.coord)
                # TODO: error if field of type function
                # For the anonymous members that are of type anonymous struct,
                # include all the nested struct's fields into this one
                elif (self.type.type == types.STRUCT
                        and self.type.isanonymous()
                        and self.symbol.name is None):
                    for field in self.type:
                        self._add_field(struct, field)
                else:
                    self._add_field(struct, d)
            # Switch back to declaration scope
            self.struct_scope = False
            struct.incomplete = False
        self.type = struct
    def visit_typedecl(self, o):
        o.type.accept(self)
    def visit_typename(self, o):
        '''Type used in a function declaration (without identifier).'''
        o.type.accept(self)
        self.symbol = symbols.FuncParamSymbol(type_=self.type, coord=o.coord)
    def visit_union(self, o):
        self.visit_struct(o)

class ExpressionVisitor(ASTVisitor):
    '''Visit the expressions in the Abstract Syntax Tree.
    Obtain the type of each expression and simplifies the constant ones.
    '''
    def __init__(self, symtable, typespool, err):
        self.symtable = symtable
        self.typespool = typespool
        # Holds the last expression analysed
        self.expression = None
        # For error reporting
        self.err = err
    def visit_arrayref(self, o):
        o.name.accept(self)
        base = self.expression
        o.subscript.accept(self)
        self.expression = ArrayRefExpression(base, self.expression, o.coord)
    def visit_assignment(self, o):
        o.lvalue.accept(self)
        lv = self.expression
        o.rvalue.accept(self)
        rv = self.expression
        self.expression = AssignmentExpression(o.op, lv, rv, o.coord)
    def visit_compound(self, o):
        for i in o.block_items:
            i.accept(self)
    def visit_constant(self, o):
        '''Check the value of the constant and stablish its type.'''
        # Find the value and the suffix
        m = RE_INTCONST.match(o.value)
        o.value = int(m.group('value'), base=0)
        suffix = m.group('suffix').lower()
        # Check that the constant value is supported for the architecture
        if o.value > types.ullong.max:
            self.err.warn('integer constant is too large for its type',
                o.coord)
        # Compute the constant type
        if not suffix:
            if m.group('dec') is not None:
                ltypes = [types.int, types.long, types.llong, types.ullong]
            else:
                ltypes = [types.int, types.uint, types.long, types.ulong,
                    types.llong, types.ullong]
        elif 'u' in suffix:
            if 'l' in suffix:
                ltypes = [types.ulong, types.ullong]
            else:
                ltypes = [types.uint, types.ulong, types.ullong]
        else: # Only l in suffix
            ltypes = [types.long, types.ulong]
        # Return the first type of the list ltypes that contains value
        expr_type = None
        for t in ltypes[:-1]:
            if o.value <= t.max:
                expr_type = t
                break
        if expr_type is None:
            expr_type = ltypes[-1]
        # Transform the Constant in a ConstantExpression class and establish
        # the type of the constant
        self.expression = ConstantExpression(type_=o.type, value=o.value,
            expr_type=expr_type, coord=o.coord)
    def visit_id(self, o):
        try:
            # Replace the name attribute by the symbol itself
            o.name = self.symtable[o.name]
            if o.name.symtype == symbols.ENUMERATOR:
                # Transform the ID in a ConstantExpression
                self.expression = ConstantExpression(
                    value=o.name.value, expr_type=types.int)
            else: # symbols.SYMBOL
                # Transform the ID in an IDExpression
                self.expression = IDExpression(o.name, o.coord)
        except KeyError:
            # TODO: And if we are indeed in a function?
            self.err.error("#'{}'$ undeclared here (not in a function)".format(
                o.name), o.coord)
            self.expression = None
    def visit_structref(self, o):
        o.name.accept(self)
        self.expression = StructRefExpression(self.expression, o.type, o.field,
            o.coord)
    def visit_unaryop(self, o):
        o.expr.accept(self)        
        operator = OPERATORS[o.op]
        e = self.expression
        if operator == OPADDR and isinstance(e, IDExpression):
            ptrtype = self.typespool.add(types.PointerType(e.expr_type))
            self.expression = ConstantExpression(symbol=e.name,
                expr_type=ptrtype, coord=e.coord)
        '''if self.expression.isconstant():
            self.expression = CONSTANT_EXPR[o.op](self.expression)
        else:
            # TODO: Define what happens for not constant expressions
            self.expression = None'''

class FirstASTVisitor(ASTVisitor):
    '''Visits the nodes in the Abstract Syntax Tree and performs the following
    operations:
    * Check semantics.
    * Fill the types pool with all the used types.
    * Fill the symbols table.
    * Compute the type of each expression.
    * Simplifies the constant expressions.
    '''
    def __init__(self, err):
        self.symtable = symbols.Symtable()
        self.typespool = types.TypesPool()
        # Declare the visitors to use
        self.ev = ExpressionVisitor(self.symtable, self.typespool, err)
        self.dv = DeclarationVisitor(
            self.symtable, self.typespool, self.ev, err)
    def visit_decl(self, o):
        o.accept(self.dv)
    def visit_fileast(self, o):
        for e in o.ext:
            e.accept(self)
    def visit_funcdef(self, o):
        o.decl.accept(self.dv)
        # Create a new symtable (function scope) and insert the parameters
        self.symtable.push()
        for s in self.dv.type.params:
            self.symtable.add(s)
        o.body.accept(self.ev)
        # Restore the global symbol table
        self.symtable.pop()

