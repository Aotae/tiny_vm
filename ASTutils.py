import os
import lark.tree as t
PRIMITIVES = ["String","Obj","Int","Bool","Nothing"]
class ASTNode:
    def __init__(self):
        pass
    def infer(self, symboltable):
        pass

class Conditional(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        self.inferred_type = "Obj"
        self.identifier = f"{left}{operator}{right}"
        
    def infer(self, symboltable):
        ltype = self.left.infer(symboltable)
        rtype = self.right.infer(symboltable)
        if ltype != rtype:
            # same thing as binary ops, do lca
            self.inferred_type = "Obj"
            symboltable[self.identifier] = self.inferred_type
        else:
            self.inferred_type = "Bool"
            symboltable[self.identifier] = ltype
        # for now if the two types match return a bool
        return self.inferred_type

class IfStatement(ASTNode):
    def __init__(self, condition, body, elsebody=None):
        self.condition = condition
        self.elsebody = elsebody
        self.body = body
          
    def infer(self, symboltable):

        if isinstance(self.condition, t.Tree):
            for expr in self.condition.children:
                expr.infer(symboltable)
        elif isinstance(self.conditon, ASTNode):
            self.conditon.infer(symboltable)
        # print(self.body)
        # print(self.elsebody.children)
        if isinstance(self.body, t.Tree):
            for statement in self.body.children:
                if isinstance(statement, ASTNode):
                    statement.infer(symboltable)
        elif isinstance(self.body, ASTNode):
            self.body.infer(symboltable)

        # if self.elifbodies != None:
        #     if isinstance(self.elifbodies,t.Tree):
        #         for elifbody in self.elifbodies.children:
        #             if isinstance(elifbody.body):
        #                 pass
        #     elif isinstance(self.elifbodies, ASTNode):
        #         pass
                
        if isinstance(self.elsebody, t.Tree):
            # print(self.elsebody.children)
            for statement in self.elsebody.children:
                if isinstance(statement, ASTNode):
                    statement.infer(symboltable)
        elif isinstance(self.elsebody, ASTNode):
            self.elsebody.infer(symboltable)
                   
class WhileStatement(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def infer(self, symboltable):
        condition_type = self.condition.infer(symboltable)
        if condition_type != "Bool":
            raise ValueError("Condition expression in while loop must evaluate to boolean type")
        
        if isinstance(self.body, t.Tree):
            for statement in self.body.children:
                if isinstance(statement, ASTNode):
                    statement.infer(symboltable)
                    
        elif isinstance(self.body, ASTNode):
            self.body.infer(symboltable)
                     
class Assignment(ASTNode):
    def __init__(self, name, value, t_type="NULL"):
        self.inferred_type = None
        self.name = name
        self.value = value
    def infer(self, symboltable):
        # print(self.value)
        self.inferred_type = self.value.infer(symboltable)
        # check if name is alreadyin table
        if self.name in symboltable:
            # do LCA
            existing_type = symboltable[self.name]
            # print("existing type:",existing_type)
            if (existing_type != self.inferred_type):
                # for now just assume LCA is Obj since thats really the only ancestor for all types right now
                # print("we got here")
                self.inferred_type = "Obj"
                                 
        symboltable[self.name] = self.inferred_type
        # print("final type:",self.inferred_type)
        # print("symbol table var value:", symboltable[self.name])
        return self.inferred_type
        
class BinaryOperation(ASTNode):
    def __init__(self, left, operator, right):
        # print(left)
        self.left = left
        self.operator = operator
        self.right = right
        # kinda hacky 
        self.inferred_type = "Obj"
        self.identifier = f"{left}{operator}{right}"
    def infer(self,symboltable):
        ltype = self.left.infer(symboltable)
        rtype = self.right.infer(symboltable)

        if ltype == rtype:
            symboltable[self.identifier] = ltype
            self.inferred_type = ltype
        else:
            # do LCA... uh for now just return Obj I guess.. the most common ancestor?
            symboltable[self.identifier] = self.inferred_type
            return self.inferred_type
        
        return self.inferred_type

class ClassDeclaration(ASTNode):
    def __init__(self, name, args, extends, body):
        self.name = name
        self.args = generate_formal_args(args)
        self.extended = extends
        self.body = body
        self.inferred_type = name
        self.methods = set()
        self.fields = set()
        
    def infer(self, symboltable):
        symboltable[self.name] = self.inferred_type
        if isinstance(self.body, t.Tree):
            for statement in self.body.children:
                if isinstance(statement,FieldAssign):
                    self.fields.add(statement.infer(symboltable))
                if isinstance(statement,MethodDeclaration):
                    self.methods.add(statement.infer(symboltable))
                if isinstance(statement, ASTNode):
                    statement.infer(symboltable)

                        
        elif isinstance(self.body, ASTNode):
            self.body.infer(symboltable)
        # print(self.methods)
        return self.inferred_type

class MethodDeclaration(ASTNode):
    def __init__(self, methodname, params, returntype, body):
        self.methodname = methodname
        self.params = params
        self.body = body
        self.return_type = returntype
        self.inferred_type = "Method"
        
    def infer(self, symboltable):
        if isinstance(self.body, t.Tree):
            for statement in self.body.children:
                if isinstance(statement, ASTNode):
                    statement.infer(symboltable)
        elif isinstance(self.body, ASTNode):
            self.body.infer(symboltable)
        # print(self.methodname)
        return self.methodname

class Variable(ASTNode):
    def __init__(self, name):
        self.name = name
        self.inferred_type = None
    def infer(self,symboltable):
        # get the type from the symbol table, if dne return Obj
        self.inferred_type = symboltable.get(self.name,'Obj')
        return self.inferred_type
        
class Constant(ASTNode):
    def __init__(self, value):
        # so value in this case is a lark lexed token, if I want to do type inference logic here I gotta be able to tell what's a string and whats an int 
        self.value = value
        self.inferred_type = None
    def infer(self, symboltable):
        # this feels kind of hacky but since consts can only be strings or ints this should work
        # especially since the grammar won't allow strings that don't start with and end with quotes
        if(self.value.startswith("\"")):
            self.inferred_type = "String"
            symboltable[self.value] = self.inferred_type
            return "String"
        elif(self.value == "true" or self.value == "false"):
            self.inferred_type = "Bool"
            symboltable[self.value] = self.inferred_type
            return "Bool"
        else:
            self.inferred_type = "Int"
            symboltable[self.value] = self.inferred_type
            return "Int"
        symboltable[self.value] = "Obj"
        return "Obj"

class SoloCond(ASTNode):
    def __init__(self, value):
        self.value = value
        self.inferred_type = None
    def infer(self,symboltable):
        self.inferred_type = self.value.infer(symboltable)
        return self.inferred_type
                      
class Methods(ASTNode):
    def __init__(self, obj, method, args=None):
        # print(obj)
        self.obj = obj
        self.method = method
        self.args = args
        
    def infer(self,symboltable):
        # should methods have types? the things they return should have a type if it isn't a method 
        # uhh for now pass the variable type and if the var is not in the table we have other problems
        return symboltable.get(self.obj,"Obj")

class ReturnStatement(ASTNode):
    def __init__(self, value):
        print(value)
        self.value = value
        
    def infer(self,symboltable):
        return self.value.infer(symboltable)
        
class FieldAssign(ASTNode):
    def __init__(self, obj, value):
        self.obj = obj
        self.name = obj.name
        self.value = value
        self.inferred_type = None
        
    def infer(self, symboltable):
        obj_type = self.obj.infer(symboltable)
        value_type = self.value.infer(symboltable)
        symboltable[f"{obj_type}.{self.name}"] = value_type
        self.inferred_type = value_type
        return self.name

class FieldAccess(ASTNode):
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
        self.inferred_type = None
        
    def infer(self, symboltable):
        obj_type = self.obj.infer(symboltable)
        self.inferred_type = symboltable.get(f"{obj_type}.{self.name}", 'Obj')
        return self.name
        
class LogicalOperation(ASTNode):
    def __init__(self, operator, left, right=None):
        self.operator = operator
        self.left = left
        self.right = right
        
    def infer(self,symboltable):
        ltype = self.left.infer(symboltable)
        rtype = None
        if self.right != None:
            rtype = self.right.infer(symboltable)
        if ltype != rtype:
            # same thing as binary ops, do lca
            self.inferred_type = "Obj"
        else:
            self.inferred_type = "Bool"
        return self.inferred_type
        
class NewNode(ASTNode):
    def __init__(self, name, args):
        self.type = name
        self.args = args
        
    def infer(self,symboltable):
        return self.type
    
def generate_formal_args(args):
    if args is None:
        return []
    
    formal_args = []
    for arg in args.children:
        if arg.data == 'formal_arg':
            formal_args.append(arg.children[0])
    
    return formal_args

def find_file(start_dir, target_file):
    # Iterate over all files and directories in the start directory
    for root, dirs, files in os.walk(start_dir):
        # Check if the target file exists in the current directory
        if target_file in files:
            # Construct the full path to the target file
            file_path = os.path.join(root, target_file)
            return file_path  # Return the path to the file

    # If the file is not found in any directory
    return None