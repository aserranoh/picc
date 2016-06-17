
from compiler import Compiler

"""class ExpressionSimplifierVisitor(ASTVisitor):
    '''Visits the AST nodes and simplifies the constant expressions.
    The original AST is modified in place.
    '''
    # Dictionary of operations indexed by the operator string
    OPS = {
        '|': lambda x, y: x | y,
    }
    def __init__(self):
        # Contains the last visited expression
        self._expression = None
    def visit_node(self, o):
        '''Generic method that iterates over the childs of a node.
        For those of the children nodes that are expressions, replace the
        original node by the one simplified (they might be the same).
        Note that this method cannot be applied on those nodes whose name
        finishes by 'List' (for instance, ExprList), because the names returned
        by the children() method are not attributes names.
        '''
        for name, child in o.children():
            self._expression = None
            child.accept(self)
            # At this point, if self._expression is not None it means that
            # the child was an expression of some kind and self._expression
            # contains the simplified expression (that may be the same as the
            # original).
            if self._expression is not None:
                setattr(o, name, self._expression)
    def visit_binaryop(self, o):
        '''Simplify the binary operator if both left and right are constant.'''
        self.visit_node(o)
        if isinstance(o.left, c_ast.Constant) \
                and isinstance(o.right, c_ast.Constant):
            self._expression = c_ast.Constant(o.left.type,
                self.OPS[o.op](int(o.left.value), int(o.right.value)))
    def visit_constant(self, o): pass
    def visit_exprlist(self, o):
        '''Simplifies the expressions on the list.'''
        for i, e in enumerate(o.exprs):
            self._expression = None
            e.accept(self)
            if self._expression is not None:
                o.exprs[i] = self._expression
    def visit_id(self, o): pass
    # Functions implemented with the generic visit_node method
    visit_arrayref = visit_node
    visit_assignment = visit_node
    visit_compound = visit_node
    visit_decl = visit_node
    visit_dowhile = visit_node
    visit_enum = visit_node
    visit_fileast = visit_node
    visit_funccall = visit_node
    visit_funcdecl = visit_node
    visit_funcdef = visit_node
    visit_identifiertype = visit_node
    visit_if = visit_node
    visit_paramlist = visit_node
    visit_return = visit_node
    visit_struct = visit_node
    visit_structref = visit_node
    visit_typedecl = visit_node
    visit_unaryop = visit_node"""

