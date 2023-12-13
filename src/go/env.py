from . import util
from .util import GetConvert, analyze, load_source_code, load_json
from copy import deepcopy
import traceback
import re
import json

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

convert = GetConvert("go")

def DefaultProfileState(name):
    return name+"State"

def DefaultProfileStateInstance(name):
    return name+"Ins"


PERFORMANCE_VARS = [
    "Time", "Report"
]

UTIL_FUNC = {
    "Append": "append",
    "print": "// fmt.Println",
    "Actor": "stdp.Actor",
    "Len": "len",
}

def typedConvert(obj):
    if obj is None:
        return ""
    if hasattr(obj, 'convert'):
        return obj.typedConvert()
    elif isinstance(obj, list):
        obj = [typedConvert(x) for x in obj]
        return obj
        # target = ""
        # for x in obj:
        #     target += typedConvert(x) + ", "
        # if len(target) > 0:
        #     target = target[:-2]
        # target = "tla.MakeTLASet(" + target + ")"
        # return target
    elif isinstance(obj, tuple):
        target = ""
        for x in obj:
            target += typedConvert(x) + ", "
        if len(target) > 0:
            target = target[:-2]
        target = "tla.MakeTLATuple(" + target + ")"
        return target
    elif isinstance(obj, dict):
        return {typedConvert(k): typedConvert(v) for k, v in obj.items()}
    elif isinstance(obj, bool):
        return f"tla.MakeTLABool({str(obj).lower()})"
    elif isinstance(obj, int):
        return f"tla.MakeTLANumber(int({str(obj)}))"
    elif isinstance(obj, float):
        # PlusCal does 
        # print("float", obj)
        return f"tla.MakeTLANumber(int({str(obj)}))"
    elif isinstance(obj, str):
        return f"tla.MakeTLAString(\"{obj}\")"
        # return f"\"{obj}\""
    else:
        # print("convert", obj, type(obj), hasattr(obj, "convert"))
        return str(obj)
class Context:
    def __init__(self):
        self.data = {}
        self.data["scope"] = "global"
        self.data["annotation_context"] = AnnContext()
        self.data["const"] = {}
        self.data["local_const"] = {}
        self.data["global_vars"] = {}
        self.data["annotation_context"] = AnnContext()
        self.data["type"] = []
        self.data["local_vars"] = {}
        self.data["local_shared_vars"] = {}
        self.data["signature"] = False
        self.data["flags"] = {}
        self.data["locks"] = False 

        self.data["add_var"] = False

    def enableAddVar(self):
        self.data["add_var"] = True
    
    def disableAddVar(self):
        self.data["add_var"] = False
    
    def get(self, name):
        return self.data.get(name)
    
    def __setitem__(self, name, value):
        self.data[name] = value
    
    def __getitem__(self, name):
        return self.data[name]
    
    def __delitem__(self, name):
        del self.data[name]

    def add_var(self, name, var, scope=""):
        # print("add_var", name, scope)
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
        # if scope == "global":
        #     return "global", self.get_global_var(name)
        # elif scope == "local":
        #     return "local", self.get_local_var(name)
        # else:
        var = self.get_local_var(name)
        if var == None:
            var = self.get_local_shared_var(name)
            if var == None:
                return "global", self.get_global_var(name)
            return "local_shared", var
        else:
            return "local", var
    
    def add_annotation(self, annotation):
        # print("add_annotation", annotation, annotation.data)
        if isinstance(annotation, NewAbstractTypeAnnotation):
            # print("add_annotation", annotation, annotation.data)
            self.add_type(annotation)
        self.data["annotation_context"].add(annotation)
        # print(convert(self.data["annotation_context"]))

    def pop_annotation(self):
        # print("pop_annotation", annotation, annotation.data)
        return self.data["annotation_context"].pop()
    
    def query_annotation(self, func):
        return self.data["annotation_context"].query(func)

    def add_type(self, type):
        self.data["type"].append(type)

    def get_type(self):
        t = self.data.get("annotation_context")
        if t != None:
            type = t.find_type()
            if isinstance(type, TypeString):
                type_name = type.data
                struct_type = self.get_type_by_name(type_name)
                if struct_type != None:
                    return struct_type.gettype()
            return type
        return None

    def get_type_by_name(self, name):
        for t in self.data["type"]:
            if t.istype(name):
                return t
        return None

    def get_all_types(self):
        return self.data["type"]
    
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

    def type_string_search(self, type):
        if isinstance(type, TypeString):
            type_name = type.data
            struct_type = self.get_type_by_name(type_name)
            if struct_type != None:
                return struct_type.gettype()
        return type

    def enter_func(self, func):
        self.data["func"] = func
        self.data["local_vars"] = {}
        self.data["local_const"] = {}
            
        # add signature vars
        query = lambda x: isinstance(x, TypeCluster)
        found, type = self.query_annotation(query)
        if found:
            inputs, outputs = type.get_inputs_outputs()
            if inputs != None:
                for k, v in inputs.items():
                    self.add_local_var(k, Variable(k), typ=self.type_string_search(TypeAnnotation(v)))
            if outputs != None:
                for k, v in outputs.items():
                    self.add_local_var(k, Variable(k), typ=self.type_string_search(TypeAnnotation(v)))

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

    def acquire_lock(self):
        self.data["locks"] = True
    
    def release_lock(self):
        self.data["locks"] = False

    def lock_state(self):
        return self.data["locks"]
    
class AnnContext:
    def __init__(self):
        self.annotations = []

    def add(self, annotation):
        self.annotations = [annotation] + self.annotations

    def pop(self):
        if len(self.annotations) > 0:
            ret = self.annotations[0]
            self.annotations = self.annotations[1:]
            return ret
        return None
    
    def query(self, func):
        for a in self.annotations:
            if func(a):
                return True, a
        return False, None
        
    def find_type(self):
        for a in self.annotations:
            if isinstance(a, AbstractTypeAnnotation):
                return a
        return None

    def convert(self):
        return ", ".join([convert(e) for e in self.annotations])
    

def GetAnnotation(data):
    type = data.split(" ")[0]
    content = " ".join(data.split(" ")[1:])
    # print("content: ", content, content.strip()[-2:])

    # content = "content {" or "content" or "content {  "
    if len(content.strip()) > 2 and content.strip()[-2:] == " {":
        content = content.strip()[:-2].strip()
        # print("content type", content)
    if type == "type":
        return TypeAnnotation(content.strip())
    if type == "retry":
        return RetryAnnotation(content.strip())
    if type == "new":
        return NewAnnotation(content.strip())
    return None


class Annotation:
    def __init__(self, data):
        self.data = data
        self.parse()
    
    def parse(self):
        self.type = self.data.split(" ")[0]
        self.content = " ".join(self.data.split(" ")[1:])
    
    def convert(self):
        return self.data


class AbstractTypeAnnotation(Annotation):
    def __init__(self, data):
        self.data = load_json(data)
        self.name = self.data
    
    def convert(self):
        return ""
    
    def istype(self, type, name=""):
        return False
    
    def isArray(self):
        return False
    
    def isStruct(self):
        return False
    
    def startswith(self, prefix, name=""):
        return False
    
    def get_name(self):
        return self.name


class TypeCluster(AbstractTypeAnnotation):
    def __init__(self, data) -> None:
        assert isinstance(data, dict)
        self.data = data
        self.name = "cluster"
    
    def istype(self, type, name=""):
        return self.data.get(name) == type

    def startswith(self, prefix, name=""):
        type_str = self.data.get(name)
        if type_str == None:
            return False
        return type_str.startswith(prefix)

    def convert(self):
        return json.dumps(self.data)
    
    def sig_convert(self):
        sig = "({args}) ({ret})"
        args = rets = ""
        if "input" in self.data:
            args = ", ".join(['ienv stdp.PInterface'] + [f"{k} {v}" for k, v in self.data["input"].items()])
        if "output" in self.data:
            rets = ", ".join([f"{k} {v}" for k, v in self.data["output"].items()])
        sig = sig.format(args=args, ret=rets)
        if rets == "":
            sig = sig[:-2]
        return sig

    def get_inputs_outputs(self):
        return self.data.get("input", {}), self.data.get("output", {})


class TypeString(AbstractTypeAnnotation):
    def __init__(self, data) -> None:
        assert isinstance(data, str)
        self.data = data
        self.name = data
    
    def istype(self, type, name=""):
        return self.data == type

    def convert(self):
        return self.data
    
    def startswith(self, prefix, name=""):
        return self.data.startswith(prefix)
    
class TypeArray(AbstractTypeAnnotation):
    def __init__(self, data) -> None:
        assert isinstance(data, str)
        self.data = data
        self.name = self.data
    
    def istype(self, type, name=""):
        return self.data == type

    def isArray(self):
        return True

    def convert(self):
        return self.data
    
    def startswith(self, prefix, name=""):
        return self.data.startswith(prefix)
    
class TypeStruct(AbstractTypeAnnotation):
    def __init__(self, data) -> None:
        assert isinstance(data, str)
        self.data = data
        self.struct = {}
        self.parse()

    def parse(self):
        # struct Person {"id": "int64", "name": "string", "parent": {"father": "string", "mother": "string"}}
        self.data = self.data.strip()
        self.data = self.data[6:].strip()
        self.name = self.data.split(" ")[0]
        self.struct_decl = self.data[len(self.name):].strip()
        try:
            self.struct = json.loads(self.struct_decl)
        except:
            raise Exception("Cannot parse struct declaration", self.struct_decl)
        

    def istype(self, type, name=""):
        return self.name == type

    def get_field_type(self, field):
        return self.struct.get(field)

    def isStruct(self):
        return True
    
    def convert(self):
        # struct Person {id: int64, name: string, parent: {father: string, mother: string}}
        # convert to golang struct definition
        target_code = TypeStruct.convertDict(self.struct)
        # target_code += "\n\ntla.RegisterStruct(new({}))\n".format(self.name)
        return target_code

    def register(self):
        return "tla.RegisterStruct({}{{}})".format(self.name)
    
    def convertDict(dictionary):
        # convert to golang struct declaration
        indent = Indent()
        target_code = "{\n"
        with indent:
            for k, v in dictionary.items():
                if isinstance(v, dict):
                    target_code += indent(f"{k}\t struct {TypeStruct.convertDict(v)}") + "\n"
                else:
                    target_code += indent(f"{k}\t{v}") + "\n"
        target_code += "}"
        struct_name = "struct"
        return target_code
        # return self.data
    
    def startswith(self, prefix, name=""):
        return self.data.startswith(prefix)


def TypeAnnotation(data):
    data = data.strip()
    data = load_json(data)
    if isinstance(data, dict):
        return TypeCluster(data)
    if data.startswith("[]"):
        return TypeArray(data)
    if data.startswith("struct"):
        return TypeStruct(data)
    return TypeString(data)

class NewAbstractTypeAnnotation(AbstractTypeAnnotation):
    def __init__(self, data) -> None:
        self.data = data

class NewStruct(NewAbstractTypeAnnotation):
    def __init__(self, data):
        self.data = data
        self.type = TypeStruct(data)
    
    def convert(self):
        return "type " + self.type.name + " struct " +  self.type.convert()
    
    def istype(self, type, name=""):
        return self.type.istype(type, name)
    
    def isStruct(self):
        return True

    def gettype(self):
        return self.type

    def get_field_type(self, field):
        return self.type.get_field_type(field)
    
    def register(self):
        return self.type.register()
    



def NewAnnotation(data):
    data = data.strip()
    # print("NewAnnotation", data, data.startswith("struct"))
    if data.startswith("struct"):
        return NewStruct(data)

    


class RetryAnnotation(Annotation):
    def __init__(self, data):
        self.data = data.strip().split(" ")
        self.retry = self.data[0]
        if len(self.data) > 1:
            self.wait_code = self.parseTime(self.data[1])
        else:
            self.wait_code = ""

        if self.retry != "*":
            try:
                self.retry = int(self.retry)
            except:
                raise Exception("FairnessAnnotation must be a number or *")
    
    def convert(self):
        return " ".join(self.data)
    
    def parseTime(self, time_str):
        time_str = time_str.strip()
        if time_str.endswith("s"):
            self.wait = time_str[:-1]
            return f"    time.Sleep({self.wait}*time.Second)\n"
        if time_str.endswith("ms"):
            self.wait = time_str[:-2]
            return f"    time.Sleep({self.wait}*time.Millisecond)\n"
        if time_str.endswith("us"):
            self.wait = time_str[:-2]
            return f"    time.Sleep({self.wait}*time.Microsecond)\n"
        if time_str.endswith("ns"):
            self.wait = time_str[:-2]
            return f"    time.Sleep({self.wait}*time.Nanosecond)\n"
        return f"    time.Sleep({self.wait})\n"
    
    def retry_code(self, code, errHandle):
        target_code = ""
        if self.retry == "*":
            target_code += f"for err != nil {{\n"
            target_code += f"    {code}\n"
            target_code += self.wait_code
            target_code += f"}}\n"
        else:
            target_code += f"for i := 0; i < {self.retry} && err != nil; i++ {{\n"
            target_code += f"    {code}\n"
            target_code += self.wait_code
            target_code += f"}}\n"
            target_code += f"if err != nil {{\n"
            target_code += f"    {errHandle}\n"
            target_code += f"}}\n"
        # print("[retry_code]", code, target_code)
        return target_code
            
def convert_performance(func_name, args):
    if func_name == "Time":
        return "Time(\"now\")"
    if func_name == "Report":
        assert len(args.data) == 2
        return f"__report := [k |-> {convert(args.data[0])}, v |-> {convert(args.data[1])}]"
    return f"{func_name}({convert(args)})"

class Env:
    def __init__(self) -> None:
        self.get_attr_expr = []
        self.mapping = {}

    def add_get_attr(self, expr):
        self.get_attr_expr.append(expr)

    def get_get_attr(self):
        return self.get_attr_expr
    
    def reset(self):
        self.get_attr_expr = []
    
    def set(self, name, value):
        self.mapping[name] = value
    
    def get(self, name):
        return self.mapping.get(name)

global_env = Env()

class EnvStack:
    def __init__(self):
        self.stack = []
    def top(self):
        return self.stack[-1]
    def push(self, env):
        self.stack.append(env)
    def pop(self):
        self.stack.pop()

env_stack = EnvStack()
env_stack.push(Env())

def add_var_to_dict(d, n, v, raise_error=True):
    if n not in d:
        d[n] = v
        return True
    else:
        print(d)
        if raise_error:
            raise Exception("Variable %s already defined" % n)
        return False


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

class StructValConverter:
    def __init__(self, struct_name, value, context) -> None:
        self.struct_name = struct_name
        self.value = value
        self.context = context
        self.isAnounymous = False
        # print("StructValConverter", self.struct_name, self.value, type(struct_name))
        if isinstance(self.struct_name, dict):
            self.struct_decl = self.struct_name
            self.isAnounymous = True
        else:
            self.struct_decl = self.context.get_type_by_name(self.struct_name)
            if self.struct_decl == None:
                raise Exception("Cannot find struct declaration", self.struct_name)
    
    def convert(self):
        target_code = ""
        indent = Indent()
        
        if isinstance(self.value, Dict):
            value = self.value.to_json()
        else:
            value = self.value
        # print("convert0", self.value, type(self.value), convert(self.value), value)
        if self.isAnounymous:
            go_struct = "struct " + TypeStruct.convertDict(self.struct_name)
        else:
            go_struct = self.struct_name
        if isinstance(value, dict):
            # print("convert1", value, type(value))
            target_code += f"{go_struct}{{\n"
            with indent:
                for k, v in value.items():
                    target_code += indent(f"{k}: {self.convert_value(value=v, key=k)},") + "\n"
            target_code += "}"
        elif isinstance(value, list):
            target_code += f"{go_struct}{{\n"
            for v in value:
                target_code += f"\t{self.convert_value(value=v)},\n"
            target_code += "}"
        else:
            target_code += f"{self.convert_value(value=value)}"
        return target_code
    
    def convert_value(self, value, key=None):
        if isinstance(value, dict):
            if isinstance(self.struct_decl, NewStruct):
                field_type = self.struct_decl.get_field_type(key)
            else:
                field_type = self.struct_decl.get(key)
            if field_type == None:
                raise Exception("Cannot find field type", key, self.struct_decl.name)    
            return StructValConverter(field_type, value, self.context).convert()
        # if isinstance(value, list):
        #     return StructValConverter(self.struct_name, value, self.context).convert()
        if isinstance(value, str):
            # return f"\"{value}\""
            # print("convert_value", value, type(value))
            return f"{value}"
        return value

def convert_list(l, sep=" "):
    if isinstance(l, list):
        return "(" + sep.join(convert_list(x, sep) for x in l) + ")"
    else:
        return convert(l)


class ProfileObject:
    def __init__(self) -> None:
        self.isValue = False
        self.type = None
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
        self.m = m

    def convert(self, indent=indent):
        # if self.name == "state":
        #     print("Name", self.name)
        return self.name

    def get_name(self):
        return self.name

class Number(ProfileObject):
    def __init__(self, data, m=None) -> None:
        super().__init__()
        self.data = data[0]
        # print(self.value[0])

    def convert(self, indent=indent, typed=False):
        if typed:
            return f"tla.MakeTLANumber(int({self.data}))"
        return self.data

    def get_name(self):
        return self.data

class KeyValue(ProfileObject):
    def __init__(self, data, m=None) -> None:
        super().__init__()
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
        self.type = TypeAnnotation("Default")
        self.is_profile_var = False
        self.scope = None
        self.profile = None
        self.func = None
        self.init = None
        self.init_op = "="
        self.m = m

    
    def set_type(self, type):
        self.type = type

    def get_declared(self):
        return self.declared
    
    def get_scope(self):
        return self.scope
    
    def get_type(self, field=""):
        if field == "":
            return self.type
        if self.type == None:
            # print("get_type", self.name, self.type, self.type.data if self.type != None else None, self.convert())
            return None
        if self.type.isStruct():
            type = self.type.get_field_type(field)
            return type
        return None

    def analyze(self, context=Context()):
        code_scope = context.get_scope() 
        declared, var, scope = context.add_var(self.get_name(), self, code_scope)
        if declared:
            self.type = var.type
        self.scope = scope
        self.declared = declared
        self.var = var
        self.profile = context.get("profile")
        self.func = context.get("func")
        self.init = context.get("init_expr")
        self.init_op = context.get("init_op")
        

    def get_name(self):
        # access the variable (except init)
        return self.name.get_name()
    
    def typedConvert(self, indent=indent):
        name = self.convert()
        if self.type == None:
            return name
        if self.type.istype("String", self.name):
            return f"tla.MakeTLAString({name})"
        if self.type.startswith("int", self.name):
            return f"tla.MakeTLANumber(int({name}))"
        if self.type.isStruct():
            return f"tla.MakeTLAStruct({name})"
        if self.type.isArray():
            return f"tla.MakeTLASet({name})"
        return name

    def convert(self, indent=indent):
        if self.scope == "local_shared":
            name = f"{DefaultProfileStateInstance(self.profile.name.get_name())}.{convert(self.name)}"
                # traceback.print_stack()
        else:
            name = convert(self.name)
        return name


    def to_json(self):
        return self.convert()
    
    def to_local(self):
        return "AsNumber()"

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
        self.is_declare = False
        self.var_scope = None
        self.var_type = ""
        self.var_name = self.vars[0].get_name()
        # print("m", self.m, self.m.line)

    def analyze(self, context=Context()):
        self.func = context.get("func")
        if self.func != None:
            self.in_func = True
        else:
            self.in_func = False

        context.enableAddVar()
        analyze(self.vars[0], context)
        context.disableAddVar()
        analyze(self.exprs[0], context)

        self.var_type = self.vars[0].get_type()
        self.is_declare = not self.vars[0].get_declared()
        self.var_scope = self.vars[0].get_scope()
        if isinstance(self.vars[0], GetItem) or isinstance(self.vars[0], GetAttr):
            self.is_declare = False
            self.var_scope = "local"

        # print("assign", self.var_scope, self.vars[0].get_name(), declared, var.type, var.type.data if var.type != None else None)

        self.global_read = ""
        self.global_write = False
        if self.var_scope == "global":
            self.global_write = True 

        expr_str = convert(self.exprs[0])
        if context.is_global_var(expr_str):
            self.global_read = expr_str

        retry_func = lambda x: isinstance(x, RetryAnnotation)
        self.retry, self.retry_annotation = context.query_annotation(retry_func)
        self.context = context

    def typeWrap(self, expr):
        if self.var_type == None:
            print("Warning: var_type is None", self.var_name, self.m.line)
        if self.var_type == None or self.var_type.istype("String", self.var_name) or self.var_type.istype("", self.var_name):
            return expr
        if self.var_type.isArray():
            if expr.strip().startswith("{"):
                return f"{self.var_type.convert()}{expr}"
            else:
                return expr
        if self.var_type.isStruct() and isinstance(self.exprs[0], Dict):
            # print("typeWrapStruct", expr)
            return self.typeWrapStruct(self.exprs[0])
        return f"{self.var_type.convert()}({expr})"
    
    def typeWrapStruct(self, expr):
        struct_name = self.var_type.name
        value = expr
        context = self.context
        return StructValConverter(struct_name, value, context).convert()
    
    def get_var(self):
        return self.vars[0]

    def get_vars_name(self):
        return self.vars[0].get_name()
    
    def get_assign_expr(self):
        return self.exprs[0]
    
    def type_convert(var, global_read):
        if global_read == "":
            return ""
        if var.type == None:
            return ""
        if var.type.istype("string", var.get_name()):
            return ".AsString()"
        if var.type.startswith("int", var.get_name()):
            return ".AsNumber()"
        if var.type.startswith("bool", var.get_name()):
            return ".AsBool()"
        # print("type_convert1", var.type, var.get_name(), var.type.istype("String", var.get_name()), var.type.data)
        var_type_name = var.type.name
        # print(var.type, isinstance(var.type, NewStruct))
        return ".AsStruct().({})".format(var_type_name)
        assert False
        return ""
    
    def type_reverse_convert(self, expr):
        if self.var_type == None:
            return expr
        if self.var_type.istype("String", self.var_name):
            return f"tla.MakeTLAString({expr})"
        if self.var_type.startswith("int", self.var_name):
            return f"tla.MakeTLANumber(int({expr}))"
        assert False
        return expr


    def readGlobalFromEnv(self, errHandle):
        target_code = ""
        global_var_name = f"global{capitalize(self.global_read)}" + str(self.m.line)
        target_code += f"{global_var_name}, err := ienv.Read(\"{self.global_read}\")" + "\n"
        retry_code = f"{global_var_name}, err = ienv.Read(\"{self.global_read}\")"
        if self.retry:
            target_code += self.retry_annotation.retry_code(retry_code, errHandle) 
        else:
            target_code += "if err != nil {\n"
            target_code += f"    {errHandle}\n"
            target_code += "}\n"
        right = global_var_name
        return right, target_code

    def writeGlobal(self, right, errHandle):
        target_code = ""
        var_name = self.vars[0].get_name()
        target_code += f"err = ienv.Write(\"{var_name}\", {self.type_reverse_convert(right)}) \n"
        target_code += "if err != nil {\n"
        target_code += f"    {errHandle}\n"
        target_code += "}\n"
        return target_code

    def writeLocal(self, right, errHandle):
        target_code = ""
        readGlobalToStruct = len(self.global_read) > 0 and isinstance(self.vars[0], NewStruct)
        if readGlobalToStruct:
            target_code += f"{self.vars[0].convert()}, err"
        else:
            target_code += f"{self.vars[0].convert()}"
        if self.is_declare:
            target_code += " := "
            # for example: result := netRead.AsStruct().(NetRead)
            target_code += self.typeWrap(f"{right}{Assign.type_convert(self.vars[0], self.global_read)}")
        else:
            target_code += " = "
            if self.var_type != None and ((self.var_type.isArray() and isinstance(self.exprs[0], List)) or (self.var_type.isStruct() and isinstance(self.exprs[0], Dict))):
                target_code += self.typeWrap(f"{right}{Assign.type_convert(self.vars[0],self.global_read)}")
            else:
                target_code += f"{right}{Assign.type_convert(self.vars[0],self.global_read)}"
        if readGlobalToStruct:
            target_code += "\n"
            target_code += f"if err != nil {{\n"
            target_code += f"    {errHandle}\n"
            target_code += f"}}\n"
        return target_code

    def convert(self, indent=indent):
        errHandle = ""
        if self.func != None:
            errHandle = self.func.err_handle()
                    
        target_code = ""
        right = convert(self.exprs[0])
        # print("convert: ", right)
        if len(self.global_read) > 0:
            right, read_code = self.readGlobalFromEnv(errHandle)
            target_code += read_code
        if self.var_scope == "local" or self.var_scope == "local_shared":
            target_code += self.writeLocal(right, errHandle)
        else:
            target_code += self.writeGlobal(right, errHandle)
        # print("convert", target_code, self.global_read, self.var_type)
        return target_code

class ConstAssign:
    def __init__(self, data, m=None):
        self.data = data[0]
        self.m = m

    def analyze(self, context=Context()):
        context.set_flag("is_const", True)
        analyze(self.data, context)
        if not self.data.is_declare:
            raise Exception("Cannot change the value of a constant", self.m.line)
        if len(self.data.global_read) > 0:
            raise Exception("Cannot assign a global variable to a constant", self.m.line)
        context.set_flag("is_const", False)
    
    def convert(self, indent=indent):
        target_code = f"const {self.data.get_vars_name()} = {convert(self.data.get_assign_expr())}"
        return target_code

class Comparison(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data
        # print("Comparison", self.data, convert(data))
        self.left = data[0]
        self.right = data[2]
        self.op = self.convert_comp_op(data[1][0].value)
        self.m = m

    def analyze(self, context=Context()):
        analyze(self.left, context)
        analyze(self.right, context)
    #     self.set_init()

    # def set_init(self):
    #     self.left.set_init(self.right, self.op)

    def convert_comp_op(self, op):
        op_mapping = {
            "==": "==",
            "!=": "!=",
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
            end = ")"*(i+1) + ";\n"
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
        self.def_type = "func"
        self.prefix = ""
        self.sig_type = None
        self.profile = None
        # print("funcdef", convert(self.name), self.args)

    def analyze(self, context=Context()):
        self.profile = context["profile"]
        if self.profile != None:
            # self.prefix = self.profile.name.get_name()
            self.prefix = f"{self.profile.get_name()}"
        global_vars = context.get("global_vars")
        query = lambda x: isinstance(x, TypeCluster)
        has_type, ann = context.query_annotation(query)
        self.sig_type = ann if has_type else None

        context.enter_func(self)
        analyze(self.name, context)
        context["is_argu"] = True
        analyze(self.args, context)
        del context["is_argu"]
        analyze(self.suite, context)
        self.func_name = f"{self.prefix}{capitalize(convert(self.name))}"
        self.call_func_name = f"{self.profile.defaultProfileStateInstance()}.{self.prefix}{capitalize(convert(self.name))}"
        self.actor_name = f"{self.prefix}Actor{capitalize(convert(self.name))}"
        self.call_actor_name = f"{self.profile.defaultProfileStateInstance()}.{self.prefix}Actor{capitalize(convert(self.name))}"
        context.exit_func()

    def get_suite_statements(self):
        return self.suite.statements
    
    def set_type(self, def_type, prefix=""):
        self.def_type = def_type
        self.prefix = prefix

    def get_args(self):
        inputs = outputs = {}
        if self.sig_type != None:
            inputs, outputs = self.sig_type.get_inputs_outputs()
        fetch_inputs = ""
        for i, k in enumerate(inputs):
            fetch_inputs += f"{k} := input[{i}].({inputs[k]})" + "\n"
            # print( k, len(k))
        # if len(fetch_inputs) > 0 and fetch_inputs[-1] == "\n":
        #     fetch_inputs = fetch_inputs[:-1]
        fetch_inputs = removeNewLine(fetch_inputs)
        return fetch_inputs
    

    def push_results(self):
        inputs, outputs = self.sig_type.get_inputs_outputs()
        fetch_outputs = ""
        for i, k in enumerate(outputs):
            fetch_outputs += f"output = append(output, {k})" + "\n"
        if len(fetch_outputs) > 0 and fetch_outputs[-1] == "\n":
            fetch_outputs = fetch_outputs[:-1]
        return fetch_outputs
    
    def get_result(self, vars, tmpResult):
        target = ""
        inputs, outputs = self.sig_type.get_inputs_outputs()
        if len(outputs) != len(vars):
            return target
        values = list(outputs.values())
        # print(values)
        for i, k in enumerate(outputs):
            target += f"{vars[i]} = {tmpResult}[{i}].({values[i]})" + "\n"
        return target
    
    def call_func(self, inputs, outputs):
        indent = Indent()
        target = ""
        if outputs != None and len(outputs) > 0:
            result = ", ".join(outputs.keys())
            target = result + " := "
        target +=  f"{self.profile.defaultProfileStateInstance()}.{self.prefix}{capitalize(convert(self.name))}({', '.join(['ienv'] + list(inputs.keys()))})"
        return target
    
    def convert(self, indent=indent):
        sig_type = self.sig_type
        inputs = outputs = {}
        if sig_type != None and isinstance(sig_type, TypeCluster):
            inputs, outputs = sig_type.get_inputs_outputs()

        target = ""
        func_def = self.convertFunc(inputs, outputs)
        target += func_def + "\n\n"
        actor_def = self.convertActor(inputs, outputs)
        target += actor_def
        return target
    
    def sig_convert(self, inputs, outputs):
        sig = "({args}) ({ret})"
        args = rets = ""
        if inputs != None:
            args = ", ".join(['ienv stdp.PInterface'] + [f"{k} {v}" for k, v in inputs.items()])
        if outputs != None:
            rets = ", ".join([f"{k} {v}" for k, v in outputs.items()])
        sig = sig.format(args=args, ret=rets)
        if rets == "":
            sig = sig[:-2]
        return sig
    
    def convertFunc(self, inputs, outputs, indent=indent):
        indent = Indent()
        sig = self.sig_convert(inputs, outputs)
        ins = ""
        if self.profile != None:
            ins = f"({self.profile.defaultProfileStateInstance()} *{self.profile.defaultProfileState()})"
        target = f"{self.def_type} {ins} {self.func_name} {sig} {{\n" 
        with indent:
            if "err" not in inputs and "err" not in outputs:
                target += indent("var err error") + "\n"
                target += indent("_ = err") + "\n"
            target += indent(self.suite.convert())+"\n"
        target += "}"
        return target
    

    def convertActor(self, inputs, outputs, indent=indent):
        ins = ""
        if self.profile != None:
            ins = f"({self.profile.defaultProfileStateInstance()} *{self.profile.defaultProfileState()})"
        target = f"{self.def_type} {ins} {self.actor_name}(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{{}}, outputs chan []interface{{}})  {{\n"
        
        with indent:
            target += indent(
"""for {
""")
            if outputs != None and len(outputs) > 0:
                target += indent(
"""output := []interface{}{}
""")                     
            target += indent(
"""select {
    case <-ctrl:
        return
    case input := <-inputs:""")
            target += "\n"
            with indent:
                with indent:
                    target += indent("_ = input") + "\n"
                    target += indent(self.get_args()) + "\n"
                    target += indent(self.call_func(inputs, outputs)) + "\n"
                    if outputs != None and len(outputs) > 0:
                        target += indent(self.push_results()) + "\n"
                        target += indent("outputs <- output") + "\n"
                        target += indent("output = []interface{}{}") + "\n"
                target +=  indent("}") + "\n"
            target += indent("}")
            # # func """ + sig + """ {
            
            # """ + self.suite.convert()"""
            #  """ + self.get_args() + "\n" + self.suite.convert() + "\n" + self.push_results() + """


            # target += indent(self.suite.convert())
        # print(target)
        target += "\n}"
        # print(target)
        return target

    def expand_code(self, indent=indent):
        target = indent(self.suite.convert() + "\nreturn")
        return target
    
    def err_handle(self):
        if self.sig_type == None:
            return ""
        inputs, outputs = self.sig_type.get_inputs_outputs()
        if outputs == None or len(outputs) == 0:
            vars = ""
        else:
            vars = ", ".join(list(outputs.keys()))
        return f"if err != nil {{\n    return {vars}\n}}\n"


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
        # target = "__call_stack[name] := <<"
        # for expr in self.expr:
        #     target += convert(expr) + ", "
        # if len(self.expr) > 0:
        #     target = target[:-2] + ">> \o __call_stack[name];\n"
        target = f"return"
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
    
class MacroDef(FuncDef):
    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)

    def analyze(self, context=Context()):
        return super().analyze(context)
    
    def convert(self):
        return ""

class List(ProfileObject):
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
        if len(self.data) > 0:
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

class Dict(ProfileObject):
    def __init__(self, data, m=None) -> None:
        super().__init__()
        self.data = data
        # print(self.data)

    def to_json(self):
        ret = {}
        for key_value in self.data:
            key = key_value[0]
            value = key_value[2]
            # print("key_value", key, value)
            if isinstance(value, ProfileObject):
                value = value.to_json()
            elif isinstance(value, str):
                value = "\"" + value + "\""
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
        target = "{"
        for key_value in self.data:
            if key_value[1].value == "->":
                target += f"{self.convert_key(key_value[0])} : {convert(key_value[2])}, "
            else:
                target += f"{self.convert_key(key_value[0])} : {convert(key_value[2])}, "
        if len(self.data) > 0:
            target = target[:-2]
        target += "}"
        # print(target)
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
                stack.append(f"{op1} {op} {op2}")
        return stack[0]
 
class OrExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class AndExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class XorExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)
        # print("xor", data)
        self.data = data
    
    def convert(self, indent=indent):
        return f"({convert(self.data[0])} ^ {convert(self.data[1])})"

class ArithExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class ShiftExpr(Term):
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

class Factor(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print(data)
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

class Comment(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        if self.data.startswith("#@"):
            self.type = "annotation"
            self.ann = GetAnnotation(self.data[2:])
        elif self.data.strip().startswith("#}"):
            self.type = "end_annotation"
            # self.data = ""
        else:
            self.type = "comment"
            # self.data = ""
        # print("comment", self.data, self.type)
    def analyze(self, context=Context()):
        # print("analyze", self.type, self.type == "end_annotation")
        if self.type == "annotation":
            # print("comment", self.ann, self.data, self.type)
            context.add_annotation(self.ann)
            # print("[comment]", convert(context.data["annotation_context"]))
        elif self.type == "end_annotation":
            # print("start pop")
            context.pop_annotation()
        else:
            pass
    
    def convert(self, indent=indent):
        # print("comment convert", self.data)
        return ""
    
class Newline(ProfileObject):
    def __init__(self, data, m=None) -> None:
        
        self.data = []
        for i in data:
            if isinstance(i, Comment):
                self.data.append(i)
                # print("NewLine add", i.convert())
        # if len(self.data) > 0:
        #     print("newline", self.data, self)

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=indent):
        target = ""
        for i in self.data:
            convi = convert(i)
            if len(convi) > 0:
                target += i.convert() + "\n"
        # print("newline convert", target, self.data, self)
        return target
    
class SimpleStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("simplestmt", self.data)

    def simple_assign(self, types):
        for i in self.data:
            for type in types:
                if isinstance(i, type):
                    return i
        return None
    
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

class Suite(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print(data)
        self.statements = data
        self.is_expr = False

    def analyze(self, context=Context()):
        self.is_expr = context.get("op") != None or context.get("is_expr") == True
        for statement in self.statements:
            # print(statement)
            analyze(statement, context)

    def convert(self, indent=indent):
        target_code = ""
        for statement in self.statements:
            try:
                convs = convert(statement)
                # if len(convs) > 0 and convs[-1] != ";"and convs[-1] != "\n" and not self.is_expr and not isinstance(statement, (LabelStmt)):
                if len(convs) > 0 and convs[-1] != ";"and convs[-1] != "\n" and not self.is_expr and not isinstance(statement, (LabelStmt)):
                    target_code += convs + "\n"
                elif len(convs) > 0:
                    target_code += convs + "\n"
                else:
                    pass
            except Exception as e:
                print(e)
                print(statement)
                traceback.print_exc()
                print("statement", statement, convert(statement))
        if len(target_code) > 0 and target_code[-1] == "\n":
            target_code = target_code[:-1]
        # print("[]", target_code)
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
            self.context = "__"+func.prefix + "_" + func.name.get_name()
        analyze(self.label, context)
        labelName = convert(self.label)
        # print("label", labelName)
        if labelName.startswith("Atom") and not context.lock_state():
            # print("label", labelName)
            self.lock = "lock"
            context.acquire_lock()
        elif context.lock_state():
            self.lock = "release"
            context.release_lock()
        else:
            self.lock = ""

    
    def convert(self):
        if self.lock == "lock":
            return f"ienv.Write(\"lock\", \"Acquire\")"
        elif self.lock == "release":
            return f"ienv.Write(\"lock\", \"Release\")"
        else:
            return ""

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
        return f"{convert(self.data[0])}, ({convert(self.data[1])})"

class GetItem(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data
        self.type = None
        # print("getitem", self.data)

    def set_type(self, type):
        self.type = type
    
    def get_declared(self):
        return self.declared
    
    def get_scope(self):
        return self.scope
    
    def get_type(self, field=""):
        if field == "":
            return self.type
        if self.type.isStruct():
            type = self.type.get_field_type(field)
            return type
        return None

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)
        if isinstance(self.data[0], Variable):
            self.type = self.data[0].get_type(convert(self.data[1]))
            self.declared = self.data[0].get_declared()
            self.scope = self.data[0].get_scope()
        

    def convertRead(self):
        pass

    def convertWrite(self):
        pass


    def convert(self):
        # print("getitem", self.data[0], self.data[1], convert(self.data[0]), convert(self.data[1]))
        if self.data[0].is_compound():
            if type(self.data[1]) == Slice:
                return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
            return f"({convert(self.data[0])})[{convert(self.data[1])}]"
        if type(self.data[1]) == Slice:
            return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
        return f"{convert(self.data[0])}[{convert(self.data[1])}]"
    
    def typedConvert(self):
        return self.convert()
    
    def to_json(self):
        return self.convert()

class GetAttr(Variable):
    def __init__(self, data, m=None) -> None:
        self.data = data
        self.obj = data[0]
        self.attr = data[1]
        # global_env.add_get_attr(self)
        self.extra_argu = ""
        self.type = None
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
        context.disableAddVar()
        analyze(self.attr, context)
        # print(self.obj, convert(self.obj), isinstance(self.obj, Variable), self.obj.get_scope(), context.data["global_vars"])
        if isinstance(self.obj, Variable) and self.obj.get_scope() == "global":
            self.global_access = True
        self.context = context

    def get_var(self):
        return self
    
    def get_name(self):
        return self.attr.get_name()
    
    def get_obj_name(self):
        return self.obj.get_name()
    
    def get_access(self):
        return self.global_access

    def set_env(self, env):
        self.env = env

    def init_code(self, init_process=False):
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
        return f"ienv.Read(\"{obj}\", "

    def convertWrite(self, obj):
        # print("convertWrite", obj)
        return f"ienv.Write(\"{obj}\", "

    def convertGlobal(self):
        action = convert(self.attr)
        obj = convert(self.obj)
        if action == "read":
            return obj, action, self.convertRead(obj)
        elif action == "write":
            return obj, action, self.convertWrite(obj)
        else:
            return "", "", ""
    
    def get_global_access(self):
        # print(self.attr.get_name(), self.obj.get_name(), self.global_access)
        return self.global_access
        

    def convert(self):
        attr = convert(self.attr)
        obj = convert(self.obj)
        if self.obj.is_compound():
            return f"({obj}).{attr}"
        return f"{obj}.{attr}"

class FuncCall(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.args = data[1]
        self.is_procedure = False
        self.target = None
        self.global_access = False
        self.m = m

    def analyze(self, context=Context()):
        profile = context.get("profile")
        analyze(self.name, context)
        analyze(self.args, context)
        self.profile = profile
        if profile != None:
            try:
                if type(self.name) == GetAttr:
                    self.global_access = self.name.get_global_access()
                else:
                    self.global_access = False
            except Exception as e:
                print(e)
                traceback.print_exc() 
        retry_func = lambda x: isinstance(x, RetryAnnotation)
        self.retry, self.retry_annotation = context.query_annotation(retry_func)
        self.context = context   

    def convert(self, indent=indent):
        def checkRecv(func_name):
            splits = func_name.split(".")
            if len(splits) > 1 and splits[1] == "Recv":
                return True
            return False
        if self.target != None:
            return self.target
        if self.global_access:
            obj, action, target = self.name.convertGlobal()
            if action == "write":
                target = f"err = {target}{', '.join(typedConvert(self.args))})"
                if self.retry:
                    target += "\n" + self.retry_annotation.retry_code(target, errHandle="")  
            else:
                if self.args != None and len(self.args) == 0:
                    raise Exception("global read must have args")
                global_var_name = f"global{capitalize(obj)}" + str(self.m.line)
                retry_code = f"{global_var_name}, err = {target}{', '.join(typedConvert(self.args[1:]))})\n"
                target = f"{global_var_name}, err := {target}{', '.join(typedConvert(self.args[1:]))})\n"
                if self.retry:
                    target += "\n" + self.retry_annotation.retry_code(retry_code, errHandle="") 
                target += "\n" + f"{convert(self.args[0])} = "
                target += f"{global_var_name}{Assign.type_convert(self.args[0], global_var_name)}"
        else:
            func_name = convert(self.name)
            fn = self.profile.get_procedure(func_name)
            if func_name in PERFORMANCE_VARS:
                target = convert_performance(func_name, self.args)
            if func_name == "nop":
                target = "_ = " + ', '.join(convert(self.args))
            elif func_name in UTIL_FUNC:
                args_name = ', '.join(convert(self.args))
                if func_name == "Actor":
                    if self.profile != None:
                        args_name = "ienv, " + f"{self.profile.defaultProfileStateInstance()}.{self.profile.get_name()}" + "Actor" + capitalize(args_name)
                func_name = UTIL_FUNC[func_name]
                target = f"{func_name}({args_name})"
            elif checkRecv(func_name):
                f_name = func_name.split(".")[0].split("Actor")[0]
                # f = self.libs[f_name]
                if fn == None:
                    target = f"{func_name}({', '.join(convert(self.args))})" 
                else:
                    vars = convert(self.args)
                    tmpResult = "outputTmp"+str(self.m.line)
                    target = f"{tmpResult} := {func_name}()" + "\n"
                    # print(vars)
                    target += fn.get_result(vars, "outputTmp"+str(self.m.line))
            elif fn != None:
                args_name = convert(self.args)
                if isinstance(args_name, list):
                    args_name = ", ".join(args_name)
                target = f"{fn.call_func_name}( {'ienv, ' + args_name})"
                # print(f_name)
                # print(self.profile.procedures)
            
                # target = f"{func_name}({', '.join(convert(self.args))})" 
            else:
                target = f"{func_name}({', '.join(convert(self.args))})"
        return target

    def to_json(self):
        return self.convert()


class Arguments(ProfileObject):
    def __init__(self, data, m=None) -> None:
        # print("Arguments", data, type(data))
        self.data = data

    def analyze(self, context=Context()):
        scope = context.get_scope()
        for arg in self.data:
            analyze(arg, context)

    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, index):
        return self.data[index]
    
    def convert(self):
        return convert(self.data)
    
    def typedConvert(self):
        
        return typedConvert(self.data)
        # for arg in self.data:
        #     target += typedConvert(arg) + ", "
        # if len(target) > 0:
        #     target = target[:-2]
        # print("Arguments", self.data, type(self.data), target)
        # return target

class Profile(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.args = data[1]
        self.suite = data[2]

        self.vars = {}
        self.symbols = {}
        self.procedures = {}
        self.processes = {}
        self.operators = {}
        self.instances = []
        self.gen_processes = []

        self.__has_process = False
        self.__is_env = False

        self.init = None 

    def is_env(self):
        return self.__is_env

    def to_json(self):
        ret = {}
        for var in self.vars:
            ret[var] = self.vars[var].to_json()
        return ret
    
    def has_init(self):
        return self.init != None

    def analyze(self, context=Context()):
        global_vars = context.get("global_vars")
        instances = context.get("instances")
        info = instances.get(self.name.get_name())
        if info != None:
            if info.get("range") != None:
                self.instances = info.get("range")
            else:
                self.instances = info.get("vars") 
        else:
            self.instances = []
        

        context.enter_profile(self)
        global_vars = deepcopy(context.get("global_vars"))
        query = lambda x: isinstance(x, AbstractTypeAnnotation)
        has_type, ann = context.query_annotation(query)
        if has_type and ann.istype("env"):
            self.__is_env = True

        for statement in self.suite.statements:
            if type(statement) == SimpleStmt and statement.simple_assign([Assign, ConstAssign, Comparison]) != None:
                statement = statement.simple_assign([Assign, ConstAssign, Comparison])
            if type(statement) == Assign or (type(statement) == Comparison and statement.op == "\in"):
                var = statement.get_var()
                if var.get_name() not in global_vars:  
                    self.vars[var.get_name()] = var
                    self.symbols[var.get_name()] = var
            elif type(statement) == FuncDef:
                self.symbols[statement.name.get_name()] = statement
                name = statement.name.get_name()
                if name == "main":
                    self.process = statement
                    self.__has_process = True
                elif name == "init":
                    self.init = statement
                    self.process_init()
                    self.procedures[statement.name.get_name()] = statement
                else:
                    self.procedures[statement.name.get_name()] = statement
            elif type(statement) == OpDef:
                self.operators[statement.name.get_name()] = statement
            elif type(statement) == ProcDef:
                self.process = statement
                self.processes[statement.name.get_name()] = statement
                self.__has_process = True
            else:
                continue
        
        # print(self.args)
        context.enter_signature()
        # print("profile", self.name.get_name(), self.args)
        analyze(self.args, context)
        context.exit_signature()
        
        for statement in self.suite.statements:
            analyze(statement, context)
        self.local_shared_vars = context.get_local_shared_vars()
        context.exit_profile()
    
    def has_process(self):
        return self.__has_process
        
    def get_process_name(self):
        if self.__has_process:
            return self.name.get_name() + "Main"
        return ""

    def get_vars_declare(self):
        target = ""
        for name in self.vars:
            var = self.vars[name]
            if var.type == "Default":
                target += f"{var.init_code(init_process=self.instances)}\n"
        if len(target) > 1:
            target = target[:-2]
        return target

    def process_init(self):
        def is_init(obj):
            if type(statement) == Assign or (type(statement) == Comparison and statement.op == "\in"):
                return True
            if type(statement) == GetAttr and convert(statement.obj) == "self" and type(statement.attr) == Name:
                return True
            return False
        statements = self.init.get_suite_statements()
        for statement in statements:
            if is_init(statement):
                var = statement.get_var()  
                statement.set_init()                         
                self.vars[var.get_name()] = var
                self.symbols[var.get_name()] = var

    def convert_process(self, indent=indent):
        target = ""
        profile_name = self.name.get_name() 
        for proc_name in self.processes:
            proc = self.processes[proc_name]
            gen_proc_name = profile_name+capitalize(proc.name.get_name())
            self.gen_processes.append(gen_proc_name)
            target += f"func ({self.defaultProfileStateInstance()} *{self.defaultProfileState()}) {gen_proc_name}(ienv stdp.PInterface) (err error)"+ "{\n"
            with indent:
                target += proc.expand_code() + "\n"
            target += "}"
            target += "\n"
        return target

    def convert_global_process(self, indent=indent):
        target = ""
        with indent:
            target += self.process.expand_code() + "\n"
        target += "}"
        target += "\n"
        return target

    def convert_global_procedures(self):
        target = ""
        for procedure in self.procedures:
            # self.procedures[procedure].set_type(TypeAnnotation("procedure", "__"+self.name.get_name()))
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

    def convert_global_variables(self, indent=indent):
        target = "variables\n"
        with indent:
            for name in self.vars:
                var = self.vars[name]
                if var.type == "Default":
                    target += indent(f"{var.init_code()}") + "\n"
        return target[:-1]


    def get_procedure(self, name):
        return self.procedures.get(name)
    
    def covert_local_shared_vars(self):
        indent = Indent()
        name = self.name.get_name()
        # if len(self.local_shared_vars) == 0:
        #     return ""
        target = f"type {DefaultProfileState(name)} struct {{\n"
        try:
            with indent:
                for var_name in self.local_shared_vars:
                    var = self.local_shared_vars[var_name]
                    target += indent(f"{var_name} {var.get_type().get_name()}")+"\n"
            target += "}\n"

        except:
            print("local_shared_vars", var_name)
        # target += f"var {DefaultProfileStateInstance(name)} {name}State = {name}State{{}}"
        return target

    def defaultProfileState(self):
        return DefaultProfileState(self.get_name())
    
    def defaultProfileStateInstance(self):
        return DefaultProfileStateInstance(self.get_name())

    def get_name(self):
        return self.name.get_name()

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
            then_k = "{"
            else_k = "else {"
            end_k = "}"

        target = f"{if_k} {convert(self.condition)} {then_k}\n"
        with indent:
            target += indent(self.suite.convert()) + "\n"
            target += f"{end_k} "
        # target = onlyOneNewLine(target)
        if self.elifs != None:
            target += convert(self.elifs) + "\n"
        # target = onlyOneNewLine(target)
        if self.else_suite:
            else_target = removeNewLine(self.else_suite.convert())
            if len(else_target) > 0:
                target = removeNewLine(target)
                target += f"{else_k}\n"
                with indent:
                    target += indent(else_target) + "\n"
                    target += f"{end_k} "
        return target

class ComprehensionVar(Assign):
    def __init__(self, data, m=None):
        self.var = data[0]
        self.suite = data[1]
    
    def analyze(self, context=Context()):
        context = deepcopy(context)
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
            target += f"else if {convert(elif_[0])} {{\n"
            with indent:
                target += indent(convert(elif_[1])) + "\n"
            target += "}"
        return removeNewLine(target)

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
        target = "for ;" + convert(self.condition) + "; {\n"
        with indent:
            target += indent(convert(self.suite)) + "\n"
        target += "}"
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
        super().__init__(data, " && ")
    
class OrTest(LogicTest):
    def __init__(self, data, m=None) -> None:
        super().__init__(data, " || ")

class NotTest(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]
        # print(self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        # return "~"
        return "!" + convert(self.data)

class AssertStmt(ProfileObject):
    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        target = convert(self.data)
        # print("assert", target)
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
    
    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self):
        return ""

class FileInput(ProfileObject):
    def __init__(self, data, m=None, tranformer=None, parse=None) -> None:
        self.statements = data
        self.transformer = tranformer
        self.parser = parse
        self.extends = """
import (
	"fmt"
    "time"
	"github.com/UBC-NSS/pgo/distsys"
	"github.com/UBC-NSS/pgo/distsys/tla"
	"stdp"
)

var _ = new(fmt.Stringer)
var _ = distsys.ErrDone
var _ = tla.TLAValue{}
var _ = stdp.ErrDone
var _ = time.Now

         """ # change to import
        self.symbols = {}
        self.vars = {}
        self.prof_vars = {}
        self.profiles = {}
        self.libs = {}
        self.is_anonymous = False
        self.const_declare = []
        self.analyze()

    def __auto_default_var(self):
        if self.prof_vars == {}:
            for profile in self.profiles:
                var_name = profile + "_var"
                var = Variable(var_name)
                var.set_type(TypeAnnotation("Profile"))
                self.prof_vars[var_name] = var
                self.profiles[profile]["vars"].append(var_name)
                self.vars[var_name] = var
                self.symbols[var_name] = var

    def analyze(self):
        for statement in self.statements:
            if isinstance(statement, SimpleStmt):
                inner = statement.simple_assign([Assign, ConstAssign, Comparison, FuncCall])
                if inner is not None:
                    statement = inner
                
            if isinstance(statement, Profile):
                name = statement.name.get_name()
                add_var_to_dict(self.profiles, name, {"profile_declare": statement, "vars": [], "range": None})
                add_var_to_dict(self.symbols, name, statement)

            if isinstance(statement, Assign):
                var = statement.get_var()
                statement.analyze()
                if isinstance(statement.exprs[0], FuncCall):
                    called = statement.exprs[0].name.get_name()
                    # print(called in self.symbols, self.symbols)
                    if called in self.symbols:
                        called_obj = self.symbols[called]
                        if isinstance(called_obj, Profile):
                            var.set_type(TypeAnnotation("Profile"))
                            self.prof_vars[var.get_name()] = var
                            self.profiles[called_obj.name.get_name()]["vars"].append(var.get_name())        
                self.vars[var.get_name()] = var
                self.symbols[var.get_name()] = var         
            if isinstance(statement, Comparison) and statement.op == "\in":
                var = statement.get_var()
                statement.analyze({})
                var_name = var.get_name()
                if var_name in self.profiles:
                    self.prof_vars[var_name] = var
                    self.profiles[var_name]["range"] = statement.right
                    self.is_anonymous = True
                else:
                    self.vars[var.get_name()] = var
                    self.symbols[var.get_name()] = var
                # print("[profile range]", var_name, self.profiles, var_name in self.profiles, self.is_anonymous)

            if isinstance(statement, ImportStmt):
                for lib in statement.libs:
                    self.libs[lib] = None
            
            if isinstance(statement, ConstAssign):
                # print("const", statement)
                self.const_declare.append(statement)
            
            

        self.__parse_libs()
        self.__auto_default_var()

        context = Context()
        context["global_vars"] = self.vars
        context["instances"] = {}
        context["libs"] = list(self.libs.keys())
        for statement in self.statements:
            analyze(statement, context)
        self.types = context.get_all_types()


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
        target = "package " + module + "\n"
        target += self.extends + "\n"
        for const in self.const_declare:
            target += convert(const) + "\n"

        # print("types", self.types)
        for type in self.types:
            target += convert(type) + "\n"

        target += util.newline(self.__convert_local_shared_vars(), n=1)
        target += util.newline(self.__convert_procedures(), n=1)
        target += util.newline(self.__convert_process(), n=1)
        self.target = target
        return target

    def convert_variables(prof, indent=indent):
        if prof is None:
            print("prof is None")
            return ""
        target = ""
        for name in prof.vars:
            var = prof.vars[name]
            if var.type == "Default":
                target += f"{var.init_code()}" + "\n"
        if len(target) > len(";\n"):
            target = target[:-1]
        else:
            target = ""
        return target
    
    def __convert_global_variables(self, indent=indent):
        pass

    def __convert_local_shared_vars(self):
        target = ""          
        for name in self.profiles:
            profile = self.profiles[name]
            target += profile["profile_declare"].covert_local_shared_vars() + "\n"
        return target


    def __convert_process_header(self, profile):
        prof = profile['profile_declare']
        target = f"func ({prof.defaultProfileStateInstance()} *{prof.defaultProfileState()}) {prof.get_process_name()}(ienv stdp.PInterface) (err error)"+ "{"
        return target

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
            # if profile["profile_declare"].is_env():
            #     continue
            # print("profile", name, profile["profile_declare"].has_process())
            if profile["profile_declare"].has_process():
                # target += self.__convert_process_header(profile) + "\n"
                target += profile["profile_declare"].convert_process() + "\n"
        for name in self.profiles:
            profile = self.profiles[name]["profile_declare"]
            if profile.is_env():
                continue
            process_name = profile.get_process_name()
            processes = [profile.defaultProfileStateInstance()+"."+e for e in profile.gen_processes]
            gen_processes = ", ".join(processes)

            #f"var {DefaultProfileStateInstance(name)} {name}State = {name}State{{}}"
            if profile.has_init():
                init_func = f"        Init: {profile.defaultProfileStateInstance()}.{name}Init,\n"
            else:
                init_func = ""
            target += \
f"func {name} () stdp.Profile {{ \n\
    var {profile.defaultProfileStateInstance()} *{profile.defaultProfileState()} = &{profile.defaultProfileState()}{{}} \n \
    return stdp.Profile {{ \n\
        Name: \"{name}\",\n\
        Main: {profile.defaultProfileStateInstance()}.{process_name},\n\
        State: {profile.defaultProfileStateInstance()}, \n\
        Processes: []stdp.Proc{{{gen_processes}}},\n{init_func}\
    }} \n}}\n"
        target += "\nfunc init() {\n"
        with indent:
            for t in self.types:
                # print("type", t, t.register())
                if isinstance(t, NewStruct):
                    target += indent(t.register()) + "\n"
        target += "}"
        return target


class MODULE(ProfileObject):
    def __init__(self, data, m=None):
        self.data = data


def get_package_name_from_file(output):
    output = output.split("/")[-1]
    output = output.split(".")[0]
    return output

def save(goCode, output):
    package = get_package_name_from_file(output)
    code = goCode.convert(module=package)
    # print(code)
    with open(output, "w") as f:
        f.write(code)