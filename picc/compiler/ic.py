
import ast
import symbols

class Address(object):
    '''Contains the address of an object.'''
    def __init__(self, symbol, offset):
        '''An address is composed by a symbol and a constant offset from
        the memory address of that symbol.'''
        self.symbol = symbol
        self.offset = offset

class Instruction(object):
    def __init__(self, op1=None, op2=None, op3=None):
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3

class AssignInstruction(Instruction):
    '''Represents the instruction op1 = op2.'''
    def __str__(self):
        return '  {:s} = {:s}'.format(self.op1, int(self.op2)
            if type(self.op2) == int else self.op2)

class CallInstruction(Instruction):
    def __str__(self):
        return '  {:s} = call {:s}'.format(self.op1, self.op2)

class GotoInstruction(Instruction):
    def __str__(self):
        return '  goto {:s}'.format(self.op1)

class IfInstruction(Instruction):
    def __str__(self):
        return '  if {:s} goto {:s}'.format(self.op1, self.op2)

class Label(Instruction):
    def __str__(self):
        return '{:s}:'.format(self.op1)

class ParamInstruction(Instruction):
    def __str__(self):
        return '  param {:s}'.format(self.op1)

class ReturnInstruction(Instruction):
    def __str__(self):
        return '  return'

class IntermediateCodeGeneratorVisitor(ast.ASTVisitor):
    '''Generic class for visitors that generate intermediate code.'''
    _temp_id = 0
    #def __init__(self):
        #self.symtable = symtable
        # Helper visitors
        #self.rv = None
        #self.jv = None
    def _newtemp(self):
        '''Generates a new temporary symbol and inserts it in the symtable.'''
        s = symbols.Symbol('.t{}'.format(
            IntermediateCodeGeneratorVisitor._temp_id), None)
        IntermediateCodeGeneratorVisitor._temp_id += 1
        return s

class JumpCodeVisitor(IntermediateCodeGeneratorVisitor):
    '''Visits an expression node and generates jump code.
    self.true: Contains the label where to jump if the expression evaluates
    true.
    self.false: Contains the label where to jump if the expression evaluates
    false.
    '''
    def visit_node(self, o):
        '''Generic method.
        Evaluates the rvalue expression and jumps according to its result.
        '''
        o.accept(self.rv)
        self.code.append(IfInstruction(self.rv.symbol, self.true))
        self.code.append(GotoInstruction(self.false))
    def visit_constant(self, o):
        '''Generate intermediate code for constant used in a boolean
        expression.'''
        self.code.append(
            GotoInstruction(self.true if int(o.value) else self.false))
    # Nodes visited with the generic method
    visit_funccall = visit_node
    visit_structref = visit_node

class RValueCodeVisitor(IntermediateCodeGeneratorVisitor):
    '''Visits an expression node and generates code to compute its rvalue.
    After calling a visit method, self.symbol contains the temporary symbol
    that contains the evaluated expression.
    '''
    def __init__(self, code):
        self.code = code
    def visit_assignment(self, o):
        # Evaluate the rvalue expression
        o.rvalue.accept(self)
        # Obtain the lvalue
        o.lvalue.accept(self.lv)
        # Emit the assign instruction
        self.code.append(self.lv.lvalue.get_assign_instruction(self.symbol))
        # Note that here, self.symbol contains the rvalue of the expression in
        # o.rvalue. That is useful if this assignment expression is used as an
        # rvalue as well.
    def visit_constant(self, o):
        '''Generate intermediate code to evaulate the rvalue of a constant
        expression.'''
        self.symbol = t = self._newtemp()
        self.code.append(AssignInstruction(t, int(o.value)))
    def visit_funccall(self, o):
        '''Generate intermediate code to evaluate the rvalue of a function
        call.'''
        # Evaluate the arguments
        if o.args is not None:
            for e in o.args.exprs:
                e.accept(self)
                self.code.append(ParamInstruction(self.symbol))
        # Evaluate the address to be called
        o.name.accept(self)
        # Call the function
        t = self._newtemp()
        self.code.append(CallInstruction(t, self.symbol))
        self.symbol = t
    def visit_id(self, o):
        self.symbol = o.name
    def visit_structref(self, o):
        '''Generate intermediate code to evaluate the rvalue of a struct
        reference'''
        # Evaluate the struct
        self.symbol = t = self._newtemp()
        struct_symbol = self.symtable[o.name.name]
        field_symbol = struct_symbol.type.fields[o.field.name]
        self.code.append(StructRefInstruction(t, struct_symbol, field_symbol))

class LValue(object):
    '''Generic lvalue, to be used as base clase.'''
    def __init__(self, address, offset):
        '''Constructor.
        For convenience, an lvalue is represented by:
        address: composed by a symbol that identifies the lvalue and a constant
                 offset.
        offset: a symbol that represents an expression with a variable offset.
        '''
        self.address = address
        self.offset = offset
    def get_assign_instruction(self, expression):
        '''Generate an assign instruction to assign expression to this lvalue.
        '''
        raise NotImplementedError

class DirectLValue(object):
    '''An lvalue that is accessed directly in memory (not through a pointer).
    '''
    def get_assign_instruction(self, expression):
        '''Generate an assign instruction to assign expression to this lvalue.
        '''
        # If self.offset is None, then use a simple AssignInstruction to
        # assign expression to this lvalue. If not, use an
        # AssignArrayInstruction.
        if self.offset is None:
            i = AssignInstruction(lvalue=self.address, rvalue=expression)
        else:
            i = AssignArrayInstruction(base=self.address, offset=self.offset,
                                       rvalue=expression)

class IndirectLValue(object):
    '''An lvalue that is accessed through a pointer.
    Represents the lvalue pointed by the address (self.address + self.offset).
    '''
    def get_assign_instruction(self, expression):
        '''Generate an assign instruction to assign expression to this lvalue.
        '''
        i = AssignPointerInstruction(base=self.address, offset=self.offset,
                                     rvalue=expression)

class LValueCodeVisitor(IntermediateCodeGeneratorVisitor):
    '''Visits a subtree of the AST that represents an lvalue and generates an
    LValue object that represents it.
    '''
    def __init__(self, code):
        self.code = code
    def visit_arrayref(self, o):
        '''Compute the lvalue associated with an array access.
        The base of the array may be one of two types: an array, in that case
        it is already an lvalue, and a pointer, that points to the lvalue
        needed but it is not an lvalue.
        '''
        # Compute the lvalue of the array, or the destination of the pointer
        base_type = o.name.expr_type.type
        if base_type == TYPE_ARRAY:
            o.name.accept(self)
        else:
            # If it's not an array, it is a pointer
            o.name.accept(self.rv)
            self.lvalue = IndirectLValue(self.rv.address, None)
        # Compute the expression given by the subscript and add the offset to
        # the lvalue
        if isinstance(o.subscript, Constant) and base_type == TYPE_ARRAY:
            self.lvalue.address.offset += o.subscript.value
        else:
            o.subscript.accept(self.rv)
            self.lvalue += self.rv.address
    def visit_id(self, o):
        '''Compute the lvalue associated to a variable.'''
        self.lvalue = DirectLValue(o.name)
    def visit_structref(self, o):
        '''Compute the lvalue of a struct field.'''
        # Compute the lvalue of the whole struct
        o.name.accept(self)
        # Add to this lvalue the constant offset of the accessed field
        self.lvalue += o.name.expr_type[o.field.name].offset
    def visit_unaryop(self, o):
        '''The only operation supported for LValue is * (pointer).'''
        # Compute the rvalue of the operand (the address)
        o.expr.accept(self.rv)
        # Compute the pointed lvalue
        self.lvalue = IndirectLValue(address=self.rv.address, offset=None)

class ASTCodeGeneratorVisitor(IntermediateCodeGeneratorVisitor):
    '''Visits the AST nodes and generates three address code.'''
    def __init__(self):
        self.code = []
        # Create the helper visitors
        self.rv = RValueCodeVisitor(self.code)
        self.lv = LValueCodeVisitor(self.code)
        # Make the visitors visible to each other
        self.rv.lv = self.lv
        self.lv.rv = self.rv
        #self._label_id = 0
    def __str__(self):
        return '\n'.join([str(i) for i in self.code])
    def _newlabel(self):
        s = Symbol('.l{}'.format(self._label_id), None)
        self._label_id += 1
        self._symtable[s.name] = s
        return s
    def visit_assignment(self, o):
        o.accept(self.rv)
    def visit_compound(self, o):
        for i in o.block_items:
            i.accept(self)
    def visit_decl(self, o): pass
    def visit_dowhile(self, o):
        '''Generate intermediate code for a do-while statement.'''
        begin = self._newlabel()
        end = self._newlabel()
        self.code.append(Label(begin))
        o.stmt.accept(self)
        jv = JumpCodeVisitor(self._symtable, true=begin, false=end)
        o.cond.accept(jv)
        self.code.extend(jv.code)
        self.code.append(Label(end))
    def visit_fileast(self, o):
        for e in o.ext:
            e.accept(self)
    def visit_funccall(self, o):
        '''Generate code for a function call.
        This is called when the funccall is not part of a condition, so the
        RValueCodeVisitor must be used.
        '''
        rv = RValueCodeVisitor(self._symtable)
        o.accept(rv)
        self.code.extend(rv.code)
    def visit_funcdef(self, o):
        #self.code.append(Label(self.symtable[o.decl.name]))
        o.body.accept(self)
    def visit_if(self, o):
        '''Generate intermediate code for an if statement.'''
        truelabel = self._newlabel()
        endlabel = self._newlabel()
        if o.iffalse is not None:
            falselabel = self._newlabel()
        else:
            falselabel = endlabel
        jv = JumpCodeVisitor(self._symtable, true=truelabel, false=falselabel)
        o.cond.accept(jv)
        self.code.extend(jv.code)
        self.code.append(Label(truelabel))
        o.iftrue.accept(self)
        if o.iffalse is not None:
            self.code.append(GotoInstruction(endlabel))
            self.code.append(Label(falselabel))
            o.iffalse.accept(self)
        self.code.append(Label(endlabel))
    def visit_return(self, o):
        '''Generate intermediate code for a return statement.'''
        self.code.append(ReturnInstruction())

