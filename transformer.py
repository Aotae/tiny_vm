from lark import Lark, Transformer, v_args
import sys
import os
import ASTutils
# From Lark Example calculator Grammar

calc_grammar = """
    ?start: declaration
        | assignment
        | method_call
        | stmt
    
    ?condition: value (">" | "<" | "==" | "!=") value
    
    ?stmt: ifstmt
        | whilestmt
        
    ?ifstmt: "if" condition "{" start* "}" -> ifcall
    
    ?whilestmt: "while" condition "{" start* "}" -> whilecall
    
    ?declaration: NAME (":" TYPE)? ";" -> declare_var
    
    ?assignment: NAME "=" value ";" -> assign_var_notype

    ?method_call: value "." NAME "(" ")" ";" -> call_method
    
    ?value: sum
    
    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div

    ?atom: NUMBER           -> number
         | NAME             -> var
         | "(" sum ")"
         | STRING -> string

    TYPE: "Int" 
         | "String"
         | "OBJ"
         
    STRING: /"[^"]*"/
    
    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""
# Parse -> AST -> ASM
@v_args(inline=True)
class ASTGenerator(Transformer):
    # Extending the Lark Transformer class to generate an AST instead of directly translating
    def __init__(self):
        self.vars = set()
        self.symboltable = {}
    
    def assign_var_notype(self, name, value):
        self.vars.add(name)
        node = ASTutils.Assignment(name, value)
        node.infer(self.symboltable)
        return node
    
    def call_method(self, obj, method):
        node = ASTutils.Methods(obj,method)
        node.infer(self.symboltable)
        return node
    
    def add(self, left, right):
        node = ASTutils.BinaryOperation(left, '+', right)
        node.infer(self.symboltable)
        return node

    def sub(self, left, right):
        node = ASTutils.BinaryOperation(left, '-', right)
        node.infer(self.symboltable)
        return node

    def mul(self, left, right):
        node = ASTutils.BinaryOperation(left, '*', right)
        node.infer(self.symboltable)
        return node

    def div(self, left, right):
        node = ASTutils.BinaryOperation(left, '/', right)
        node.infer(self.symboltable)
        return node

    def number(self, value):
        node = ASTutils.Constant(value)
        node.infer(self.symboltable)
        return node
        
    def string(self, value):
        node = ASTutils.Constant(value)
        node.infer(self.symboltable)
        return node

    def var(self, name):
        node = ASTutils.Variable(name)
        node.infer(self.symboltable)
        return node
    
    def print_ast(self, node=None, indent=0):
        if node is None:
            return

        if isinstance(node, ASTutils.Declaration):
            print(' ' * indent, 'Declaration:', node.name, node.t_type)
        elif isinstance(node, ASTutils.Assignment):
            print(' ' * indent, 'Assignment:', node.name)
            self.print_ast(node.value, indent + 4)
        elif isinstance(node, ASTutils.BinaryOperation):
            print(' ' * indent, 'Binary Operation:', node.operator)
            self.print_ast(node.left, indent + 4)
            self.print_ast(node.right, indent + 4)
        elif isinstance(node, ASTutils.Constant):
            print(' ' * indent, 'Constant:', node.value)
        elif isinstance(node, ASTutils.Variable):
            print(' ' * indent, 'Variable:', node.name)
        elif isinstance(node, ASTutils.Methods):
            print(' ' * indent, 'Method Call:', node.method)
            self.print_ast(node.obj, indent + 4)
        # print(self.symboltable)

    def generate_asm(self, node=None):
        if node is None:
            return ''
        elif isinstance(node, ASTutils.Assignment):
            asm = self.generate_asm(node.value)
            return f"{asm}\nstore {node.name}"
        
        elif isinstance(node, ASTutils.Methods):
            asm = self.generate_asm(node.obj)
            if isinstance(node.obj, ASTutils.Constant):
                nodekey = node.obj.value
            else:
                nodekey = node.obj.name
            call = f"{asm}\ncall {self.symboltable[nodekey]}:{node.method}"
            
            if (node.method == "print"):
                call += "\npop"
            return call
        
        elif isinstance(node, ASTutils.BinaryOperation):
            left_asm = self.generate_asm(node.left)
            right_asm = self.generate_asm(node.right)
            if node.operator == '+':
                return f"{right_asm}\n{left_asm}\ncall {self.symboltable[node.identifier]}:plus"
            elif node.operator == '-':
                return f"{right_asm}\n{left_asm}\ncall {self.symboltable[node.identifier]}:minus"
            elif node.operator == '*':
                return f"{right_asm}\n{left_asm}\ncall {self.symboltable[node.identifier]}:mult"
            elif node.operator == '/':
                return f"{right_asm}\n{left_asm}\ncall {self.symboltable[node.identifier]}:div"
            
        elif isinstance(node, ASTutils.Constant):
            return f"const {node.value}"
        elif isinstance(node, ASTutils.Variable):
            return f"load {node.name}"
            
# probably need to generate the asm file this time instead of just generating the code and printing it out
def main():
    debug = open('debug', 'w', encoding="utf-8")
    file = False
    asm = []
    transformer = ASTGenerator()
    calc_parser_ptree = Lark(calc_grammar, parser='lalr')
    calc_parser = Lark(calc_grammar, parser='lalr', transformer=transformer)
    calc = calc_parser.parse
    calcp = calc_parser_ptree.parse
    for index, arg in enumerate(sys.argv[1:]):
        if arg == "-f":
            if index + 1 <len(sys.argv[1:]):
                filename = sys.argv[index+2]
                file = True
            else:
                print(f"Error: requires filename after -f")
                return
    if file:
        path = ASTutils.find_file(os.getcwd(),filename)
        if path:
            print(f"Found {filename} at:{path}")
        else:
            print(f"File {filename} not found in:{os.getcwd()}")
            return
        try:
            # Open the file in read mode as a stream
            with open(path, 'r') as file_stream:
                # Process the file stream (e.g., read lines, parse data)
                for line in file_stream:
                    # skip new lines
                    if line != "\n":
                        # get the ast
                        ast = calc(line.strip())
                        # infer types
                        ast.infer(transformer.symboltable)
                        # add it to the asm list
                        asm.append(ast)
  
        except FileNotFoundError:
            print("File not found:", path)
        except IOError:
            print("Error opening file:", path)
        
        main = open('Main.asm', 'w+', encoding="utf-8")
        print(f".class Main:Obj\n.method $constructor",file=main)
        print('.local',','.join(transformer.vars),file=main)
        for i in range(len(asm)):
            print(transformer.generate_asm(asm[i]),file=main)
            if(transformer.print_ast(asm[i])!=None):
                print(transformer.print_ast(asm[i]))
        print(f"return 0\n",file=main)
        # print(transformer.symboltable)
    else:
        while True:
            try:
                s = input('> ')
            except EOFError:
                break
            # Generate the asm code
            AST = calc(s.strip())
            ptree = calcp(s.strip())
            print("Parse Tree:")
            tree = ptree.pretty('   ')
            print(tree)
            print("AST:")
            transformer.print_ast(AST)
            print("ASM:")
            print(transformer.generate_asm(AST))
            
    debug.close()
            
if __name__ == '__main__':
    main()

