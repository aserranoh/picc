
import pycparser
import ast
import ic
import picc.error

class Compiler(object):
    def __init__(self, ifile, include):
        self.ifile = ifile
        self.include = include
    def compile(self):
        try:
            # Parse the source object
            cpp_args = r' '.join([r'-I{}'.format(path)
                for path in self.include])
            tree = pycparser.parse_file(
                self.ifile, use_cpp=True, cpp_args=cpp_args)
            tree.show()
            # First AST visit
            e = picc.error.Error()
            v = ast.FirstASTVisitor(e)
            tree.accept(v)
            # Generate three address code
            gen = ic.ASTCodeGeneratorVisitor()
            tree.accept(gen)
            # Print the generated code
            print(gen)
        except pycparser.plyparser.ParseError as e:
            # Syntactic error
            print(e)

