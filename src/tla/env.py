from . import util
from .util import GetConvert, analyze, load_source_code
from copy import deepcopy
import traceback
import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')

# A log function that safely handles any type of parameters
def c(*args):
    # Convert all parameters to strings and connect them with spaces
    debug_message = ' '.join(str(arg) for arg in args)
    return debug_message

debug = logging.debug

def DefaultProfileState(name):
    return name+"State"

def DefaultProfileStateInstance(name):
    return name+"Ins"


convert = GetConvert("tla")

PERFORMANCE_VARS = [
    "Time", "Report"
]

NOT_DECLARE_VARS = ["pID"]

UTIL_FUNC = {
    "print": "print(<<{args}>>)",
    "len": "Len({args})",
}

def removeLastLine(s):
    for i in range(len(s)-1, -1, -1):
        if s[i] == "\n":
            return s[:i]
    return s

def removeNewLine(s):
    while s.endswith("\n"):
        s = s[:-1]
    return s

def onlyOneNewLine(s):
    s = removeNewLine(s)
    return s + "\n"

def capitalize(s):
    if len(s) == 0:
        return s 
    return s[0].upper() + s[1:]

def convert_performance(func_name, args):
    if func_name == "Time":
        return "Time(\"now\")"
    if func_name == "Report":
        assert len(args.data) == 2
        return f"__report := [k |-> {convert(args.data[0])}, v |-> {convert(args.data[1])}]"
    return f"{func_name}({convert(args)})"

def add_var_to_dict(d, n, v, raise_error=True):
    if n not in d:
        d[n] = v
        return True
    else:
        # print(d)
        if raise_error:
            raise Exception("Variable %s already defined" % n)
        return False

class Context:
    def __init__(self):
        self.data = {}
        self.data["scope"] = "global"
        self.data["const"] = {}
        self.data["local_const"] = {}
        self.data["global_vars"] = {}
        self.data["type"] = []
        self.data["local_vars"] = {}
        self.data["local_shared_vars"] = {}
        self.data["signature"] = False
        self.data["flags"] = {}
        self.data["add_var"] = False
        self.data["in_macro"] = False
        self.data["macros"] = []
    
    def enterMacro(self, macro):
        self.data["in_macro"] = True 
        if macro not in self.data["macros"]:
            self.data["macros"].append(macro)
    
    def exitMacro(self):
        self.data["in_macro"] = False

    def is_macro(self, name):
        name = name.replace(".", "_")
        return name in self.data["macros"]

    def inMacro(self):
        return self.data["in_macro"]

    def enterAssign(self, init_expr, init_op):
        self.data["init_expr"] = init_expr
        self.data["init_op"] = init_op
    
    def exitAssign(self):
        self.data["init_expr"] = None
        self.data["init_op"] = ""

    def exitAssignInner(self):
        self.data["init_expr_last"] = self.data["init_expr"]
        self.data["init_expr"] = None
    
    def restoreAssign(self):
        self.data["init_expr"] = self.data["init_expr_last"]
        self.data["init_expr_last"] = None

    def enableAddVar(self):
        self.data["add_var"] = True and not self.inMacro()
    
    def disableAddVar(self):
        self.data["add_var"] = False
    
    def canAddVar(self):
        return self.data["add_var"]
    
    def get(self, name):
        return self.data.get(name)
    
    def __setitem__(self, name, value):
        self.data[name] = value
    
    def __getitem__(self, name):
        return self.data[name]
    
    def __delitem__(self, name):
        del self.data[name]

    def add_var(self, name, var, scope=""):
        scope1, var1 = self.get_var(name, scope)
        if var1 != None:
            return True, var1, scope1
        
        if self.data["add_var"] == False:
            return False, var, scope
     
        if scope == "global":
            declared, var = self.add_global_var(name, var)
        if scope == "local_shared":
            declared, var = self.add_local_shared_var(name, var)
        else:
            declared, var = self.add_local_var(name, var)
        return declared, var, scope

    def get_var(self, name, scope=""):
        var = self.get_local_var(name)
        if var == None:
            var = self.get_local_shared_var(name)
            if var == None:
                return "global", self.get_global_var(name)
            return "local_shared", var
        else:
            return "local", var
    

    def set_global_vars(self, global_vars):
        self.data["global_vars"] = global_vars
    
    def get_global_vars(self):
        return self.data.get("global_vars")
    
    def add_global_var(self, name, var):
        if name not in self.data["global_vars"]:
            self.data["global_vars"][name] = var
            var.set_type(self.get_type())
            if self.get_flag("is_const"):
                self.data["const"][name] = var
            return False, var
        return True, self.data["global_vars"][name]

    def get_global_var(self, name):
        return self.data["global_vars"].get(name)
    
    def del_global_var(self, name):
        if name in self.data["global_vars"]:
            del self.data["global_vars"][name]
    
    def add_local_shared_var(self, name, var, typ=None):
        if name not in self.data["local_shared_vars"]:
            self.data["local_shared_vars"][name] = var
            if typ != None:
                var.set_type(typ)
            else:
                var.set_type(self.get_type())
            if self.get_flag("is_const"):
                self.data["const"][name] = var
            return False, var
        return True, self.data["local_shared_vars"][name]
    
    def get_type(self):
        return "Default"
    
    def get_local_shared_vars(self):
        return self.data["local_shared_vars"]
    
    def get_local_shared_var(self, name):
        return self.data["local_shared_vars"].get(name)

    def del_local_shared_var(self, name):
        if name in self.data["local_shared_vars"]:
            del self.data["local_shared_vars"][name]

    def add_local_var(self, name, var, typ=None):
        if var not in self.data["local_vars"]:
            self.data["local_vars"][name] = var
            if typ != None:
                var.set_type(typ)
            else:
                var.set_type(self.get_type())
            if self.get_flag("is_const"):
                self.data["const"][name] = var
            return False, var
        return True, self.data["local_vars"][name]
    
    def get_local_var(self, name):
        return self.data["local_vars"].get(name)

    def del_local_var(self, name):
        if name in self.data["local_vars"]:
            del self.data["local_vars"][name]

    def get_local_vars(self):
        return self.data["local_vars"]


    def enter_func(self, func):
        self.data["func"] = func
        self.data["local_vars"] = {}
        self.data["local_const"] = {}
            
    def exit_func(self):
        self.data["func"] = None
        self.data["local_vars"] = {}
        self.data["local_const"] = {}

    def enter_signature(self):
        self.enableAddVar()
        self.data["signature"] = True
    
    def exit_signature(self):
        self.disableAddVar()
        self.data["signature"] = False
    
    def is_signature(self):
        return self.data["signature"]

    def get_func(self):
        return self.data.get("func")
    
    def backup_global_vars(self):
        self.data["global_vars_backup"] = {}
        self.data["const_backup"] = {}
        for k, v in self.data["global_vars"].items():
            self.data["global_vars_backup"][k] = v
        for k, v in self.data["const"].items():
            self.data["const_backup"][k] = v


    def restore_global_vars(self):
        self.data["global_vars"] = self.data["global_vars_backup"]
        self.data["global_vars_backup"] = {}
        self.data["const"] = self.data["const_backup"]
        self.data["const_backup"] = {}
    
    def enter_profile(self, prof):
        self.backup_global_vars()
        self.data["profile"] = prof
        self.data["scope"] = "profile"
        self.data["local_shared_vars"] = {}
    
    def exit_profile(self):
        self.data["profile"] = None
        self.data["scope"] = "global"
        self.restore_global_vars()
        self.data["local_shared_vars"] = {}

    def get_scope(self):
        if self.data["scope"] == "global":
            return "global"
        if  self.data.get("func") != None:
            return "local"
        if self.data["signature"] == True:
            return "global"
        # print(self.data.get("scope"))
        return "local_shared" 
    
    def is_global_var(self, name):
        # If in the function, and the variable name is a local variable, return False
        if self.data.get("func") != None and name in self.data.get("local_vars"):
            return False
        if self.data.get("scope") == "profile" and name in self.data.get("local_shared_vars"):
            return False
        if name in self.data["global_vars"] and name not in self.data["const"]:
            return True
        return False
    
    def set_flag(self, name, value):
        self.data["flags"][name] = value

    def get_flag(self, name):
        return self.data["flags"].get(name)
    
class SymbolTab:
    def __init__(self) -> None:
        self.table = {}
    
    def add(self, name, type):
        self.table[name] = type

    def get(self, name):
        return self.table[name]
    
    def clear(self):
        self.table = {}
class Indent:
    def __init__(self, indent=4):
        self.indent = indent
        self.level = 0

    def reset(self):
        self.level = 0

    def __enter__(self):
        self.level += 1

    def __exit__(self, *args):
        self.level -= 1

    def __call__(self, s):
        sl = s.split("\n")
        target = "\n".join([" " * self.indent * self.level + i for i in sl])
        return target

indent = Indent()

def convert_list(l, sep=" "):
    if isinstance(l, list):
        return "(" + sep.join(convert_list(x, sep) for x in l) + ")"
    else:
        return convert(l)


class ProfileObject:
    def __init__(self, data, m=None) -> None:
        pass

    def convert(self, indent=indent):
        return ""
    
    def get_name(self):
        return ""
    
    def analyze(self, context=Context()):
        pass
    
    def is_compound(self):
        return False


class Name(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print("Name", data[0], type(data[0].value))
        self.name = data

    def convert(self, indent=indent):
        return self.name

    def get_name(self):
        return self.name

class Number(ProfileObject):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)
        self.data = data[0]
        # print(self.value[0])

    def convert(self, indent=indent):
        return int(self.data)

    def get_name(self):
        return self.data

class KeyValue(ProfileObject):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)
        self.data = data
        self.key = data[0]
        self.value = data[1]

    def analyze(self, context=Context()):
        analyze(self.key, context)
        analyze(self.value, context)

    def convert(self, indent=indent):
        return f"{self.key} = {self.value}"

class Variable(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.type = "Default"
        self.is_profile_var = False
        self.scope = None
        self.profile = None
        self.func = None
        self.init = None
        self.init_op = "="
        self.is_declare = False
        self.is_var = True
    
    def set_type(self, type):
        self.type = type

    def get_scope(self):
        return self.scope
    
    def analyze(self, context=Context()):
        code_scope = context.get_scope() 
        declared, var, scope = context.add_var(self.get_name(), self, code_scope)
        if declared:
            self.type = var.type
        self.scope = scope
        self.var = var
        self.profile = context.get("profile")
        self.func = context.get("func")
        if not declared:
            self.is_declare = True
            self.init = context.get("init_expr")
            self.init_op = context.get("init_op")
            if not context.canAddVar():
                self.is_var = False

    def get_init(self):
        return self.init

    def get_name(self):
        # access the variable (except init)
        n = self.name.get_name()
        # A temporary processing method, which needs to be modified later
        if n == "self":
            return "pID"
        return n

    def convertOld(self, indent=indent):
        name = convert(self.name)
        if self.profile != None:
            # The variable is accessed in the profile
            vars = self.profile.vars
            if name in vars:
                # The variable is declared in the profile
                name = "__" + self.profile.name.get_name() + "_" + name
                if self.func != None:
                    # The variable is declared in the function
                    name = name + "[self]"
            if name in self.profile.procedures:
                name = "__" + self.profile.name.get_name() + "_" + name 
        return name

    def convert(self, indent=indent):
        if self.scope == "local_shared" and self.is_var:
            name = f"{DefaultProfileStateInstance(self.profile.name.get_name())}[pID].{convert(self.name)}"
                # traceback.print_stack()
        else:
            name = self.get_name()
        
        return name


    def to_json(self):
        return self.convert()
        # if self.init != None:
        #     if isinstance(self.init, ProfileObject):
        #         ret = self.init.to_json()
        #     else:
        #         ret = self.init
        # else:
        #     ret = self.convert()
        # return ret

    def init_code(self, init_process=None):
        init_op = self.init_op
        end = ";"
        # print(init_process, self.init_op)
        if init_process:
            self.is_profile_var = True
            process_set = convert(init_process).replace('[', '{').replace(']', '}').replace('\'', '\"')
            # print("init_op", self.init_op)
            if self.init_op == "=":
                target = f"{self.convert()} = [p \in {process_set} |-> {convert(self.init)}];"
            else:
                target = f"{self.convert()} \in [{process_set} -> {convert(self.init)}];"
            # print(target)
            return target
            # op_mapping = {"=": "|->", "\in": ":"}
            # init_op = op_mapping[self.init_op]
            # end = ""
        if type(self.init) == Suite:
            target = ""
            indent = Indent()
            target += f"{self.convert()} {init_op}\n "
            with indent:
                target += f"{indent(self.init.convert())}"
            return target
        return f"{self.convert()} {init_op} {convert(self.init)}{end}"

class Assign(ProfileObject):
    def __init__(self, data, m=None):
        self.m = m
        self.vars = [data[0]]
        self.exprs = [data[1]]
        self.is_expr = False
        # print(self.vars, self.exprs)
        # self.analyze()

    def analyze(self, context=Context()):
        self.func = context.get("func")
        if self.func != None:
            self.in_func = True
        else:
            self.in_func = False
        context.enterAssign(self.exprs[0], "=")
        context.enableAddVar()
        analyze(self.vars[0], context)
        context.disableAddVar()
        analyze(self.exprs[0], context)
        if context.get("op") != None:
            self.is_expr = True
        context.exitAssign()

    def get_var(self):
        return self.vars[0]

    def get_vars_name(self):
        return self.vars[0].get_name()

    def get_expr(self):
        return self.exprs[0]

    def convert(self, indent=indent):
        # env = env_stack.top()
        target_code = ""
        target_code += f"{self.vars[0].convert()}"
        # for var in self.vars:
        #     target_code += f"{convert(var)}, "
        # target_code = target_code[:-2]
        if self.is_expr:
            target_code += " = "
        else:
            # if self.vars[0].init_op != "":
            target_code += " := "
        # for e in self.exprs:
        if type(self.exprs[0]) == FuncCall and self.exprs[0].is_procedure:
            target_code = f"{convert(self.exprs[0])}\nL{self.m.line}:\n" + target_code + "Head(__call_stack[self]);\n"
            target_code += "__call_stack[self] := Tail(__call_stack[self]);\n"
        elif type(self.exprs[0]) == FuncCall and self.exprs[0].is_macro:
            target_code = f"{self.exprs[0].macro_call(self.vars[0].convert())}, "
        else:
            target_code += f"{convert(self.exprs[0])}, "
        if not self.is_expr:
            target_code = target_code[:-2] + ";"
        else:
            target_code = target_code[:-2]
        return target_code
    
class AssignLink(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data[0]
        # print("AssignLink", self.vars, self.exprs)

    def analyze(self, context=Context()):
        analyze(self.data, context)
    
    def convert(self):
        target = self.data.convert()
        if target.endswith(";"):
            target = target[:-1]
        return target + " ||"

class Comparison(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data
        # print("Comparison", self.data, convert(data))
        self.left = data[0]
        self.right = data[2]
        self.op = self.convert_comp_op(data[1][0].value)
        self.m = m

    def analyze(self, context=Context()):
        context["init_expr"] = self.right
        context["init_op"] = self.op
        analyze(self.left, context)
        analyze(self.right, context)

    def convert_comp_op(self, op):
        op_mapping = {
            "==": "=",
            "!=": "/=",
            "in": "\in",
        }
        if op in op_mapping:
            return op_mapping[op]
        else:
            return op

    def get_var(self):
        return self.left

    def is_in_op(self):
        return self.op == "\in"

    def convert(self, indent=indent):
        target = ""
        if type(self.left) == FuncCall and self.left.is_procedure:
            target += f"{convert(self.left)}\nL{self.m.line}:\n"
            if type(self.right) == FuncCall and self.right.is_procedure:
                target += f"{convert(self.left)}\nL{self.m.line}_1:\n"
                target += f"Head(Tail(__call_stack[self])) {self.op} Head(__call_stack[self]);\n"
                target += "__call_stack[self] := Tail(Tail(__call_stack[self]))"
            else:
                target += f"Head(__call_stack[self]) {self.op} {convert(self.right)}"
        else:
            if type(self.right) == FuncCall and self.right.is_procedure:
                target += f"{convert(self.right)}\nL{self.m.line}:\n"
                target += f"{convert(self.left)} {self.op} Head(__call_stack[self]);\n"
                target += "__call_stack[self] := Tail(__call_stack[self])"
            else:
                target += f"{convert(self.left)} {self.op} {convert(self.right)}"
        return target

class Parameters(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data
        self.is_argu = None
        # print(self.data)
        # print(convert(self.data))
    
    def analyze(self, context=Context()):
        self.is_argu = context.get("is_argu")
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=indent):  
        target = ""
        line_end = '\n' if self.is_argu == True else ''
        for a in self.data:
            # print("i",i)
            if a == None:
                continue
            target += f"{convert(a)}, " + line_end
        target = target[:-2-len(line_end)]
        return target

    def fetch_argus_from_stack(self):
        target = ""
        j = 0
        for i, a in enumerate(self.data):
            if a == None:
                continue
            j += 1
            tail = "Tail("*i
            end = ")"*(i+1) + " ||\n"
            target += f"{convert(a)} := Head(" + tail + "__call_stack[name]" + end
        target += "__call_stack[name] := "+ "Tail("*j + "__call_stack[name]" + ")"*j + ";\n"
        return target

class FuncDef(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.m = m
        self.args = data[1] 
        self.local_vars = []
        self.suite = data[3]
        self.def_type = "procedure"
        self.prefixName = ""
        # print("funcdef", convert(self.name), self.args)

    def analyze(self, context=Context()):
        profile = context["profile"]
        if profile != None:
            self.prefixName = profile.get_procedure_name(convert(self.name))
        global_vars = context.get("global_vars")
        context.enter_func(self)
        context["func"] = self
        analyze(self.name, context)
        context["is_argu"] = True
        analyze(self.args, context)
        del context["is_argu"]
        # Analyze all variables that appear in the function body
        # Extract all undefined variables (not in profile.vars)
        analyze(self.suite, context)
        self.local_vars = context.get_local_vars()
        # xdebug(c(self.local_vars))
        context.exit_func()

    def get_suite_statements(self):
        return self.suite.statements
    
    def set_type(self, def_type, prefix=""):
        self.def_type = def_type
        self.prefix = prefix

    def convert(self, indent=indent):
        target = f"{self.def_type} {self.prefixName}(name, pID)\n"
        if len(self.local_vars) > 0:
            target += "variables\n" 
            with indent:
                # args_str = convert(self.args)
                # target += indent(args_str)
                for var in self.local_vars:
                    if var != None and var != "":
                        target += f"{var};"

            target += "\n"
            target += "__Profile = " + convert(self.prefix) + ";\n"
        target += "begin\n"
        with indent:
            if self.args != None:
                target += indent(f"L{self.m.line}:\n" + self.args.fetch_argus_from_stack() + self.suite.convert())
            else:
                target += indent(f"L{self.m.line}:\n" + self.suite.convert())
        if target.endswith(":"):
            # remove last line
            target = removeLastLine(target)
        target += f"\n    return;\nend {self.def_type};"
        return target

    def expand_code(self, pMap, indent=indent):
        target = ""
        target += "variables\n    "
        for var in self.local_vars:
            target += f"{var}, "
        target = target + f"{pMap};\n"
        # target = target[:-2] + ";\n"
        target += "begin\n"
        target += indent(self.suite.convert())
        if target.endswith(":"):
            # remove last line
            target = removeLastLine(target)
        return target
    

class ProcDef(FuncDef):
    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)

class ReturnStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.expr = data
        self.m = m
        # print("return", self.expr)

    def analyze(self, context=Context()):
        analyze(self.expr, context)

    def convert(self, indent=indent):
        target = "__call_stack[name] := <<"
        for expr in self.expr:
            target += convert(expr) + ", "
        if len(self.expr) > 0:
            target = target[:-2] + ">> \o __call_stack[name];\n"
        target += f"\nL{self.m.line}:\nreturn;"
        return target

class OpDef(FuncDef):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

    def analyze(self, context=Context()):
        context = deepcopy(context)
        context["scope"] = "op"
        context["op"] = self
        analyze(self.suite, context)
        profile = context.get("profile")
        if profile != None:
            self.prefix = profile.name.get_name()
    
    def convert(self):
        indent = Indent()
        target = f"{self.prefix}_{convert(self.name)}({convert(self.args)}) == \n"
        with indent:
            target += indent(self.suite.convert())
        return target

class List(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("data", self.data)

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=indent):
        target = "<<"
        for i in self.data:
            target += f"{convert(i)}, "
        if len(self.data) > 0:
            target = target[:-2]
        target += ">>"
        return target
    
    def to_json(self):
        ret = []
        for i in self.data:
            if isinstance(i, ProfileObject):
                ret.append(i.to_json())
            else:
                ret.append(i)
        return ret

class Dict(ProfileObject):
    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)
        self.data = data
        # print(self.data)

    def to_json(self):
        ret = {}
        for key_value in self.data:
            key = key_value[0]
            value = key_value[2]
            if isinstance(value, ProfileObject):
                value = value.to_json()
            ret[key] = value
        return ret
    
    def convert_key(self, key):
        if isinstance(key, str):
            return key
        return convert(key)

    def analyze(self, context=Context()):
        for key_value in self.data:
            analyze(key_value[0], context)
            analyze(key_value[2], context)

    def convert(self, indent=indent):
        target = "["
        for key_value in self.data:
            if key_value[1].value == "->":
                target += f"{self.convert_key(key_value[0])} -> {convert(key_value[2])}, "
            else:
                target += f"{self.convert_key(key_value[0])} |-> {convert(key_value[2])}, "
        if len(self.data) > 0:
            target = target[:-2]
        target += "]"
        if target == "[]":
            target = "[__reserved |-> 0]"
        return target

class Set(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("data", self.data)

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=indent):
        target = "{"
        for i in self.data:
            target += f"{convert(i)}, "
        target = target[:-2]
        target += "}"
        return target
    
    def to_json(self):
        ret = []
        for i in self.data:
            if isinstance(i, ProfileObject):
                ret.append(i.to_json())
            else:
                ret.append(i)
        return ret


class Term(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print("term", data, convert(data))
        self.data = data
        # self.oprand1 = data[0]
        # self.oprand2 = data[-1]
        # if len(data) == 3:
        #     self.op = data[1]
        # elif len(data) > 3:
        #     if data[1].value == "\\":
        #         self.op = data[1].value + data[2].get_name()
        # else:
        #     self.op = "$placeholder"

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)
        # analyze(self.oprand1, context)
        # analyze(self.oprand2, context)

    def convert(self, indent=indent):
        targets = []
        loc = "normal"
        for i in self.data:
            v = ""
            if isinstance(i, ProfileObject):
                v = convert(i)
            elif isinstance(i, float):
                v = str(int(i))
            else:
                v = i.value
            if loc == "normal":
                if v == "\\":
                    loc = "op"
                targets.append(v)
            else:
                targets[-1] += v
                loc = "normal"
        
        stack = []
        for i in targets:
            stack.append(i)
            if len(stack) == 3:
                op2 = stack.pop()
                op = stack.pop()
                op1 = stack.pop()
                if op == "/":
                    stack.append(f"Div({op1}, {op2})")
                else:
                    stack.append(f"{op1} {op} {op2}")
        return stack[0]
                

            
        # target = ""
        # loc = "op1"
        # op = ""
        # op1 = ""
        # for i in self.data:
        #     if loc == "op1":
        #         op1 = i
        #         loc = "op"
        #     elif loc == "op":
        #         if isinstance(i, ProfileObject):
        #             op = op + i.get_name()
        #         else:
        #             op = op + i.value
        #         if op[-1] != "\\":
        #             loc = "op2"
        #     elif loc == "op2":
        #         op2 = i
        #         if op == "/":
        #             target += f"Div({convert(op1)}, {convert(op2)})"
        #         else:
        #             target += f"{convert(op1)} {op} {convert(op2)}"
        #         loc = "op"
        #         op1 = ""
        #         op = ""
        #         op2 = ""
        return "(" + target + ")"

class OrExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class AndExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class XorExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)
        self.data = data
    
    def convert(self, indent=indent):
        return f"({convert(self.data[0])} ^ {convert(self.data[1])})"

class ArithExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class ShiftExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class FThreadpool(ProfileObject):
    def __init__(self, data, m=None) -> None:
        try:
            self.op = data[0].value
            # print(data)
        except Exception as e:
            print("error")
            print(e)
            print(data[0])
        self.data = data[1]
        # print(self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=indent):
        has_space = " " if len(self.op) > 1 else ""
        return f"({self.op}" + has_space + f"{convert(self.data)})"

class Suite(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print(data)
        self.statements = data
        self.is_expr = False

    def analyze(self, context=Context()):
        self.is_expr = context.get("op") != None or context.get("is_expr") == True
        for statement in self.statements:
            analyze(statement, context)

    def convert(self, indent=indent):
        def isAssign(statement):
            if isinstance(statement, Assign):
                return True
            if isinstance(statement, SimpleStmt):
                return statement.simple_assign([Assign])
            return False

        target_code = ""
        for i, statement in enumerate(self.statements):
        # for statement in self.statements:
            try:
                target_code += convert(statement)
                # xdebug(statement, target_code)
                # if len(target_code) > 0 and i < len(self.statements) - 1 and isAssign(statement) and isAssign(self.statements[i+1]):
                #     if target_code.endswith(";"):
                #         target_code = target_code[:-1]
                #     target_code += " ||\n"
                if len(target_code) > 0 and target_code[-1] in ["|"]:
                    target_code += "\n"
                elif len(target_code) > 0 and target_code[-1] not in [";", ":"] and not self.is_expr and not isinstance(statement, LabelStmt):
                    target_code += ";\n"
                elif len(target_code) > 0 and not target_code.endswith("\n"):
                    target_code += "\n"
            except Exception as exp:
                print(exp)
                print(statement)
                traceback.print_exc()
                print("statement", statement, convert(statement))
        target_code = removeNewLine(target_code)
        if target_code.endswith(":"):
            target_code = removeLastLine(target_code)
        return target_code

class AnnAssign(ProfileObject):
    def __init__(self, data, m=None):
        # print("AnnAssign", data)
        self.label = data[1]

    def analyze(self, context=Context()):
        analyze(self.label, context)
    
    def convert(self):
        return f"{convert(self.label)}:"

class LabelStmt(ProfileObject):
    def __init__(self, data, m=None):
        # print("LabelStmt", data)
        self.label = data[0]

    def analyze(self, context=Context()):
        func = context.get("func")
        if func != None:
            self.context = "__"+func.prefixName
        analyze(self.label, context)
    
    def convert(self):
        return f"{convert(self.label)}:"

class AwaitExpr(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data[1]
        # print("await", self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return f"await {convert(self.data)}"

class Slice(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data
        # print("slice", self.data)

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)

    def convert(self):
        return f"({convert(self.data[0])})+1, ({convert(self.data[1])})"

class GetItem(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data
        # print("getitem", self.data)

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)

    def convert(self):
        if self.data[0].is_compound():
            if type(self.data[1]) == Slice:
                return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
            return f"({convert(self.data[0])})[({convert(self.data[1])})+1]"
        if type(self.data[1]) == Slice:
            return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
        # return f"{convert(self.data[0])}[({convert(self.data[1])})+1]"
        return f"{convert(self.data[0])}[({convert(self.data[1])})]"
    
    def to_json(self):
        return self.convert()

class GetAttr(Variable):
    def __init__(self, data, m=None) -> None:
        self.data = data
        self.obj = data[0]
        self.attr = data[1]
        # global_env.add_get_attr(self)
        self.extra_argu = ""
        self.type = "Default"
        self.env = None
        self.libs = None
        self.scope = None
        self.global_access = False
        # self.extra_argu = "" if self.obj.get_name() != "self" else "self"
        self.name = self
        self.declared = True
    
    def analyze(self, context=Context()):
        profile = context.get("profile")
        if profile != None and context.get("scope") == "profile":
            self.env = {"name": profile.name.get_name(), "procedures": profile.procedures}
        self.libs = context.get("libs")
        context.enableAddVar()
        analyze(self.obj, context)
        # if convert(self.obj).startswith("Len"):
        # xdebug(c(self.obj, convert(self.obj)))
        context.disableAddVar()
        analyze(self.attr, context)
        # logging.debug(c(self.obj.get_scope(), isinstance(self.obj, Variable), self.obj))
        if isinstance(self.obj, Variable) and self.obj.get_scope() == "global":
            self.global_access = True
        self.context = context

    # TODO: 增加get_var
    def get_var(self):
        return self
    
    def get_name(self):
        return self.attr.get_name()

    def set_env(self, env):
        self.env = env

    def init_code(self, init_process=False):
        # TODO: Generate initialization code
        init_op = self.init_op
        end = ";"
        if type(self.init) == Suite:
            target = ""
            indent = Indent()
            target += f"{convert(self.name)} {init_op}\n "
            with indent:
                target += f"{indent(self.init.convert())}"
            return target
        return f"{self.convert()} {init_op} {convert(self.init)}{end}"
    
    def convertRead(self, obj):
        return f"Read(\"{obj}\", "

    def convertWrite(self, obj):
        # print("convertWrite", obj)
        return f"Write(\"{obj}\", "

    def splitGetAttr(self):
        action = convert(self.attr)
        obj = convert(self.obj)
        if action == "read":
            return obj, action, self.convertRead(obj)
        elif action == "write":
            return obj, action, self.convertWrite(obj)
        else:
            return obj, action, ""

    def get_global_access(self):
        # print(self.attr.get_name(), self.obj.get_name(), self.global_access)
        return self.global_access
        
    def convert(self):
        attr = convert(self.attr)
        if self.obj.get_name() == "self":
            if attr in self.env.get('procedures'):
                self.extra_argu = "self"
                return f"__{self.env.get('name')}_{convert(self.attr)}"
            return f"__{self.env.get('name')}_{convert(self.attr)}[self]"
        if self.libs != None and self.obj.get_name() in self.libs:
            return f"__{convert(self.obj)}_{convert(self.attr)}"
        # 重写库接口名字
        if self.obj.is_compound():
            return f"({convert(self.obj)}).{convert(self.attr)}"
        return f"{convert(self.obj)}.{convert(self.attr)}"

class FuncCall(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.args = data[1]
        self.is_procedure = False
        self.global_access = False
        self.m = m
        if self.name.get_name() == "TLA":
            self.target = ', '.join(convert(self.args))
            if len(self.target) < 2:
                raise Exception("TLA must have one string arguments")
            else:
                self.target = self.target[1:-1]

            # self.target = convert(self.args)
        else:
            self.target = None
        # print("FuncCall", self.name, self.args)

    def analyze(self, context=Context()):
        # print("analyze func_call", context.get("libs"), self.name)
        profile = context.get("profile")
        context.exitAssignInner()
        context.disableAddVar()
        analyze(self.name, context)
        analyze(self.args, context)
        context.restoreAssign()
        self.is_macro = context.is_macro(convert(self.name))
        #xdebug(c("func_call", self.name, convert(self.name), profile.procedures))
        self.profile = profile
        if profile != None:
            try:
                if type(self.name) == GetAttr:
                    self.is_procedure = convert(self.name.obj) in context.get("libs")
                    self.global_access = self.name.get_global_access()
                else:
                    self.is_procedure = convert(self.name) in profile.procedures
                    self.global_access = False
            except Exception as e:
                debug(c(e))
                self.is_procedure = False   
  
    
    def macro_call(self, var):
        target = ""
        if type(self.name) == GetAttr:
            obj, action, _ = self.name.splitGetAttr()
            # target = f"{convert(self.args.head())} = {target}{', '.join(convert(self.args.tail()))})"
            idxs = ", ".join(convert(self.args))
            if idxs == "":
                args = f"{var}" 
            else:
                args = f"{var}, {idxs}"
            target = f"{obj}_{action}(<<{args}>>)"
            return target
        
        func_name = convert(self.name)
        args = convert(self.args)
        if type(args) == list:
            args = ', '.join([var] + args)
        elif args == "":
            args = var
        else:
            args = f"{var}, {args}"
        
        if func_name in UTIL_FUNC:
            target = UTIL_FUNC[func_name].format(args=args)
        else:
            target = f"{convert(self.name)}({args})"
        return target

    def convert(self, indent=indent):
        if self.target != None:
            return self.target
        target = ""
        if self.is_procedure:
            # print("len", len(self.name.extra_argu), type(self.args))
            target = "__call_stack[self] := <<"
            # if len(self.name.extra_argu) > 0:
            #     target += f"{self.name.extra_argu}, {', '.join(convert(self.args))}>>;\n"
            # else:
            target += f"{', '.join(convert(self.args))}>> \o __call_stack[self];\n"
            prefixName = self.profile.get_procedure_name(convert(self.name))
            target += f"call {prefixName}(self, pID);"
        else:
            if self.global_access:
                obj, action, _ = self.name.splitGetAttr()
                # target = f"{convert(self.args.head())} = {target}{', '.join(convert(self.args.tail()))})"
                idxs = ", ".join(convert(self.args))
                target = f"{obj}_{action}({idxs})"
                return target                
            func_name = convert(self.name)
            if func_name in PERFORMANCE_VARS:
                target = convert_performance(func_name, self.args)
            elif func_name in UTIL_FUNC:
                target = UTIL_FUNC[func_name].format(args=', '.join(convert(self.args)))
            else:
                target = f"{convert(self.name)}({', '.join(convert(self.args))})"
        return target

    def to_json(self):
        return self.convert()

class Comment(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print(self.data)
    def convert(self, indent=indent):
        return ""

class Arguments(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print("Arguments", data, type(data))
        self.data = data

    def analyze(self, context=Context()):
        for arg in self.data:
            analyze(arg, context)
    
    def head(self):
        if len(self.data) > 0:
            return self.data[0]
        logging.warning(c("get head of empty list"))
        return None

    def tail(self):
        if len(self.data) > 1:
            return self.data[1:]
        logging.warning(c("get tail of empty list"))
        return None

    def convert(self):
        return convert(self.data)

class Profile(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.args = data[1]
        self.suite = data[2]

        self.vars = {}
        self.symbols = {}
        self.procedures = {}
        self.operators = {}
        self.instances = []
        self.processes = {}
        self.gen_processes = []

        self.__has_process = False

        # self.analyze()

    def to_json(self):
        ret = {}
        for var in self.vars:
            ret[var] = self.vars[var].to_json()
        return ret

    def analyze(self, context=Context()):
        global_vars = context.get("global_vars")
        pName = self.name.get_name()
        instances = context.get("instances")
        info = instances.get(pName)
        if info != None:
            if info.get("range") != None:
                self.instances = info.get("range").to_json()
                self.instance_type = "range"
            else:
                self.instances = info.get("vars") 
                self.instance_type = "vars"
        else:
            self.instances = []
            self.instance_type = "vars"
        
        for i, k in enumerate(self.instances):
            if isinstance(k, float):
                self.instances[i] = str(int(k))
        

        # Record all variable declarations and initializations
        context.enter_profile(self)
        global_vars = deepcopy(context.get("global_vars"))
        context["profile"] = self
        context["scope"] = "profile"
        for statement in self.suite.statements:
            # print("statement", statement, type(statement), type(statement) == OpDef)
            if type(statement) == Assign or (type(statement) == Comparison and statement.op == "\in"):
                var = statement.get_var()
                # Set the variable type of var to Profile
                if var.get_name() not in global_vars:  
                    self.vars[var.get_name()] = var
                    self.symbols[var.get_name()] = var
            elif type(statement) == FuncDef:
                self.symbols[statement.name.get_name()] = statement
                name = statement.name.get_name()
                if name == "main":
                    self.process = statement
                elif name == "init":
                    self.init = statement
                    self.process_init()
                else:
                    self.procedures[statement.name.get_name()] = statement
            elif type(statement) == OpDef:
                self.operators[statement.name.get_name()] = statement
            elif type(statement) == ProcDef:
                self.process = statement
                # self.process = statement
                self.processes[statement.name.get_name()] = statement
                self.__has_process = True
            else:
                continue

        context.enter_signature()
        analyze(self.args, context)
        context.exit_signature()

        # logging.debug(c("analyze profile", context.get_global_vars(), self.args))
        self.global_vars = context.get_global_vars()
        for statement in self.suite.statements:
            analyze(statement, context)
        self.local_shared_vars = context.get_local_shared_vars()
        context.exit_profile()


    def get_procedure_name(self, pName):
        if pName in self.procedures:
            return "__" + self.name.get_name() + "_" + pName
        # else:
        #     logging.error(f"procedure {pName} is not defined")
        return "Error"
    


    def has_process(self):
        return self.__has_process

    # Return all variable initialization code
    def get_vars_declare(self):
        target = ""
        for name in self.vars:
            var = self.vars[name]
            if var.type == "Default":
                target += f"{var.init_code(init_process=self.instances)}\n"
        if len(target) > 1:
            target = target[:-2]
        # logging.debug(target)
        return target
    # TODO: Delete init
    def process_init(self):
        def is_init(obj):
            if type(statement) == Assign or (type(statement) == Comparison and statement.op == "\in"):
                return True
            if type(statement) == GetAttr and convert(statement.obj) == "self" and type(statement.attr) == Name:
                return True
            return False
        statements = self.init.get_suite_statements()
        for statement in statements:
            # print("statement", statement, type(statement), type(statement) == OpDef)
            # TODO: Add code for GetAttr
            if is_init(statement):
                var = statement.get_var()  
                statement.set_init()                         
                self.vars[var.get_name()] = var
                self.symbols[var.get_name()] = var


    def __convert_process_header(self, profile_name, process_name):
        instances = ""
        if self.instance_type == "range":
            instances = "\", \"".join([self.convertProcessIns(i, process_name) for i in self.instances])
            instances = "\in {\"" + instances + "\"}"
        else:
            instances = "\", \"".join(self.instances)
            instances = "\in {\"" + instances + "\"}"
        target = f"process {self.convertProcessIns(profile_name, process_name)} {instances}"
        return target
    
    def get_process_instances(self):
        process_name = [p for p in self.processes]
        # xdebug(c(self.instance_type, self.instances, type(self.instances), process_name))
        process_instances = []
        for i in self.instances:
            for p in process_name:
                process_instances.append(self.convertProcessIns(i, p))
        return process_instances
    
    def convertProcessIns(self, pName, procName):
        if isinstance(pName, float):
            pName = str(pName)
        return pName + capitalize(procName)

    def getPMap(self, process_name):
        pMap = "pMap=["
        if self.instance_type == "range":
            for i in self.instances:
                pMap += f"{self.convertProcessIns(i, process_name)} |-> {i},"
            if len(self.instances) > 0:
                pMap = pMap[:-1] + f"], pID=pMap[self]"
        else:
            pass
        return pMap 
    
    def convert_process(self, indent=indent):
        target = ""
        profile_name = self.name.get_name() 
        for proc_name in self.processes:
            proc = self.processes[proc_name]
            process_name = proc.name.get_name()
            gen_proc_name = self.convertProcessIns(profile_name, process_name)
            self.gen_processes.append(gen_proc_name)
            target += self.__convert_process_header(profile_name, process_name) + "\n"
            pMap = self.getPMap(process_name)
            with indent:
                target += proc.expand_code(pMap) + "\n"
            target += "end process;\n\n"
        target = onlyOneNewLine(target)
        return target
    
    def convert_global_procedures(self):
        target = ""
        for procedure in self.procedures:
            self.procedures[procedure].set_type("procedure", "__"+self.name.get_name())
            target += convert(self.procedures[procedure]) + "\n\n"
        if len(target) > 2:
            target = target[:-2]
        return target

    def convert_global_operators(self):
        target = ""
        for operators in self.operators:
            target += convert(self.operators[operators]) + "\n\n"
        if len(target) > 2:
            target = target[:-2]
        return target

    def defaultProfileState(self):
        return DefaultProfileState(self.get_name())
    
    def defaultProfileStateInstance(self):
        return DefaultProfileStateInstance(self.get_name())
    
    def get_instances(self):
        ins = ""
        if self.instance_type == "range":
            ins = str(self.instances).replace("'", "").replace("[", "{").replace("]", "}")
        else:
            ins = "\", \"".join(self.instances)
        ## xdebug(c(ins, self.instance_type, self.instances, type(self.instances)))
        return ins
    
    def genDefaultProfileState(self):
        target = "["
        for varName in self.local_shared_vars:
            target += f"{varName} |-> {convert(self.local_shared_vars[varName].get_init())},"
            # xdebug(c(self.local_shared_vars[varName], convert(self.local_shared_vars[varName].init)))
        if len(self.local_shared_vars) > 0:
            target = target[:-1] 
        # xdebug(c(target))
        return target + "]"

    def get_name(self):
        return self.name.get_name()
    
    def convert_local_shared_declare(self):
        target = ""
        if self.local_shared_vars == None or len(self.local_shared_vars) == 0:
            return target 
        target += f"{self.defaultProfileStateInstance()} = [r \in {self.get_instances()} |-> {self.genDefaultProfileState()}]"
        # xdebug(c(self.genDefaultProfileState()))
        return target


class Condition(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        self.m = m

    def analyze(self, context=Context()):
        # print("condition", self.data)
        analyze(self.data, context)

    def convert(self, indent=indent):
        target = ", ".join(convert(self.data))
        return target

class QuantifierExpr(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print("quantifier", data, convert(data))
        # self.data = data
        self.quantifier = data[0]
        self.conditions = data[1]
        # self.expr = data[2]

    def is_compound(self):
        return True

    def analyze(self, context=Context()):
        # print("quantifier expr", self.data)
        analyze(self.quantifier, context)
        analyze(self.conditions, context)

    def convert(self, indent=indent):
        # return self.data
        target = ""
        target += f"{convert(self.quantifier)}: "
        target += f"{convert(self.conditions)}, "
        return target[:-2]
        # print("QuantifierExpr", convert(self.quantifier), convert(self.condition))
        # return f"({convert(self.quantifier)}: {convert(self.condition)})"

class QuantifierItem(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("quantifier item", data, self.convert())

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=indent):
        target = ""
        for i in self.data:
            if type(i) == str:
                target += i + " "
            elif isinstance(i, Name):
                target += i.get_name() + ", "
            elif isinstance(i, Set) or isinstance(i, Variable) or isinstance(i, Range) or isinstance(i, FuncCall):
                target = target[:-2] + " \in " + i.convert() + ", "
        target = target[:-2]
        return target

class IfStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print(self.data)
        self.condition = data[0]
        self.suite = data[1]
        self.elifs = data[2]
        if len(data) > 3:
            self.else_suite = data[3]
        else:
            self.else_suite = None
        self.is_expr = False

    def analyze(self, context=Context()):
        self.is_expr = context.get("is_expr") != None or context.get("op") != None
        analyze(self.condition, context)
        analyze(self.suite, context)
        analyze(self.elifs, context)
        analyze(self.else_suite, context)

    def convert(self, indent=indent):
        # env = env_stack.top()
        indent = Indent()
        if self.is_expr:
            if_k = "IF"
            then_k = "THEN"
            else_k = "ELSE"
            end_k = ""
        else:
            if_k = "if"
            then_k = "then"
            else_k = "else"
            end_k = "end if;"

        target = f"{if_k} {convert(self.condition)} {then_k}\n"
        with indent:
            target += indent(self.suite.convert())
            target = removeNewLine(target)
            if target.endswith(":"):
                target = removeLastLine(target)
            # target += "\n"
        if self.elifs != None:
            elif_code = convert(self.elifs)
            if len(elif_code) > 0:
                target += "\n" + convert(self.elifs) + "\n"
        if self.else_suite:
            else_code = self.else_suite.convert()
            if len(else_code) > 0:
                if not target.endswith("\n"):
                    target += "\n"
                target += f"{else_k}\n"
                with indent:
                    target += indent(else_code) + "\n"
        if not target.endswith("\n"):
            target += "\n"
        target += f"{end_k}"
        return target

class ComprehensionVar(Assign):
    def __init__(self, data, m=None):
        self.var = data[0]
        self.suite = data[1]
    
    def analyze(self, context=Context()):
        context = deepcopy(context)
        context["init_expr"] = self.suite
        context["is_expr"] = True
        analyze(self.var, context)
        analyze(self.suite, context)

    # def set_init(self):
    #     self.var.set_init(self.suite)

    def convert(self):
        # env = Env()
        # env.set("is_expr", True)
        # env_stack.push(env)
        indent = Indent()
        target = ""
        target += convert(self.var) + " = \n"
        with indent:
            target += indent(self.suite.convert()) + "\n"
        # env_stack.pop()
        return target


class LetStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.let = data[0]
        self.in_expr = data[1]
        # print("let", self.let)

    def analyze(self, context=Context()):
        context = deepcopy(context)
        context["is_expr"] = True
        analyze(self.let, context)
        analyze(self.in_expr, context)
    
    def convert(self):
        indent = Indent()
        target = f"LET\n"
        with indent:
            target += indent(self.let.convert()) + "\n"
        target += f"IN\n"
        with indent:
            target += indent(self.in_expr.convert())
        return target

class Elifs(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("elif\n", self.convert())

    def analyze(self, context=Context()):
        for elif_ in self.data:
            analyze(elif_[0], context)
            analyze(elif_[1], context)

    def convert(self, indent=indent):
        target = ""
        indent = Indent()
        for elif_ in self.data:
            target += f"elsif {convert(elif_[0])} then\n"
            with indent:
                target += indent(convert(elif_[1])) + "\n"
        return target[:-1]

class WhileStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.condition = data[0]
        self.suite = data[1]

    def analyze(self, context=Context()):
        analyze(self.condition, context)
        analyze(self.suite, context)

    def convert(self):
        indent = Indent()
        # print("convert", self.condition, self.condition.data)
        target = "while " + convert(self.condition) + " do\n"
        with indent:
            target += indent(convert(self.suite))
        target = removeNewLine(target)
        if target.endswith(":"):
            target = removeLastLine(target)
        target += "\nend while;"
        return target

class WithItem(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]
        # print("with item", self.convert())

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return convert(self.data)

class WithItems(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("with items", self.convert())

    def analyze(self, context=Context()):
        for item in self.data:
            analyze(item, context)

    def convert(self):
        target = ""
        for item in self.data:
            target += convert(item) + ", "
        return target[:-2]

class WithStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        self.items = data[0]
        self.suite = data[1]

    def analyze(self, context=Context()):
        analyze(self.items, context)
        analyze(self.suite, context)

    def convert(self):
        indent = Indent()
        target = "with " + convert(self.items) + " do\n"
        with indent:
            target += indent(convert(self.suite)) + "\n"
        target += "end with;"
        return target

class EitherClause(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.suite = data[0]

    def analyze(self, context=Context()):
        analyze(self.suite, context)

    def convert(self):
        target = "or\n"
        indent = Indent()
        with indent:
            target += indent(convert(self.suite)) + "\n"
        return target[:-1]

class EitherStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        self.suite = data[0]
        self.either = data[1]

    def analyze(self, context=Context()):
        analyze(self.suite, context)
        for i in self.either:
            analyze(i, context)

    def convert(self):
        indent = Indent()
        target = "either\n"
        with indent:
            target += indent(convert(self.suite)) + "\n"
        for i in self.either:
            target += indent(convert(i)) + "\n"
        target += "end either;"
        return target

class RawCode(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data

    def convert(self):
        return self.data

    def analyze(self, context=Context()):
        analyze(self.data, context)

class Range(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)

    def convert(self):
        return convert(self.data[0]) + ".." + convert(self.data[1])

class LogicTest(ProfileObject):
    def __init__(self, data, op) -> None:
        self.data = data
        self.op = op

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self):
        target = ""
        for i in self.data:
            target += convert(i) + self.op
        return "(" + target[:-4] + ")"

class AndTest(LogicTest):
    def __init__(self, data, m=None) -> None:
        super().__init__(data, " /\\ ")
    
class OrTest(LogicTest):
    def __init__(self, data, m=None) -> None:
        super().__init__(data, " \\/ ")

class NotTest(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]
        # print(self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        # return "~"
        return "~" + convert(self.data)

class AssertStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        target = convert(self.data)
        statements = target.split("\n")
        statements[-1] = "assert " + statements[-1] + ";"
        target = "\n".join(statements)
        return target


class DottedName(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return convert(self.data)
class DottedAsName(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return convert(self.data)

class DottedAsNames(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return convert(self.data)

class ImportName(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return convert(self.data)

class ImportStmt(ProfileObject):
    def __init__(self, data, m) -> None:
        self.data = data[0]
        self.m = m
        self.libs = convert(self.data)
        # print("import", self.libs)
        debug(c(data))
    
    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return ""

class ExtendName(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return convert(self.data)

class ExtendStmt(ProfileObject):
    def __init__(self, data, m) -> None:
        self.data = data[0]
        self.m = m
        self.libs = convert(self.data)
    
    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return ""

class FileInput(ProfileObject):
    def __init__(self, data, m=None, tranformer=None, parse=None) -> None:
        self.statements = data
        self.transformer = tranformer
        self.parser = parse
        self.extends = "EXTENDS Integers, TLC, Sequences"
        self.macros = []
        self.symbols = {}
        self.vars = {}
        self.prof_vars = {}
        self.profiles = {}
        self.libs = {}
        self.extends_libs = {}
        self.constVars = []
        self.is_anonymous = False
        self.analyze()

    def __auto_default_var(self):
        # If there is no profile variable, automatically define
        if self.prof_vars == {}:
            for profile in self.profiles:
                # create var
                var_name = profile + "_var"
                var = Variable(var_name)
                var.set_type("Profile")
                self.prof_vars[var_name] = var
                self.profiles[profile]["vars"].append(var_name)
                self.vars[var_name] = var
                self.symbols[var_name] = var

    def analyze(self):
        context = Context()
        # Get all the declarations of main
        for statement in self.statements:
            if isinstance(statement, MacroDef):
                self.macros.append(statement)
            if isinstance(statement, SimpleStmt):
                statement = statement.extract()

            if isinstance(statement, Profile):
                name = statement.name.get_name()
                add_var_to_dict(self.profiles, name, {"profile_declare": statement, "vars": [], "range": None})
                add_var_to_dict(self.symbols, name, statement)

            if isinstance(statement, Assign):
                var = statement.get_var()
                analyze(statement, context)
                if isinstance(statement.exprs[0], FuncCall):
                    called = statement.exprs[0].name.get_name()
                    # print(called in self.symbols, self.symbols)
                    if called in self.symbols:
                        called_obj = self.symbols[called]
                        if isinstance(called_obj, Profile):
                            var.set_type("Profile")
                            self.prof_vars[var.get_name()] = var
                            self.profiles[called_obj.name.get_name()]["vars"].append(var.get_name())        
                self.vars[var.get_name()] = var
                self.symbols[var.get_name()] = var         
            if isinstance(statement, Comparison) and statement.op == "\in":
                var = statement.get_var()
                analyze(statement, context)
                var_name = var.get_name()
                if var_name in self.profiles:
                    self.prof_vars[var_name] = var
                    self.profiles[var_name]["range"] = statement.right
                    self.is_anonymous = False
                else:
                    self.vars[var.get_name()] = var
                    self.symbols[var.get_name()] = var

            if isinstance(statement, ImportStmt):
                for lib in statement.libs:
                    self.libs[lib] = None

            if isinstance(statement, ExtendStmt):
                for lib in statement.libs:
                    self.extends_libs[lib] = None

            if isinstance(statement, ConstAssign):
                self.constVars.append(statement)

            
        self.__parse_libs()

        self.__auto_default_var()
        
        context["global_vars"] = self.vars
        context["instances"] = {}
        for pName in self.profiles:
            context["instances"][pName] = {"range": self.profiles[pName].get("range"), "vars": self.profiles[pName].get("vars")}
        context["libs"] = list(self.libs.keys())
        for statement in self.statements:
            analyze(statement, context)

    def __parse_libs(self):
        for lib in self.libs:
            if lib in self.libs and self.libs[lib] is not None:
                continue
            try: 
                source_code = load_source_code(lib)
                lib_profile = self.transformer().transform(self.parser(source_code))
                self.libs[lib] = lib_profile
                self.libs = {**self.libs, **lib_profile.libs}
            except Exception as e:
                print("lib ", lib, " failed")
                print(e)

    def to_json(self):
        result = {}
        for name in self.profiles:
            profile = self.profiles[name]
            result[name] = profile["profile_declare"].to_json()
        return result

    def convert(self, indent=indent, module="main"):
        indent.reset()
        # Generate Module head
        target = "------------------------------- MODULE " + module + " -------------------------------\n"
        # Generate Extends module statement
        target += self.extends + "\n"
        target += util.newline(self.__convert_extends(), n=1) + "\n"
        target += util.newline(self.__convert_const(), n=1)
        target += "\n"
        # Generate algorithm statement
        target += "(*--algorithm " + module + "\n"
        # Generate global variable declaration
        target += util.newline(self.__convert_global_variables(), n=1)
        target += util.newline(self.__convert_operators(), n=1)
        target += util.newline(self.__convert_macros(), n=1)
        target += util.newline(self.__convert_procedures(), n=1)
        target += util.newline(self.__convert_process(), n=1)
        target += "end algorithm;*)\n"
        target += "============================================================================="
        self.target = target
        return target

    def convert_variables(prof, indent=indent):
        # xdebug(c(prof, prof.vars))
        if prof is None:
            print("prof is None")
            return ""
        target = ""
        for name in prof.vars:
            var = prof.vars[name]
            if var.type == "Default" and var.get_name() not in NOT_DECLARE_VARS:
                target += f"{var.init_code()}" + "\n"

        if len(target) > len(";\n"):
            target = target[:-1]
        else:
            target = ""
        return target
    
    def __convert_const(self, indent=indent):
        target = ""
        for statement in self.constVars:
            target += convert(statement) + "\n"
        return target
    
    def __convert_extends(self, indent=indent):
        target = ""
        for lib in self.extends_libs:
            code = load_source_code(lib, ".tla")
            target += code + "\n"
        return target
    
    def __convert_global_variables(self, indent=indent):
        target = "variables\n"
        proc_instances = set()
        with indent:
            var_str = FileInput.convert_variables(self, indent)
            if len(var_str) > 0:
                target += indent(var_str) + "\n"
            if not self.is_anonymous:
                for name in self.profiles:
                    profile = self.profiles[name]
                    proc_instances = proc_instances | set(profile["profile_declare"].get_process_instances())
                proc_instances = str(proc_instances).replace("'", '"')
                target += indent(f"__call_stack = [p \in {proc_instances} |-> <<>>];") + "\n"
            target += indent(f"__path = 0;") + "\n"
            for name in self.profiles:
                profile = self.profiles[name]
                local_shared_declare = f"{profile['profile_declare'].convert_local_shared_declare()}"
                if len(local_shared_declare) > 0:
                    target += f"{indent(local_shared_declare)}" + ";\n"
            for lib in self.libs:
                lib_profile = self.libs[lib]
                target += indent("\* Variables from " + lib) + "\n"
                target += indent(FileInput.convert_variables(lib_profile)) + "\n"
        return target[:-1]

    def __convert_operators(self):
        indent = Indent()
        target = "define\n"
        with indent:
            for name in self.profiles:
                op_target = self.profiles[name]["profile_declare"].convert_global_operators()
                if op_target == "":
                    continue
                target += indent(op_target) + "\n"
        if target == "define\n":
            return ""
        target += "end define;"
        return target
    
    def __convert_macros(self):
        target = "\n"
        for m in self.macros:
            target += convert(m) + "\n"
        return target

    def convert_procs(obj):
        if obj is None:
            return ""
        target = ""
        for name in obj.profiles:
            profile = obj.profiles[name]
            target += profile["profile_declare"].convert_global_procedures() + "\n"
        return target

    def __convert_procedures(self):
        target = FileInput.convert_procs(self)
        for name in self.libs:
            lib = self.libs[name]
            target += FileInput.convert_procs(lib)
        return target

    def __convert_process(self, indent=indent):
        target = ""
        for name in self.profiles:
            profile = self.profiles[name]
            if profile["profile_declare"].has_process():
                target += profile["profile_declare"].convert_process() + "\n"
        return target

class Newline(ProfileObject):
    def convert(self, indent=indent):
        return ""
    
class ConstAssign(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data[0]
        self.m = m

    
    def convert(self, indent=indent):
        target = ""
        var = self.data.get_var()
        expr = self.data.get_expr()
        if var != None and expr != None:
            target = f"{convert(var)} == {convert(expr)}"

        return target
 

class SimpleStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data

    def simple_assign(self, types):
        for i in self.data:
            for type in types:
                if isinstance(i, type):
                    return i
        return None
    
    def extract(self):
        if len(self.data) >= 1:
            return self.data[0]
        return self
    
    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)
    
    def convert(self, indent=indent):
        target = ""
        for i in self.data:
            # print("simplestmt item", i, convert(i))
            convi = convert(i)
            if len(convi) > 0:
                target += convi + "\n"
        if len(target) > 0 and target[-1] == "\n":
            target = target[:-1]
        # print("simplestmt convert", target)
        return target 

class Process(ProfileObject):
    pass

class MacroDef(FuncDef):
    def __init__(self, data, m=None) -> None:
        self.data = data
        self.m = m
        self.mName = self.data[0]
        self.mParams = self.data[1]
        self.mSuite = self.data[3]

    def analyze(self, context=Context()):
        context.enterMacro(convert(self.mName))
        analyze(self.data, context)
        context.exitMacro()
        
    def convert(self):
        indent = Indent()
        target = f"macro {convert(self.mName)} ({convert(self.mParams)}) begin" + "\n"
        with indent:
            target += indent(convert(self.mSuite)) + "\n"
        target += "end macro;"
        return target

class MODULE(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data