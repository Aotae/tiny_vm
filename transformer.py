from lark import Lark, Transformer, v_args 
import lark.tree as t
import sys
import os
import ASTutils
import staticsemantics as ss
# From Lark Example calculator Grammar

calc_grammar = """
    ?start: codeblock

    codeblock: statement+

    ?statement: assignment
        | method_call
        | flow
        | class_decl
        | return_statement

    ?condition: value evaluator value -> conditional
        | value -> boolean

    logicalexpr: or_expr

    ?or_expr: and_expr
        | or_expr "or" and_expr -> or_

    ?and_expr: not_expr
        | and_expr "and" not_expr -> and_

    ?not_expr: "not" not_expr -> not_
        | condition

    ?evaluator: ">" -> gt
        | "<" -> lt
        | "==" -> equals
        | "!=" -> nequals

    ?flow: ifstmt
        | whilestmt

    ?ifstmt: "if" logicalexpr "{" codeblock* "}" elsestmt? -> ifcall

    ?elsestmt: "else" "{" codeblock* "}" -> elsecall

    ?return_statement: "return" value? ";" -> return_stmt

    ?whilestmt: "while" logicalexpr "{" codeblock* "}" -> whilecall
    
    ?assignment: NAME "=" value ";" -> assign_var
        | field "=" value ";" -> assign_field

    ?method_call: calls ";"

    ?class_decl: "class" NAME "(" formal_args ")" "{" class_body "}" -> class_declaration_p
        | "class" NAME "(" ")" "{" class_body "}" -> class_declaration
        | "class" NAME "(" formal_args ")" "extends" NAME "{" class_body "}" -> class_declaration_extended_p
        | "class" NAME "(" ")" "extends" NAME "{" class_body "}" -> class_declaration_extended

    ?method_decl: "def" NAME "(" argument_list ")" ":" NAME "{" codeblock* "}" -> mthd_p_decl_return
        | "def" NAME "(" argument_list ")" "{" codeblock* "}" -> mthd_p_decl
        | "def" NAME "(" ")"  ":" NAME  "{" codeblock* "}" -> mthd_decl_return
        | "def" NAME "(" ")" "{" codeblock* "}" -> mthd_decl

    formal_args: formal_arg ("," formal_arg)*
    formal_arg: NAME ":" NAME

    argument_list: value ("," value)*

    class_body: (method_decl | statement)*

    ?value: sum

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: calls
        | product "*" calls  -> mul
        | product "/" calls  -> div

    ?calls: field
        | method_invocation

    ?field: atom
        | field "." NAME -> access_field

    ?method_invocation: field "." NAME "(" argument_list? ")" -> call_method

    ?atom: NUMBER -> number
        | STRING -> string
        | NAME "(" argument_list? ")" -> new
        | NAME -> var
        | "(" sum ")"
        | TRUE -> tf
        | FALSE -> tf
    TRUE: "true"
    FALSE: "false"
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
        self.classtable = {}
        self.symboltable = {}
        self.current_class = None
        self.if_counter = 0
        self.while_counter = 0
        self.and_counter = 0
        self.or_counter = 0
        self.not_counter = 0

    def assign_var(self, name, value):
        self.vars.add(name)
        node = ASTutils.Assignment(name, value)
        return node

    def call_method(self, obj, method, args=None):
        node = ASTutils.Methods(obj, method, args)
        return node

    def conditional(self, left, operator, right):
        node = ASTutils.Conditional(left, operator, right)
        return node

    def ifcall(self, conditional, body, elsepart=None):
        node = ASTutils.IfStatement(conditional, body, elsepart)
        return node

    def whilecall(self, conditional, body):
        node = ASTutils.WhileStatement(conditional, body)
        return node

    def class_declaration(self, name, body):
        node = ASTutils.ClassDeclaration(name, None, "Obj", body)
        return node

    def class_declaration_extended(self, name, extends, body):
        node = ASTutils.ClassDeclaration(name, None, extends, body)
        return node

    def class_declaration_p(self, name, args, body):
        node = ASTutils.ClassDeclaration(name, args, "Obj", body)
        return node

    def class_declaration_extended_p(self, name, args, extends, body):
        node = ASTutils.ClassDeclaration(name, args, extends, body)
        return node

    def mthd_p_decl_return(self, name, params, return_type, body):
        node = ASTutils.MethodDeclaration(name, params, return_type, body)
        return node

    def mthd_p_decl(self, name, params, body):
        node = ASTutils.MethodDeclaration(name, params, "Nothing", body)
        return node

    def mthd_decl_return(self, name, return_type, body):
        node = ASTutils.MethodDeclaration(name, [], return_type, body)
        return node

    def mthd_decl(self, name, body):
        node = ASTutils.MethodDeclaration(name, [], "Nothing", body)
        return node

    def return_stmt(self, value=None):
        node = ASTutils.ReturnStatement(value)
        return node

    def boolean(self, value):
        node = ASTutils.SoloCond(value)
        return node

    def add(self, left, right):
        node = ASTutils.BinaryOperation(left, '+', right)
        return node

    def sub(self, left, right):
        node = ASTutils.BinaryOperation(left, '-', right)
        return node

    def mul(self, left, right):
        node = ASTutils.BinaryOperation(left, '*', right)
        return node

    def div(self, left, right):
        node = ASTutils.BinaryOperation(left, '/', right)
        return node

    def number(self, value):
        node = ASTutils.Constant(value)
        return node

    def string(self, value):
        node = ASTutils.Constant(value)
        return node

    def tf(self, value):
        node = ASTutils.Constant(value)
        return node

    def var(self, name):
        node = ASTutils.Variable(name)
        return node

    def assign_field(self, obj, value):
        node = ASTutils.FieldAssign(obj, value)
        return node

    def access_field(self, obj, name):
        node = ASTutils.FieldAccess(obj, name)
        return node

    def new(self, name, args):
        node = ASTutils.NewNode(name, args)
        return node

    def print_ast(self, node=None, indent=0):
        if node is None:
            return

        if isinstance(node, t.Tree):
            for statement in node.children:
                self.print_ast(statement, indent)

        if isinstance(node, ASTutils.Assignment):
            print(' ' * indent, 'Assignment:', node.name, 'Type:', node.inferred_type)
            self.print_ast(node.value, indent + 4)

        elif isinstance(node, ASTutils.ClassDeclaration):
            print(' ' * indent, 'Class Declaration:', node.name, 'Type:', node.inferred_type)
            self.print_ast(node.body, indent + 4)

        elif isinstance(node, ASTutils.BinaryOperation):
            print(' ' * indent, 'Binary Operation:', node.operator, 'Type:', node.inferred_type)
            self.print_ast(node.left, indent + 4)
            self.print_ast(node.right, indent + 4)

        elif isinstance(node, ASTutils.Constant):
            print(' ' * indent, 'Constant:', node.value, 'Type:', node.inferred_type)

        elif isinstance(node, ASTutils.Variable):
            print(' ' * indent, 'Variable:', node.name, 'Type:', node.inferred_type)

        elif isinstance(node, ASTutils.Methods):
            print(' ' * indent, 'Method Call:', node.method, 'Type:', node.obj)
            self.print_ast(node.obj, indent + 4)
            print(' ' * indent, "args:", node.args)
        elif isinstance(node, ASTutils.IfStatement):
            print(' ' * indent, 'If Statement:')
            self.print_ast(node.condition, indent + 4)
            self.print_ast(node.body, indent + 4)
            if node.elsebody is not None:
                print(' ' * indent, 'Else:')
                self.print_ast(node.elsebody, indent + 4)

        elif isinstance(node, ASTutils.WhileStatement):
            print(' ' * indent, 'While Loop:')
            self.print_ast(node.condition, indent + 4)
            self.print_ast(node.body, indent + 4)

        elif isinstance(node, ASTutils.Conditional):
            print(' ' * indent, 'Conditional:', 'Type:', node.inferred_type)
            self.print_ast(node.left, indent + 4)
            print(' ' * (indent + 4), 'Operator:', node.operator)
            self.print_ast(node.right, indent + 4)

        elif isinstance(node, ASTutils.SoloCond):
            print(' ' * indent, 'Solo Conditional:', 'Type:', node.inferred_type)
            self.print_ast(node.value, indent + 4)

        elif isinstance(node, ASTutils.LogicalOperation):
            print(' ' * indent, 'Logical Operation:', node.operator, 'Type:', node.inferred_type)
            self.print_ast(node.left, indent + 4)
            if node.right is not None:
                self.print_ast(node.right, indent + 4)

        elif isinstance(node, ASTutils.FieldAssign):
            print(' ' * indent, 'Field Assignment:', node.name, 'Type:', node.inferred_type)
            self.print_ast(node.obj, indent + 4)
            self.print_ast(node.value, indent + 4)

        elif isinstance(node, ASTutils.FieldAccess):
            print(' ' * indent, 'Field Access:', node.name, 'Type:', node.inferred_type)
            self.print_ast(node.obj, indent + 4)

        elif isinstance(node, ASTutils.MethodDeclaration):
            print(' ' * indent, 'Method Declaration:', node.methodname, 'Type:', node.inferred_type)
            self.print_ast(node.body, indent + 4)

        elif isinstance(node, ASTutils.NewNode):
            print(' ' * indent, 'New Instance:', node.inferred_type, 'Type:', node.inferred_type)
            print(' ' * indent, "args:", node.args)

        elif isinstance(node, ASTutils.ReturnStatement):
            print(' ' * indent, 'Return Statement:', 'Value:', node.value)
            self.print_ast(node.value, indent + 4)

    def print_symbol_table(self):
        print("Symbol Table:")
        for key, value in self.symboltable.items():
            print(f"  {key}: {value}")

    def typecheck(self, checker, node=None):
        if node is None:
            return ''
        if isinstance(node, t.Tree):
            for statement in node.children:
                print(statement)
                checker(statement)

    def generate_asm(self, node=None, for_store=False, indent_level=0):
        indent = "    " * indent_level  # Four spaces for each indentation level
        inner_indent = "    " * (indent_level + 1)  # Indentation for inner content

        if node is None:
            return ''

        elif isinstance(node, t.Tree):
            asm = ""
            for statement in node.children:
                asm += self.generate_asm(statement, for_store=for_store, indent_level=indent_level) + "\n"
            return asm

        elif isinstance(node, ASTutils.ClassDeclaration):
            classname = node.name
            classasm = f"{node.name}:{node.extended}"
            fields = "\n".join([f".field {field}" for field in node.fields])
            methods = "\n".join([f".method {method} forward" for method in node.methods])
            constructor = f".method $constructor"
            constructor_args = ".args " + ",".join([f"{arg[0]}" for arg in node.args]) if node.args else ""
            method_bodies = ""
            constructor_body = ""
            
            for statement in node.body.children:
                if isinstance(statement, ASTutils.MethodDeclaration):
                    method_bodies += self.generate_asm(statement, indent_level=indent_level) + "\n"
                else:
                    constructor_body += self.generate_asm(statement) + "\n"
            
            constructor_asm = f"{constructor}\n{constructor_args}\n{inner_indent}enter\n{constructor_body}{inner_indent}load $\nreturn {len(node.args)}\n"
            class_asm_code = f".class {classasm}\n{fields}\n{methods}\n{constructor_asm}\n{method_bodies}"
            self.write_class_asm(classname, class_asm_code)
            return ""

        elif isinstance(node, ASTutils.MethodDeclaration):
            method_header = f".method {node.methodname}"
            method_body = self.generate_asm(node.body)
            return f"{method_header}\n{inner_indent}enter\n{method_body}{inner_indent}return {len(node.params)}"

        elif isinstance(node, ASTutils.FieldAccess):
            obj_asm = self.generate_asm(node.obj, indent_level=indent_level)
            if for_store:
                return f"{obj_asm}"
            objtype = node.obj.inferred_type
            objname = node.obj.name
            if objname == "this":
                objtype = "$"
            return f"{obj_asm}\n{inner_indent}load_field {objtype}:{node.name}"

        elif isinstance(node, ASTutils.FieldAssign):
            value_asm = self.generate_asm(node.value, indent_level=indent_level)
            obj_asm = self.generate_asm(node.obj, for_store=True, indent_level=indent_level)
            objname = node.obj.obj.name
            if objname == "this":
                objname = "$"
            return f"{value_asm}\n{obj_asm}\n{inner_indent}store_field {objname}:{node.name}"

        elif isinstance(node, ASTutils.Assignment):
            asm = self.generate_asm(node.value, indent_level=indent_level)
            return f"{asm}\n{inner_indent}store {node.name}"

        elif isinstance(node, ASTutils.IfStatement):
            ifasm = ""
            condition_asm = self.generate_asm(node.condition, indent_level=indent_level)
            then_asm = self.generate_asm(node.body, indent_level=indent_level + 1)
            thenlabel = f"then_{self.if_counter}"
            elselabel = f"else_{self.if_counter}"
            endiflabel = f"endif_{self.if_counter}"
            self.if_counter += 1
            ifasm += f"{condition_asm}\n"
            ifasm += f"{inner_indent}jump_ifnot {elselabel}\n"
            ifasm += f"{inner_indent}jump {thenlabel}\n"
            ifasm += f"{thenlabel}:\n{then_asm}\n{inner_indent}jump {endiflabel}\n"
            if node.elsebody is not None:
                else_asm = self.generate_asm(node.elsebody, indent_level=indent_level + 1)
                ifasm += f"{elselabel}:\n"
                ifasm += f"{else_asm}"
            else:
                ifasm += f"{elselabel}:\n"
            ifasm += f"{endiflabel}:\n"
            return ifasm
        
        elif isinstance(node, ASTutils.LogicalOperation):
            if node.operator == "and":
                label_and = f"and_false_{self.and_counter}"
                label_end = f"and_end_{self.and_counter}"
                self.and_counter += 1
                left_asm = self.generate_asm(node.left, indent_level=indent_level)
                right_asm = self.generate_asm(node.right, indent_level=indent_level)
                return f"{left_asm}\n{inner_indent}jump_ifnot {label_and}\n{right_asm}\n{inner_indent}jump_ifnot {label_and}\n{inner_indent}const true\n{inner_indent}jump {label_end}\n{label_and}:\n{inner_indent}const false\n{label_end}:"
            
            elif node.operator == "or":
                label_or = f"or_true_{self.or_counter}"
                label_end = f"or_end_{self.or_counter}"
                self.or_counter += 1
                left_asm = self.generate_asm(node.left, indent_level=indent_level)
                right_asm = self.generate_asm(node.right, indent_level=indent_level)
                return f"{left_asm}\n{inner_indent}jump_if {label_or}\n{right_asm}\n{inner_indent}jump_if {label_or}\n{inner_indent}const false\n{inner_indent}jump {label_end}\n{label_or}:\n{inner_indent}const true\n{label_end}:\n"
            
            elif node.operator == "not":
                value_asm = self.generate_asm(node.left, indent_level=indent_level)
                label_true = f"val_true_{self.not_counter}"
                label_end = f"end_not_{self.not_counter}"
                self.not_counter += 1
                return f"{value_asm}\n{inner_indent}jump_if {label_true}\n{inner_indent}const true\n{inner_indent}jump {label_end}\n{label_true}:\n{inner_indent}const false\n{label_end}:\n"

        elif isinstance(node, ASTutils.WhileStatement):
            while_asm = ""
            condition_asm = self.generate_asm(node.condition, indent_level=indent_level)
            body_asm = self.generate_asm(node.body, indent_level=indent_level + 1)
            whilelabel = f"while_{self.while_counter}"
            endlabel = f"endwhile_{self.while_counter}"
            self.while_counter += 1
            while_asm += f"{whilelabel}:\n"
            while_asm += f"{condition_asm}\n{inner_indent}jump_ifnot {endlabel}\n"
            while_asm += f"{body_asm}\n{inner_indent}jump {whilelabel}\n"
            while_asm += f"{endlabel}:\n"
            return while_asm

        elif isinstance(node, ASTutils.ReturnStatement):
            value_asm = self.generate_asm(node.value, indent_level=indent_level) if node.value else ""
            return f"{value_asm}"

        elif isinstance(node, ASTutils.Conditional):
            left_asm = self.generate_asm(node.left, indent_level=indent_level)
            right_asm = self.generate_asm(node.right, indent_level=indent_level)
            if node.operator == '>':
                return f"{left_asm}\n{right_asm}\n{inner_indent}call {self.symboltable[node.identifier]}:less"
            elif node.operator == '<':
                return f"{right_asm}\n{left_asm}\n{inner_indent}call {self.symboltable[node.identifier]}:less"
            elif node.operator == '==':
                return f"{right_asm}\n{left_asm}\n{inner_indent}call {self.symboltable[node.identifier]}:equals"

        elif isinstance(node, ASTutils.SoloCond):
            s_cond_asm = self.generate_asm(node.value, indent_level=indent_level)
            return f"{s_cond_asm}"

        elif isinstance(node, ASTutils.Methods):
            table = self.symboltable
            asm = self.generate_asm(node.obj, indent_level=indent_level)
            if isinstance(node.obj, ASTutils.Constant):
                nodekey = node.obj.value
            elif isinstance(node.obj, ASTutils.Variable):
                nodekey = node.obj.name
            elif isinstance(node.obj, ASTutils.FieldAccess):
                nodekey = f"{node.obj.obj.name}.{node.obj.name}"
                asm = self.generate_asm(node.obj, indent_level=indent_level)
            args_asm = ""
            if node.args:
                for arg in node.args:
                    args_asm += self.generate_asm(arg, indent_level=indent_level) + "\n"

            call = f"{args_asm}{asm}\n{inner_indent}call {table[nodekey]}:{node.method}"

            if node.method == "print":
                call += f"\n{inner_indent}pop"
            return call

        elif isinstance(node, ASTutils.NewNode):
            args_asm = ""
            if node.args:
                for arg in node.args:
                    args_asm += self.generate_asm(arg, indent_level=indent_level) + "\n"

            new_obj = f"{inner_indent}new {node.inferred_type}\n"
            newcall = f"{args_asm}{new_obj}{inner_indent}call {node.inferred_type}:$constructor"
            return newcall

        elif isinstance(node, ASTutils.BinaryOperation):
            left_asm = self.generate_asm(node.left, indent_level=indent_level)
            right_asm = self.generate_asm(node.right, indent_level=indent_level)
            if node.operator == '+':
                return f"{right_asm}\n{left_asm}\n{inner_indent}call {self.symboltable[node.identifier]}:plus"
            elif node.operator == '-':
                return f"{right_asm}\n{left_asm}\n{inner_indent}call {self.symboltable[node.identifier]}:minus"
            elif node.operator == '*':
                return f"{right_asm}\n{left_asm}\n{inner_indent}call {self.symboltable[node.identifier]}:mult"
            elif node.operator == '/':
                return f"{right_asm}\n{left_asm}\n{inner_indent}call {self.symboltable[node.identifier]}:div"

        elif isinstance(node, ASTutils.Constant):
            return f"{inner_indent}const {node.value}"

        elif isinstance(node, ASTutils.Variable):
            if node.name == "this":
                return f"{inner_indent}load $"
            return f"{inner_indent}load {node.name}"

        return ""


    def write_class_asm(self, class_name, asm_code):
        file_name = f"{class_name}.asm"
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(asm_code)
        
def main():
    debug = open('debug', 'w', encoding="utf-8")
    file = False
    asm = ""
    transformer = ASTGenerator()
    calc_parser_ptree = Lark(calc_grammar, parser='lalr')
    calc_parser = Lark(calc_grammar, parser='lalr', transformer=transformer)
    calc = calc_parser.parse
    calcp = calc_parser_ptree.parse
    for index, arg in enumerate(sys.argv[1:]):
        if arg == "-f":
            if index + 1 < len(sys.argv[1:]):
                filename = sys.argv[index+2]
                file = True
            else:
                print(f"Error: requires filename after -f")
                return
    if file:
        path = ASTutils.find_file(os.getcwd(), filename)
        if path:
            print(f"Found {filename} at:{path}")
        else:
            print(f"File {filename} not found in:{os.getcwd()}")
            return
        try:
            with open(path, 'r') as file_stream:
                content = file_stream.read().replace("\n", "")
                print()
                tree = calc(content)
                # First pass: build the AST and collect symbols
                # kind of abusing the infer function honestly
                # this should be its own thing
                for node in tree.children:
                    node.infer(transformer.symboltable, pass_number=1)
                    
                # print()
                # transformer.print_symbol_table()
                # print()
                
                # transformer.print_ast(tree)
                # Second pass: resolve `this` references
                for node in tree.children:
                    node.infer(transformer.symboltable, pass_number=2)
                    
                print("FINAL SYMBOL TABLE AND TREE")
                transformer.print_symbol_table()
                print()
                transformer.print_ast(tree)
                checker = ss.Checker(transformer.symboltable)
                transformer.typecheck(checker.check, tree)

                asm = transformer.generate_asm(tree)  # Add initial indent level


        except FileNotFoundError:
            print("File not found:", path)
        except IOError:
            print("Error opening file:", path)
        
        main_file_name = 'Main.asm'
        with open(main_file_name, 'w+', encoding="utf-8") as main:
            print(f".class Main:Obj\n.method $constructor", file=main)
            if transformer.vars:
                print(f"    .local {','.join(transformer.vars)}", file=main)  # Indent .local statement
            print("    enter", file=main)  # Indent enter statement
            print(asm, file=main)
            print(f"    return 0\n", file=main)  # Indent return statement

    else:
        while True:
            try:
                s = input('> ')
            except EOFError:
                break
            AST = calc(s.strip())
            ptree = calcp(s.strip())
            print("Parse Tree:")
            tree = ptree.pretty('   ')
            print(tree)
            print("AST:")
            transformer.print_ast(AST)
            print("ASM:")
            print(transformer.generate_asm(AST, indent_level=1))  # Add initial indent level
            
    debug.close()

if __name__ == '__main__':
    main()

