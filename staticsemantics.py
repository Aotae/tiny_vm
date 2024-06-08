import ASTutils as a
import lark.tree as t
import sys

class Checker:
    
    def __init__(self, symboltable):
        self.symboltable = symboltable
        self.warnings = []
        self.methods = {
            '+': ["String", "Int"],
            '*': ["Int"],
            "-": ["Int"],
            "/": ["Int"],
            '<': ["String", "Int"],
            '>': ["String", "Int"],
            '==': ["String", "Int"],
            '!=': ["String", "Int"],
            "print":["String","Obj","Nothing","Bool","Int"]
        }
        
    def check(self, node):
        if isinstance(node, a.Assignment):
            self.check_assignment(node)
        elif isinstance(node, a.FieldAssign):
            self.check_field_assignment(node)
        elif isinstance(node, a.BinaryOperation):
            self.check_binops(node)
        elif isinstance(node, a.Conditional):
            self.check_cond(node)
        elif isinstance(node, a.SoloCond):
            self.check_cond(node)
        elif isinstance(node, a.IfStatement):
            self.check_if(node)
        elif isinstance(node, a.WhileStatement):
            self.check_while(node)
        elif isinstance(node, a.ClassDeclaration):
            self.check_class_declaration(node)
        elif isinstance(node, a.MethodDeclaration):
            self.check_method_declaration(node)
        elif isinstance(node, a.Methods):
            self.check_method_call(node)

    def check_assignment(self, node):
        if self.check(node.value) != node.inferred_type:
            self.warnings.append(f"Type mismatch in assignment: {node.name}")
            
    def check_field_assignment(self, node):
        if self.check(node.value) != node.inferred_type:
            self.warnings.append(f"Type mismatch in assignment: {node.name}")

    def check_if(self, node):
        error = self.check(node.condition)
        if error is not None:
            sys.tracebacklimit = 0
            raise TypeError(f"\n{error[0]} if {error[1]}")
        if isinstance(node.body, t.Tree):
            for statement in node.body.children:
                if isinstance(statement, a.ASTNode):
                    self.check(statement)
        elif isinstance(node.body, a.ASTNode):
            self.check(node.body)
            
        if isinstance(node.elsebody, t.Tree):
            for statement in node.elsebody.children:
                if isinstance(statement, a.ASTNode):
                    self.check(statement)
        elif isinstance(node.elsebody, a.ASTNode):
            self.check(node.elsebody)
            
    def check_while(self, node):
        error = self.check(node.condition)
        if error is not None:
            sys.tracebacklimit = 0
            raise TypeError(f"\n{error[0]} while {error[1]}")
        if isinstance(node.body, t.Tree):
            for statement in node.body.children:
                if isinstance(statement, a.ASTNode):
                    self.check(statement)
        elif isinstance(node.body, a.ASTNode):
            self.check(node.body)
              
    def check_cond(self, node):
        if isinstance(node, a.Conditional):
            cond_type = node.inferred_type
            eval = f"{node.left.inferred_type} {node.operator} {node.right.inferred_type} evaluates to {cond_type}\nType {cond_type} does not have method '{node.operator}' and cannot return a 'Bool'"
            if cond_type != "Bool":
                return f"Compilation failed\nCondition expression in", f"statement must evaluate to boolean type\n{eval}"
        elif isinstance(node, a.SoloCond):
            cond_type = node.inferred_type
            eval = f"{cond_type}\nType {cond_type} is not a 'Bool'"
            if cond_type != "Bool":
                return f"Compilation failed\nCondition expression in", f"statement must evaluate to boolean type\n{eval}"
        return None
    
    def check_binops(self, node):
        print("checking binops")
        self.check_binops_helper(node.left)
        self.check_binops_helper(node.right)
        
        left_key = self.get_key(node.left)
        right_key = self.get_key(node.right)
        
        if node.operator == '+' and node.inferred_type not in self.methods['+']:
            sys.tracebacklimit = 0
            raise TypeError(f"Compilation failed \nat {left_key}+{right_key}\nType {node.inferred_type} does not have method '+' ")
        if node.operator == '-' and node.inferred_type not in self.methods['-']:
            sys.tracebacklimit = 0
            raise TypeError(f"Compilation failed \nat {left_key}-{right_key}\nType {node.inferred_type} does not have method '-' ") 
        if node.operator == '*' and node.inferred_type not in self.methods['*']:
            sys.tracebacklimit = 0
            raise TypeError(f"Compilation failed \nat {left_key}*{right_key}\nType {node.inferred_type} does not have method '*' ")  
        if node.operator == '/' and node.inferred_type not in self.methods['/']:
            sys.tracebacklimit = 0
            raise TypeError(f"Compilation failed \nat {left_key}/{right_key}\nType {node.inferred_type} does not have method '/' ")

    def check_binops_helper(self, node):
        if isinstance(node, a.BinaryOperation):
            self.check(node)

    def check_class_declaration(self, node):
        for statement in node.body.children:
            if isinstance(statement, a.ASTNode):
                self.check(statement)

    def check_method_declaration(self, node):
        for statement in node.body.children:
            if isinstance(statement, a.ASTNode):
                self.check(statement)

    def check_method_call(self, node):
        obj_type = self.get_node_type(node.obj)
        method_key = f"{obj_type}:{node.method}"
        method_type = self.symboltable.get(method_key, None)

        if method_type is None and obj_type not in self.methods.get(node.method, []):
            raise TypeError(f"Method {node.method} not found in object type {obj_type}")

        if node.args:
            for arg in node.args:
                arg_type = self.check(arg)
                if arg_type not in self.symboltable:
                    raise TypeError(f"Argument type {arg_type} not found in symboltable")

    def get_node_type(self, node):
        if isinstance(node, a.Variable):
            return self.symboltable.get(node.name, "Obj")
        elif isinstance(node, a.Constant):
            return self.get_type_from_constant(node)
        elif isinstance(node, a.NewNode):
            return node.inferred_type
        elif isinstance(node, a.FieldAccess):
            obj_type = self.get_node_type(node.obj)
            return self.symboltable.get(f"{obj_type}.{node.name}", "Obj")
        return "Obj"

    def get_type_from_constant(self, constant):
        if constant.value.startswith("\""):
            return "String"
        elif constant.value == "true" or constant.value == "false":
            return "Bool"
        else:
            return "Int"

    def get_key(self, node):
        if isinstance(node, a.Variable):
            return node.name
        elif isinstance(node, a.Constant):
            return node.value
        elif isinstance(node, a.FieldAccess):
            obj_type = self.get_node_type(node.obj)
            return f"{obj_type}.{node.name}"
        else:
            return "unknown"
