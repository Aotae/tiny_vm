import os
import lark.tree as t

PRIMITIVES = ["String", "Obj", "Int", "Bool", "Nothing"]

class ASTNode:
    def __init__(self):
        pass

    def infer(self, symboltable, current_class=None, pass_number=1):
        pass

class ThisReference(ASTNode):
    def __init__(self):
        self.inferred_type = None

    def infer(self, symboltable, current_class=None, pass_number=1):
        if pass_number == 2:
            self.inferred_type = symboltable.get("this")
            if self.inferred_type is None:
                raise ValueError("`this` not found in symboltable")
        return self.inferred_type

class Variable(ASTNode):
    def __init__(self, name):
        self.name = name
        self.inferred_type = None

    def infer(self, symboltable, current_class=None, pass_number=1):
        if self.name == "this":
            return ThisReference().infer(symboltable, current_class, pass_number)
        if pass_number == 2:
            # print(self.name)
            self.inferred_type = symboltable.get(self.name)
            if self.inferred_type is None:
                raise ValueError(f"{self.name} not found in symboltable")
        return self.inferred_type

class Conditional(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        self.inferred_type = "Obj"
        self.identifier = f"{left}{operator}{right}"

    def infer(self, symboltable, current_class=None, pass_number=1):
        ltype = self.left.infer(symboltable, current_class, pass_number)
        rtype = self.right.infer(symboltable, current_class, pass_number)
        if ltype != rtype:
            self.inferred_type = "Obj"
        else:
            self.inferred_type = "Bool"
        symboltable[self.identifier] = self.inferred_type
        return self.inferred_type

class IfStatement(ASTNode):
    def __init__(self, condition, body, elsebody=None):
        self.condition = condition
        self.elsebody = elsebody
        self.body = body

    def infer(self, symboltable, current_class=None, pass_number=1):
        self.infer_node(self.condition, symboltable, current_class, pass_number)
        self.infer_node(self.body, symboltable, current_class, pass_number)
        if self.elsebody:
            self.infer_node(self.elsebody, symboltable, current_class, pass_number)

    def infer_node(self, node, symboltable, current_class, pass_number):
        if isinstance(node, t.Tree):
            for child in node.children:
                self.infer_node(child, symboltable, current_class, pass_number)
        elif isinstance(node, ASTNode):
            node.infer(symboltable, current_class, pass_number)

class WhileStatement(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def infer(self, symboltable, current_class=None, pass_number=1):
        condition_type = self.condition.infer(symboltable, current_class, pass_number)
        if condition_type != "Bool":
            raise ValueError("Condition expression in while loop must evaluate to boolean type")
        for statement in self.body.children:
            statement.infer(symboltable, current_class, pass_number)

class Assignment(ASTNode):
    def __init__(self, name, value):
        self.inferred_type = None
        self.name = name
        self.value = value

    def infer(self, symboltable, current_class=None, pass_number=1):
        # print(self.value)
        self.inferred_type = self.value.infer(symboltable, current_class, pass_number)
        if pass_number == 2:
            if self.name in symboltable:
                existing_type = symboltable[self.name]
                if existing_type != self.inferred_type:
                    self.inferred_type = "Obj"
            symboltable[self.name] = self.inferred_type
        return self.inferred_type

class BinaryOperation(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        self.inferred_type = "Obj"
        self.identifier = f"{left}{operator}{right}"

    def infer(self, symboltable, current_class=None, pass_number=1):
        ltype = self.left.infer(symboltable, current_class, pass_number)
        rtype = self.right.infer(symboltable, current_class, pass_number)
        if ltype == rtype:
            self.inferred_type = ltype
        else:
            self.inferred_type = "Obj"
        symboltable[self.identifier] = self.inferred_type
        return self.inferred_type

class ClassDeclaration(ASTNode):
    def __init__(self, name, args, extends, body):
        self.name = name
        self.args = generate_formal_args(args)
        self.extended = extends
        self.body = body
        self.inferred_type = name
        self.methods = set()
        self.fields = {}

    def infer(self, symboltable, current_class=None, pass_number=1):
        current_class = self.name
        if pass_number == 1:
            symboltable["this"] = self.name
            symboltable[self.name] = self.inferred_type
            for arg_name, arg_type in self.args:
                symboltable[f"{arg_name}"] = arg_type
        
        for statement in self.body.children:
            if isinstance(statement, FieldAssign):
                field_name = statement.obj.name
                field_type = statement.value.infer(symboltable, current_class, pass_number)
                self.fields[field_name] = field_type
            elif isinstance(statement, MethodDeclaration):
                method_name = statement.methodname
                return_type = statement.inferred_type
                symboltable[f"{self.name}:{method_name}"] = return_type
                self.methods.add(method_name)
                statement.infer(symboltable, current_class, pass_number)
            elif isinstance(statement, ASTNode):
                statement.infer(symboltable, current_class, pass_number)

        return self.inferred_type

class MethodDeclaration(ASTNode):
    def __init__(self, methodname, params, returntype, body):
        self.methodname = methodname
        self.params = params
        self.body = body
        self.inferred_type = returntype

    def infer(self, symboltable, current_class=None, pass_number=1):
        if pass_number == 1:
            symboltable["this"] = current_class
            for param_name, param_type in self.params:
                symboltable[param_name] = param_type
                
        for statement in self.body.children:
            statement.infer(symboltable, current_class, pass_number)

        return self.inferred_type

class Constant(ASTNode):
    def __init__(self, value):
        self.value = value
        self.inferred_type = None

    def infer(self, symboltable, current_class=None, pass_number=1):
        if self.value.startswith("\""):
            self.inferred_type = "String"
        elif self.value == "true" or self.value == "false":
            self.inferred_type = "Bool"
        else:
            self.inferred_type = "Int"
        symboltable[self.value] = self.inferred_type
        return self.inferred_type

class SoloCond(ASTNode):
    def __init__(self, value):
        self.value = value
        self.inferred_type = None

    def infer(self, symboltable, current_class=None, pass_number=1):
        self.inferred_type = self.value.infer(symboltable, current_class, pass_number)
        return self.inferred_type

class Methods(ASTNode):
    def __init__(self, obj, method, args=None):
        self.obj = obj
        self.method = method
        self.args = generate_args(args)

    def infer(self, symboltable, current_class=None, pass_number=1):
        obj_type = self.obj.infer(symboltable, current_class, pass_number)
        method_return_type = symboltable.get(f"{obj_type}:{self.method}", "Nothing")
        self.inferred_type = method_return_type
        return self.inferred_type

class ReturnStatement(ASTNode):
    def __init__(self, value):
        self.value = value
        self.inferred_type = "Nothing"

    def infer(self, symboltable, current_class=None, pass_number=1):
        if self.value:
            self.inferred_type = self.value.infer(symboltable, current_class, pass_number)
        return self.inferred_type

class FieldAssign(ASTNode):
    def __init__(self, obj, value):
        self.obj = obj
        self.name = obj.name
        self.value = value
        self.inferred_type = None

    def infer(self, symboltable, current_class=None, pass_number=1):
        # print("FA",self.value)
        obj_type = self.obj.infer(symboltable, current_class, pass_number)
        value_type = self.value.infer(symboltable, current_class, pass_number)
        field_key = f"{obj_type}.{self.name}"
        symboltable[field_key] = value_type
        self.inferred_type = value_type
        return self.inferred_type

class FieldAccess(ASTNode):
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
        self.inferred_type = None

    def infer(self, symboltable, current_class=None, pass_number=1):
        obj_type = self.obj.infer(symboltable, current_class, pass_number)
        self.inferred_type = symboltable.get(f"{obj_type}.{self.name}", 'Obj')
        return self.inferred_type

class LogicalOperation(ASTNode):
    def __init__(self, operator, left, right=None):
        self.operator = operator
        self.left = left
        self.right = right

    def infer(self, symboltable, current_class=None, pass_number=1):
        ltype = self.left.infer(symboltable, current_class, pass_number)
        rtype = None
        if self.right:
            rtype = self.right.infer(symboltable, current_class, pass_number)
        if ltype != rtype:
            self.inferred_type = "Obj"
        else:
            self.inferred_type = "Bool"
        return self.inferred_type

class NewNode(ASTNode):
    def __init__(self, name, args=None):
        self.args = generate_args(args)
        self.inferred_type = name

    def infer(self, symboltable, current_class=None, pass_number=1):
        if self.inferred_type not in symboltable:
            symboltable[self.inferred_type] = self.inferred_type
        if isinstance(self.args,t.Tree):
            for arg in self.args.children:
                arg.infer(symboltable, current_class, pass_number)
        elif isinstance(self.args,ASTNode):
            self.args.infer(symboltable,current_class,pass_number)
            
        return self.inferred_type

def generate_formal_args(args):
    if args is None:
        return []
    formal_args = []
    for arg in args.children:
        if arg.data == 'formal_arg':
            formal_args.append(arg.children)
    return formal_args

def find_file(start_dir, target_file):
    for root, dirs, files in os.walk(start_dir):
        if target_file in files:
            return os.path.join(root, target_file)
    return None

def generate_args(args):
    if args is None:
        return []
    arglist = []
    if isinstance(args,ASTNode):
        arglist.append(args)
    elif isinstance(args,t.Tree):
        for arg in args.children:
            arglist.append(arg)
    return arglist