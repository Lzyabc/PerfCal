"""
The module contains classes for converting and manipulating Golang profile objects.
"""
import traceback
import re
import json
import logging
from . import util
from .util import get_convert, analyze, load_source_code, load_json
from copy import deepcopy


def remove_blank_line(s):
    """
    Removes trailing newline characters from a given string.
    """
    while s.endswith("\n"):
        s = s[:-1]
    return s


def keep_one_blank_line(s):
    """
    Ensures that a given string ends with exactly one newline character.
    """
    s = remove_blank_line(s)
    return s + "\n"


def capitalize(s):
    """
    Capitalizes the first character of the given string.
    """
    if len(s) == 0:
        return s
    return s[0].upper() + s[1:]


convert = get_convert("go")


def default_profile_state(name):
    """Default profile state name"""
    return name+"State"


def default_profile_state_instance(name):
    """Default profile instance name"""
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

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')


def c(*args):
    """
    A log function that safely handles any type of parameters.
    Convert all parameters to strings and connect them with spaces.
    """
    debug_message = ' '.join(str(arg) for arg in args)
    return debug_message


debug = logging.debug


def typed_convert(obj):
    """
    Converts a given object to a string representation of its type.
    """
    if obj is None:
        return ""
    if hasattr(obj, 'convert'):
        return obj.typed_convert()
    elif isinstance(obj, list):
        obj = [typed_convert(x) for x in obj]
        return obj
    elif isinstance(obj, tuple):
        target = ""
        for x in obj:
            target += typed_convert(x) + ", "
        if len(target) > 0:
            target = target[:-2]
        target = "tla.MakeTLATuple(" + target + ")"
        return target
    elif isinstance(obj, dict):
        return {typed_convert(k): typed_convert(v) for k, v in obj.items()}
    elif isinstance(obj, bool):
        return f"tla.MakeTLABool({str(obj).lower()})"
    elif isinstance(obj, int):
        return f"tla.MakeTLANumber(int({str(obj)}))"
    elif isinstance(obj, float):
        return f"tla.MakeTLANumber(int({str(obj)}))"
    elif isinstance(obj, str):
        return f"tla.MakeTLAString(\"{obj}\")"
    else:
        return str(obj)


class Context:
    """
    A class for managing the context of a code processing environment, particularly
    for handling variables and states.

    The `Context` class provides mechanisms to handle various aspects of a code's
    context, such as variable scopes, function definitions, and macro handling. 
    It offers methods to enter and exit specific code constructs and manage variables
    within different scopes.
    """

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

    def enable_add_var(self):
        """
        Enables the addition of variables to the context unless within a macro context.
        """
        self.data["add_var"] = True

    def disable_add_var(self):
        """
        Disables the addition of variables to the context.
        """
        self.data["add_var"] = False

    def get(self, name):
        """
        Retrieves a value from the context data based on the provided name.
        """
        return self.data.get(name)

    def __setitem__(self, name, value):
        self.data[name] = value

    def __getitem__(self, name):
        return self.data[name]

    def __delitem__(self, name):
        del self.data[name]

    def add_var(self, name, var, scope=""):
        """
        Adds a variable to the context in a specified scope.
        """
        scope1, var1 = self.get_var(name, scope)
        if var1 is not None:
            return True, var1, scope1

        if not self.data["add_var"]:
            return False, var, scope

        if scope == "global":
            declared, var = self.add_global_var(name, var)
        if scope == "local_shared":
            declared, var = self.add_local_shared_var(name, var)
        else:
            declared, var = self.add_local_var(name, var)
        return declared, var, scope

    def get_var(self, name, scope=""):
        """
        Retrieves a variable from the context based on its name and optional scope.
        """
        var = self.get_local_var(name)
        if var is None:
            var = self.get_local_shared_var(name)
            if var is None:
                return "global", self.get_global_var(name)
            return "local_shared", var
        else:
            return "local", var

    def add_annotation(self, annotation):
        """
        Adds an annotation to the Context.
        """
        if isinstance(annotation, NewAbstractTypeAnnotation):
            self.add_type(annotation)
        self.data["annotation_context"].add(annotation)

    def pop_annotation(self):
        """
        Pops the last annotation from the annotation context.
        """
        return self.data["annotation_context"].pop()

    def query_annotation(self, func):
        """
        Queries for annotations that meet a specific condition.
        """
        return self.data["annotation_context"].query(func)

    def add_type(self, typ):
        """
        Adds a type definition to the Context.
        """
        self.data["type"].append(typ)

    def get_type(self):
        """
        Gets the type definition in the current context.
        """
        t = self.data.get("annotation_context")
        if t is not None:
            typ = t.find_type()
            if isinstance(typ, TypeString):
                type_name = typ.data
                struct_type = self.get_type_by_name(type_name)
                if struct_type is not None:
                    return struct_type.gettype()
            return typ
        return None

    def get_type_by_name(self, name):
        """
        Retrieves a type definition by its name from the stored types.
        """
        for t in self.data["type"]:
            if t.is_type(name):
                return t
        return None

    def get_all_types(self):
        """
        Retrieves all type definitions stored in the context.
        """
        return self.data["type"]

    def set_global_vars(self, global_vars):
        """
        Sets the global variables in the context.
        """
        self.data["global_vars"] = global_vars

    def get_global_vars(self):
        """
        Retrieves the global variables stored in the context.
        """
        return self.data.get("global_vars")

    def add_global_var(self, name, var):
        """
        Adds a global variable to the context.
        """
        if name not in self.data["global_vars"]:
            self.data["global_vars"][name] = var
            var.set_type(self.get_type())
            if self.get_flag("is_const"):
                self.data["const"][name] = var
            return False, var
        return True, self.data["global_vars"][name]

    def get_global_var(self, name):
        """
        Retrieves a global variable by its name.
        """
        return self.data["global_vars"].get(name)

    def del_global_var(self, name):
        """
        Deletes a global variable from the context by its name.
        """
        if name in self.data["global_vars"]:
            del self.data["global_vars"][name]

    def add_local_shared_var(self, name, var, typ=None):
        """
        Adds a local shared variable to the context.
        """
        if name not in self.data["local_shared_vars"]:
            self.data["local_shared_vars"][name] = var
            if typ is not None:
                var.set_type(typ)
            else:
                var.set_type(self.get_type())
            if self.get_flag("is_const"):
                self.data["const"][name] = var
            return False, var
        return True, self.data["local_shared_vars"][name]

    def get_local_shared_vars(self):
        """
        Retrieves all local shared variables stored in the context.
        """
        return self.data["local_shared_vars"]

    def get_local_shared_var(self, name):
        """
        Retrieves a local shared variable by its name.
        """
        return self.data["local_shared_vars"].get(name)

    def del_local_shared_var(self, name):
        """
        Deletes a local shared variable from the context by its name.
        """
        if name in self.data["local_shared_vars"]:
            del self.data["local_shared_vars"][name]

    def add_local_var(self, name, var, typ=None):
        """
        Adds a local variable to the context.
        """
        if var not in self.data["local_vars"]:
            self.data["local_vars"][name] = var
            if typ is not None:
                var.set_type(typ)
            else:
                var.set_type(self.get_type())
            if self.get_flag("is_const"):
                self.data["const"][name] = var
            return False, var
        return True, self.data["local_vars"][name]

    def get_local_var(self, name):
        """
        Retrieves a local variable by its name.
        """
        return self.data["local_vars"].get(name)

    def del_local_var(self, name):
        """
        Deletes a local variable from the context by its name.
        """
        if name in self.data["local_vars"]:
            del self.data["local_vars"][name]

    def type_string_search(self, typ):
        """
        Searches for a type definition based on a TypeString instance.
        """
        if isinstance(typ, TypeString):
            type_name = typ.data
            struct_type = self.get_type_by_name(type_name)
            if struct_type is not None:
                return struct_type.gettype()
        return typ

    def enter_func(self, func):
        """
        Sets up the context for entering a function, including initializing local 
        variables and constants.
        """
        self.data["func"] = func
        self.data["local_vars"] = {}
        self.data["local_const"] = {}

        # add signature vars
        def query(x):
            return isinstance(x, TypeCluster)

        found, typ = self.query_annotation(query)
        if found:
            inputs, outputs = typ.get_inputs_outputs()
            if inputs is not None:
                for k, v in inputs.items():
                    self.add_local_var(k, Variable(
                        k), typ=self.type_string_search(type_annotation(v)))
            if outputs is not None:
                for k, v in outputs.items():
                    self.add_local_var(k, Variable(
                        k), typ=self.type_string_search(type_annotation(v)))

    def exit_func(self):
        """
        Cleans up the context after exiting a function, including clearing local variables
        and constants.
        """
        self.data["func"] = None
        self.data["local_vars"] = {}
        self.data["local_const"] = {}

    def enter_signature(self):
        """
        Prepares the context for entering a signature, enabling the addition of variables.
        """
        self.enable_add_var()
        self.data["signature"] = True

    def exit_signature(self):
        """
        Cleans up the context after exiting a signature, disabling the addition of variables.
        """
        self.disable_add_var()
        self.data["signature"] = False

    def is_signature(self):
        """
        Checks if the context is currently in a signature state.
        """
        return self.data["signature"]

    def get_func(self):
        """
        Retrieves the current function instance from the context.
        """
        return self.data.get("func")

    def backup_global_vars(self):
        """
        Backs up the current state of global variables and constants in the context.
        """
        self.data["global_vars_backup"] = {}
        self.data["const_backup"] = {}
        for k, v in self.data["global_vars"].items():
            self.data["global_vars_backup"][k] = v
        for k, v in self.data["const"].items():
            self.data["const_backup"][k] = v

    def restore_global_vars(self):
        """
        Restores the global variables and constants from the backup in the context.
        """
        self.data["global_vars"] = self.data["global_vars_backup"]
        self.data["global_vars_backup"] = {}
        self.data["const"] = self.data["const_backup"]
        self.data["const_backup"] = {}

    def enter_profile(self, prof):
        """
        Sets up the context for entering a profile, including backing up global variables.
        """
        self.backup_global_vars()
        self.data["profile"] = prof
        self.data["scope"] = "profile"
        self.data["local_shared_vars"] = {}

    def exit_profile(self):
        """
        Cleans up the context after exiting a profile, including restoring global variables.
        """
        self.data["profile"] = None
        self.data["scope"] = "global"
        self.restore_global_vars()
        self.data["local_shared_vars"] = {}

    def get_scope(self):
        """
        Determines the current scope of the context.
        """
        if self.data["scope"] == "global":
            return "global"
        if self.data.get("func") is not None:
            return "local"
        if self.data["signature"]:
            return "global"
        return "local_shared"

    def is_global_var(self, name):
        """
        Checks if a given variable name corresponds to a global variable in the context.
        """
        if self.data.get("func") is not None and name in self.data.get("local_vars"):
            return False
        if self.data.get("scope") == "profile" and name in self.data.get("local_shared_vars"):
            return False
        if name in self.data["global_vars"] and name not in self.data["const"]:
            return True
        return False

    def set_flag(self, name, value):
        """
        Sets a flag in the context.
        """
        self.data["flags"][name] = value

    def get_flag(self, name):
        """
        Retrieves the value of a flag from the context.
        """
        return self.data["flags"].get(name)

    def acquire_lock(self):
        """
        Activates the lock state in the context, indicating a locked or exclusive state.
        """
        self.data["locks"] = True

    def release_lock(self):
        """
        Deactivates the lock state in the context, indicating an unlocked or non-exclusive state.
        """
        self.data["locks"] = False

    def lock_state(self):
        """
        Checks the current lock state of the context.
        """
        return self.data["locks"]

class Indent:
    """
    A class to manage indentation levels for string formatting.
    """

    def __init__(self, ind=4):
        self.indent = ind
        self.level = 0

    def reset(self):
        """
        Resets the indentation level to zero.
        """
        self.level = 0

    def __enter__(self):
        """
        Increments the indentation level by one. Used in the context manager 'with' statement.
        """
        self.level += 1

    def __exit__(self, *args):
        """
        Decrements the indentation level by one. Used in the context manager 'with' statement.
        """
        self.level -= 1

    def __call__(self, s):
        """
        Applies the current indentation level to a given string.
        """
        sl = s.split("\n")
        target = "\n".join([" " * self.indent * self.level + i for i in sl])
        return target

class AnnContext:
    """
    The AnnContext class manages a collection of annotations, providing methods to add, 
    pop, query, and find specific types of annotations within its collection.
    """

    def __init__(self):
        self.annotations = []

    def add(self, annotation):
        """
        Adds a new annotation to the beginning of the annotations list.
        """
        self.annotations = [annotation] + self.annotations

    def pop(self):
        """
        Removes and returns the first annotation from the annotations list, if the list is not empty.
        """
        if len(self.annotations) > 0:
            ret = self.annotations[0]
            self.annotations = self.annotations[1:]
            return ret
        return None

    def query(self, func):
        """
        Searches for an annotation in the annotations list that meets a specified condition.
        """
        for a in self.annotations:
            if func(a):
                return True, a
        return False, None

    def find_type(self):
        """
        Finds the first occurrence of an AbstractTypeAnnotation within the annotations list.
        """
        for a in self.annotations:
            if isinstance(a, AbstractTypeAnnotation):
                return a
        return None

    def convert(self, indent=Indent()):
        """
        Converts all annotations in the list to their string representations and 
        concatenates them, separated by commas.
        """
        return ", ".join([convert(e) for e in self.annotations])


def get_annotation(data):
    """
    Parses a string to create and return the appropriate annotation object.

    :param data: A string containing the annotation type and content.
    :return: An instance of the corresponding annotation class, or None if no matching 
    type is found.
    """
    typ = data.split(" ")[0]
    content = " ".join(data.split(" ")[1:])
    if len(content.strip()) > 2 and content.strip()[-2:] == " {":
        content = content.strip()[:-2].strip()
    if typ == "type":
        return type_annotation(content.strip())
    if typ == "retry":
        return RetryAnnotation(content.strip())
    if typ == "new":
        return NewAnnotation(content.strip())
    return None


class Annotation:
    """
    The Annotation class represents a general annotation, storing its data and providing
    methods to parse and convert it.
    """

    def __init__(self, data):
        self.data = data
        self.parse()

    def parse(self):
        """
        Parses the data to extract the annotation type and content.
        """
        self.type = self.data.split(" ")[0]
        self.content = " ".join(self.data.split(" ")[1:])

    def convert(self, indent=Indent()):
        """
        Converts the annotation data to its string representation.
        """
        return self.data


class AbstractTypeAnnotation(Annotation):
    """
    The AbstractTypeAnnotation class extends the Annotation class, specifically for annotations 
    related to abstract types. It includes methods for type-specific functionalities.
    """

    def __init__(self, data):
        super().__init__(data)
        self.data = load_json(data)
        self.name = self.data

    def convert(self, indent=Indent()):
        return ""

    def is_type(self, typ, name=""):
        """
        Checks if the annotation is of a specific type.
        """
        return False

    def is_array(self):
        """
        Checks if the annotation represents an array type.
        """
        return False

    def is_struct(self):
        """
        Checks if the annotation represents an struct type.
        """
        return False

    def startswith(self, prefix, name=""):
        """
        Checks if the annotation's data starts with a given prefix.
        """
        return False

    def get_name(self):
        """ 
        Retrieves the name of the annotation.
        """
        return self.name


class TypeCluster(AbstractTypeAnnotation):
    """
    TypeCluster extends AbstractTypeAnnotation to represent a cluster of types, typically
    used for function signatures with inputs and outputs. It provides methods for type 
    checking, conversion, and retrieval of signature details.
    """

    def __init__(self, data) -> None:
        # super().__init__(data)
        assert isinstance(data, dict)
        self.data = data
        self.name = "cluster"

    def is_type(self, typ, name=""):
        """
        Checks if the type associated with the given name matches the specified type.
        """
        return self.data.get(name) == typ

    def startswith(self, prefix, name=""):
        """
        Checks if the type string associated with the given name starts with the 
        specified prefix.
        """
        type_str = self.data.get(name)
        if type_str is None:
            return False
        return type_str.startswith(prefix)

    def convert(self, indent=Indent()):
        """
        Converts the type cluster data into a JSON string representation.
        """
        return json.dumps(self.data)

    def sig_convert(self):
        """
        Converts the type cluster data into a signature representation, suitable for 
        function declarations.
        """
        sig = "({args}) ({ret})"
        args = rets = ""
        if "input" in self.data:
            args = ", ".join(['ienv stdp.PInterface'] +
                             [f"{k} {v}" for k, v in self.data["input"].items()])
        if "output" in self.data:
            rets = ", ".join(
                [f"{k} {v}" for k, v in self.data["output"].items()])
        sig = sig.format(args=args, ret=rets)
        if rets == "":
            sig = sig[:-2]
        return sig

    def get_inputs_outputs(self):
        """
        Retrieves the input and output types defined in the type cluster.
        """
        return self.data.get("input", {}), self.data.get("output", {})


class TypeString(AbstractTypeAnnotation):
    """
    TypeString extends AbstractTypeAnnotation to represent a simple string type. 
    It includes methods for type checking and conversion.
    """

    def __init__(self, data) -> None:
        super().__init__(data)
        assert isinstance(data, str)
        self.data = data
        self.name = data

    def is_type(self, typ, name=""):
        return self.data == typ

    def convert(self, indent=Indent()):
        return self.data

    def startswith(self, prefix, name=""):
        return self.data.startswith(prefix)


class TypeArray(AbstractTypeAnnotation):
    """
    TypeArray extends AbstractTypeAnnotation to represent an array type. 
    It provides methods for type checking, conversion, and array-specific functionalities.
    """

    def __init__(self, data) -> None:
        super().__init__(data)
        assert isinstance(data, str)
        self.data = data
        self.name = self.data

    def is_type(self, typ, name=""):
        return self.data == typ

    def is_array(self):
        return True

    def convert(self, indent=Indent()):
        return self.data

    def startswith(self, prefix, name=""):
        return self.data.startswith(prefix)


class TypeStruct(AbstractTypeAnnotation):
    """
    TypeStruct extends AbstractTypeAnnotation to represent a structure type. 
    It includes methods for parsing structure definitions, type checking, conversion 
    to code, and registration.
    """

    def __init__(self, data) -> None:
        """
        Initializes a TypeStruct instance with the given string data representing a structure definition.
        """
        super().__init__(data)
        assert isinstance(data, str)
        self.data = data
        self.struct = {}
        self.parse()

    def parse(self):
        """
        Parses the string data to extract the structure name and its declaration.
        Converts the declaration from JSON format into a dictionary.
        :raise Exception: If the structure declaration cannot be parsed.
        """
        self.data = self.data.strip()
        self.data = self.data[6:].strip()
        self.name = self.data.split(" ")[0]
        self.struct_decl = self.data[len(self.name):].strip()
        try:
            self.struct = json.loads(self.struct_decl)
        except Exception as exc:
            raise Exception("Cannot parse struct declaration",
                            self.struct_decl) from exc

    def is_type(self, typ, name=""):
        return self.name == typ

    def get_field_type(self, field):
        """
        Retrieves the type of a specified field within the structure.
        """
        return self.struct.get(field)

    def is_struct(self):
        """
        Checks if the annotation represents a structure type.
        """
        return True

    def convert(self, indent=Indent()):
        """
        Converts the structure data into a Go-like struct definition.
        """
        target_code = TypeStruct.convert_dict(self.struct)
        return target_code

    def register(self):
        """
        Generates a registration string for the structure type in TLA format.
        """
        return f"tla.RegisterStruct({self.name}{{}})"

    @staticmethod
    def convert_dict(dictionary):
        """
        Converts a dictionary representing a struct into a Go-like struct declaration.
        """
        indent = Indent()
        target_code = "{\n"
        with indent:
            for k, v in dictionary.items():
                if isinstance(v, dict):
                    target_code += indent(
                        f"{k}\t struct {TypeStruct.convert_dict(v)}") + "\n"
                else:
                    target_code += indent(f"{k}\t{v}") + "\n"
        target_code += "}"
        return target_code

    def startswith(self, prefix, name=""):
        return self.data.startswith(prefix)


def type_annotation(data):
    """
    Creates and returns the appropriate type annotation object based on the given data.
    """
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
    """
    NewAbstractTypeAnnotation extends AbstractTypeAnnotation and serves as a base class
    for new type annotations.
    """

    def __init__(self, data) -> None:
        super().__init__(data)
        self.data = data


class NewStruct(NewAbstractTypeAnnotation):
    """
    NewStruct extends NewAbstractTypeAnnotation to represent a new structure type. 
    It includes methods for conversion to code, type checking, and registration.
    """

    def __init__(self, data):
        super().__init__(data)
        self.data = data
        self.type = TypeStruct(data)

    def convert(self, indent=Indent()):
        return "type " + self.type.name + " struct " + self.type.convert()

    def is_type(self, typ, name=""):
        return self.type.is_type(typ, name)

    def is_struct(self):
        return True

    def gettype(self):
        """
        Retrieves the TypeStruct instance representing the structure.
        """
        return self.type

    def get_field_type(self, field):
        """
        Retrieves the type of a specified field within the new structure.
        """
        return self.type.get_field_type(field)

    def register(self):
        """
        Generates a registration string for the new structure type in TLA format.
        """
        return self.type.register()


def NewAnnotation(data):
    """
    Creates and returns a new structure annotation object based on the given data.
    """
    data = data.strip()
    # print("NewAnnotation", data, data.startswith("struct"))
    if data.startswith("struct"):
        return NewStruct(data)


class RetryAnnotation(Annotation):
    """
    RetryAnnotation extends Annotation to represent a retry mechanism with optional wait times. 
    It includes methods for conversion to code and generating retry logic.
    """

    def __init__(self, data):
        super().__init__(data)
        self.data = data.strip().split(" ")
        self.retry = self.data[0]
        if len(self.data) > 1:
            self.wait_code = self.parse_time(self.data[1])
        else:
            self.wait_code = ""

        if self.retry != "*":
            try:
                self.retry = int(self.retry)
            except:
                raise Exception("FairnessAnnotation must be a number or *")

    def convert(self, indent=Indent()):
        return " ".join(self.data)

    def parse_time(self, time_str):
        """
        Parses the given time string and converts it into Go-like sleep code.
        """
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

    def retry_code(self, code, err_handle):
        """
        Generates Go code for implementing retry logic based on the annotation data.
        """
        target_code = ""
        if self.retry == "*":
            target_code += "for err != nil {\n"
            target_code += f"    {code}\n"
            target_code += self.wait_code
            target_code += "}\n"
        else:
            target_code += f"for i := 0; i < {self.retry} && err != nil; i++ {{\n"
            target_code += f"    {code}\n"
            target_code += self.wait_code
            target_code += "}\n"
            target_code += "if err != nil {\n"
            target_code += f"    {err_handle}\n"
            target_code += "}\n"
        return target_code


def convert_performance(func_name, args):
    """
    Converts performance-related functions and their arguments into a string representation.
    """
    if func_name == "Time":
        return "Time(\"now\")"
    if func_name == "Report":
        assert len(args.data) == 2
        return f"__report := [k |-> {convert(args.data[0])}, v |-> {convert(args.data[1])}]"
    return f"{func_name}({convert(args)})"


def add_var_to_dict(d, n, v, raise_error=True):
    """
    Adds a variable to a dictionary if it does not already exist.
    """
    if n not in d:
        d[n] = v
        return True
    if raise_error:
        raise ValueError(f"Variable {n} already defined")
    return False




class StructValConverter:
    """
    StructValConverter is designed to convert values into a structured representation
    based on a provided struct definition. 
    It handles both named and anonymous struct conversions within a given context.
    """

    def __init__(self, struct_name, value, context) -> None:
        self.struct_name = struct_name
        self.value = value
        self.context = context
        self.is_anounymous = False
        if isinstance(self.struct_name, dict):
            self.struct_decl = self.struct_name
            self.is_anounymous = True
        else:
            self.struct_decl = self.context.get_type_by_name(self.struct_name)
            if self.struct_decl is None:
                raise Exception(
                    "Cannot find struct declaration", self.struct_name)

    def convert(self, indent=Indent()):
        """
        Converts the provided value into a structured representation based on the struct definition.
        """
        target_code = ""
        indent = Indent()
        if isinstance(self.value, Dict):
            value = self.value.to_dict()
        else:
            value = self.value
        if self.is_anounymous:
            go_struct = "struct " + TypeStruct.convert_dict(self.struct_name)
        else:
            go_struct = self.struct_name
        if isinstance(value, dict):
            target_code += f"{go_struct}{{\n"
            with indent:
                for k, v in value.items():
                    target_code += indent(
                        f"{k}: {self.convert_value(value=v, key=k)},") + "\n"
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
        """
        Converts an individual value based on the struct's field type. Handles nested 
        structures and different value types.
        """
        if isinstance(value, dict):
            if isinstance(self.struct_decl, NewStruct):
                field_type = self.struct_decl.get_field_type(key)
            else:
                field_type = self.struct_decl.get(key)
            if field_type is None:
                raise Exception("Cannot find field type",
                                key, self.struct_decl.name)
            return StructValConverter(field_type, value, self.context).convert()
        if isinstance(value, str):
            return f"{value}"
        return value


def convert_list(l, sep=" "):
    """
    Converts a list into a string representation, separated by the provided separator.
    """
    if isinstance(l, list):
        return "(" + sep.join(convert_list(x, sep) for x in l) + ")"
    else:
        return convert(l)


class ProfileObject:
    """
    A base class for different profile objects used in the context of code processing.
    This class serves as a template for more specific profile object types.
    """

    def __init__(self, data, m=None) -> None:
        """
        Initializes the ProfileObject.
        """

    def convert(self, indent=Indent()):
        """
        Converts the profile object to a PlusCal string representation.
        """
        return ""

    def get_name(self):
        """
        Retrieves the name of the profile object.
        """
        return ""

    def analyze(self, context=Context()):
        """
        Analyzes the profile object within a given context.
        """
        return

    def is_compound(self):
        """
        Checks if the profile object is a compound type.
        """
        return False

    def to_dict(self):
        """
        Converts the Dict object to a dictionary representation.
        """
        return {}


class Name(ProfileObject):
    """
    A class representing a name profile object.
    """

    def __init__(self, data, m=None) -> None:
        self.name = data

    def convert(self, indent=Indent()):
        return self.name

    def get_name(self):
        return self.name


class Number(ProfileObject):
    """
    A class representing a number
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)
        self.data = data[0]

    def convert(self, indent=Indent(), typed=False):
        if typed:
            return f"tla.MakeTLANumber(int({self.data}))"
        return self.data

    def get_name(self):
        return self.data


class KeyValue(ProfileObject):
    """
    Represents a key-value pair as a profile object.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)
        self.data = data
        self.key = data[0]
        self.value = data[1]

    def analyze(self, context=Context()):
        analyze(self.key, context)
        analyze(self.value, context)

    def convert(self, indent=Indent()):
        return f"{self.key} = {self.value}"


class Variable(ProfileObject):
    """
    Represents a variable as a profile object.
    """

    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.type = type_annotation("Default")
        self.is_profile_var = False
        self.scope = None
        self.profile = None
        self.func = None
        self.init = None
        self.init_op = "="
        self.m = m
        self.declared = False
        self.var = None

    def set_type(self, typ):
        """
        Sets the type of the variable.
        """
        self.type = typ

    def get_declared(self):
        """ 
        Retrieves the declared state of the variable.
        """
        return self.declared

    def get_scope(self):
        """
        Retrieves the scope (global, local shared or local) of the variable.
        """
        return self.scope

    def get_type(self, field=""):
        """
        Retrieves the type of the variable, or the type of a specific field if provided
        for struct variable.
        """
        if field == "":
            return self.type
        if self.type is None:
            return None
        if self.type.is_struct():
            typ = self.type.get_field_type(field)
            return typ
        return None

    def analyze(self, context=Context()):
        code_scope = context.get_scope()
        declared, var, scope = context.add_var(
            self.get_name(), self, code_scope)
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

    def typed_convert(self, indent=Indent()):
        """
        Converts the variable to its typed representation based on its type. 
        Handles different types such as string, integer, struct, and array.
        """
        name = self.convert()
        if self.type is None:
            return name
        if self.type.is_type("String", self.name):
            return f"tla.MakeTLAString({name})"
        if self.type.startswith("int", self.name):
            return f"tla.MakeTLANumber(int({name}))"
        if self.type.is_struct():
            return f"tla.MakeTLAStruct({name})"
        if self.type.is_array():
            return f"tla.MakeTLASet({name})"
        return name

    def convert(self, indent=Indent()):
        if self.scope == "local_shared":
            name = f"{default_profile_state_instance(self.profile.name.get_name())}.{convert(self.name)}"
            # traceback.print_stack()
        else:
            name = convert(self.name)
        return name

    def to_dict(self):
        return self.convert()

    def to_local(self):
        """
        Converts the variable to a local representation, specifically as a number.
        """
        return "AsNumber()"

    def init_code(self, init_process=None):
        """
        Generates the initialization code for the variable, handling different
        scenarios like global or local initialization.
        """
        init_op = self.init_op
        end = ";"
        # print(init_process, self.init_op)
        if init_process:
            self.is_profile_var = True
            process_set = convert(init_process).replace(
                '[', '{').replace(']', '}').replace('\'', '\"')
            # print("init_op", self.init_op)
            if self.init_op == "=":
                target = f"{self.convert()} = [p \in {process_set} |-> {convert(self.init)}];"
            else:
                target = f"{self.convert()} \in [{process_set} -> {convert(self.init)}];"
            # print(target)
            return target
        if isinstance(self.init, Suite):
            target = ""
            indent = Indent()
            target += f"{self.convert()} {init_op}\n "
            with indent:
                target += f"{indent(self.init.convert())}"
            return target
        return f"{self.convert()} {init_op} {convert(self.init)}{end}"


class Assign(ProfileObject):
    """
    Assign represents an assignment operation in the profile object. 
    It holds information about the variables, expressions, and scope involved in the assignment.
    """
    def __init__(self, data, m=None):
        self.m = m
        self.vars = [data[0]]
        self.exprs = [data[1]]
        self.is_declare = False
        self.var_scope = None
        self.var_type = ""
        self.var_name = self.vars[0].get_name()
        self.func = None
        self.in_func = False
        self.global_read = ""
        self.global_write = ""
        self.retry = ""
        self.context = None
        self.retry_annotation = None

    def analyze(self, context=Context()):
        self.func = context.get("func")
        if self.func is not None:
            self.in_func = True

        context.enable_add_var()
        analyze(self.vars[0], context)
        context.disable_add_var()
        analyze(self.exprs[0], context)

        self.var_type = self.vars[0].get_type()
        self.is_declare = not self.vars[0].get_declared()
        self.var_scope = self.vars[0].get_scope()
        if isinstance(self.vars[0], GetItem) or isinstance(self.vars[0], GetAttr):
            self.is_declare = False
            self.var_scope = "local"

        self.global_read = ""
        self.global_write = False
        if self.var_scope == "global":
            self.global_write = True

        expr_str = convert(self.exprs[0])
        if context.is_global_var(expr_str):
            self.global_read = expr_str

        def retry_func(x):
            return isinstance(x, RetryAnnotation)
        self.retry, self.retry_annotation = context.query_annotation(
            retry_func)
        self.context = context

    def type_wrap(self, expr):
        """
        Wraps the expression in the appropriate type based on the variable's type. 
        Handles different types like string, array, and struct.
        """
        if self.var_type is None:
            print("Warning: var_type is None", self.var_name, self.m.line)
        if self.var_type is None or self.var_type.is_type("String", self.var_name) or self.var_type.is_type("", self.var_name):
            return expr
        if self.var_type.is_array():
            if expr.strip().startswith("{"):
                return f"{self.var_type.convert()}{expr}"
            else:
                return expr
        if self.var_type.is_struct() and isinstance(self.exprs[0], Dict):
            return self.type_wrap_struct(self.exprs[0])
        return f"{self.var_type.convert()}({expr})"

    def type_wrap_struct(self, expr):
        """
        Specifically wraps a struct expression in its appropriate type.
        """
        struct_name = self.var_type.name
        value = expr
        context = self.context
        return StructValConverter(struct_name, value, context).convert()

    def get_var(self):
        """
        Retrieves the variable involved in the assignment.
        """
        return self.vars[0]

    def get_vars_name(self):
        """
        Retrieves the name of the variable involved in the assignment.
        """
        return self.vars[0].get_name()

    def get_assign_expr(self):
        """
        Retrieves the expression part of the assignment.
        """
        return self.exprs[0]

    @staticmethod
    def type_convert(var, global_read):
        """
        Converts a variable to its appropriate type based on global read status and 
        the variable's type.
        """
        if global_read == "":
            return ""
        if var.type is None:
            return ""
        if var.type.is_type("string", var.get_name()):
            return ".AsString()"
        if var.type.startswith("int", var.get_name()):
            return ".AsNumber()"
        if var.type.startswith("bool", var.get_name()):
            return ".AsBool()"
        return f".AsStruct().({var.type.name})"

    def type_reverse_convert(self, expr):
        """
        Reverses the type conversion of an expression to match the variable's type.
        """
        if self.var_type is None:
            return expr
        if self.var_type.is_type("String", self.var_name):
            return f"tla.MakeTLAString({expr})"
        if self.var_type.startswith("int", self.var_name):
            return f"tla.MakeTLANumber(int({expr}))"
        if self.var_type.is_struct():
            return f"tla.MakeTLAStruct({expr})"
        assert False
        return expr

    def read_global_from_env(self, err_handle):
        """
        Generates code to read a global variable from the environment.
        """
        target_code = ""
        global_var_name = f"global{capitalize(self.global_read)}" + \
            str(self.m.line)
        target_code += f"{global_var_name}, err := ienv.Read(\"{self.global_read}\")" + "\n"
        retry_code = f"{global_var_name}, err = ienv.Read(\"{self.global_read}\")"
        if self.retry:
            target_code += self.retry_annotation.retry_code(
                retry_code, err_handle)
        else:
            target_code += "if err != nil {\n"
            target_code += f"    {err_handle}\n"
            target_code += "}\n"
        right = global_var_name
        return right, target_code

    def write_global(self, right, err_handle):
        """
        Generates code to write a global variable to the environment.
        """
        target_code = ""
        var_name = self.vars[0].get_name()
        target_code += f"err = ienv.Write(\"{var_name}\", {self.type_reverse_convert(right)}) \n"
        target_code += "if err != nil {\n"
        target_code += f"    {err_handle}\n"
        target_code += "}\n"
        return target_code

    def write_local(self, right, err_handle):
        """
        Generates code to handle local variable assignment.
        """
        target_code = ""
        read_global_to_struct = len(self.global_read) > 0 and isinstance(
            self.vars[0], NewStruct)
        if read_global_to_struct:
            target_code += f"{self.vars[0].convert()}, err"
        else:
            target_code += f"{self.vars[0].convert()}"
        if self.is_declare:
            target_code += " := "
            # for example: result := netRead.AsStruct().(NetRead)
            target_code += self.type_wrap(
                f"{right}{Assign.type_convert(self.vars[0], self.global_read)}")
        else:
            target_code += " = "
            if self.var_type is not None and ((self.var_type.is_array() and isinstance(self.exprs[0], List)) or (self.var_type.is_struct() and isinstance(self.exprs[0], Dict))):
                target_code += self.type_wrap(
                    f"{right}{Assign.type_convert(self.vars[0],self.global_read)}")
            else:
                target_code += f"{right}{Assign.type_convert(self.vars[0],self.global_read)}"
        if read_global_to_struct:
            target_code += "\n"
            target_code += "if err != nil {\n"
            target_code += f"    {err_handle}\n"
            target_code += "}\n"
        return target_code

    def convert(self, indent=Indent()):
        err_handle = ""
        if self.func is not None:
            err_handle = self.func.err_handle()

        target_code = ""
        right = convert(self.exprs[0])
        if len(self.global_read) > 0:
            right, read_code = self.read_global_from_env(err_handle)
            target_code += read_code
        if self.var_scope == "local" or self.var_scope == "local_shared":
            target_code += self.write_local(right, err_handle)
        else:
            target_code += self.write_global(right, err_handle)
        return target_code


class ConstAssign(ProfileObject):
    """
    ConstAssign represents a constant assignment operation. It ensures that the 
    assignment is valid and permissible in the given context.
    """
    def __init__(self, data, m=None):
        self.data = data[0]
        self.m = m

    def analyze(self, context=Context()):
        context.set_flag("is_const", True)
        analyze(self.data, context)
        if not self.data.is_declare:
            raise Exception(
                "Cannot change the value of a constant", self.m.line)
        if len(self.data.global_read) > 0:
            raise Exception(
                "Cannot assign a global variable to a constant", self.m.line)
        context.set_flag("is_const", False)

    def convert(self, indent=Indent()):
        target_code = f"const {self.data.get_vars_name()} = {convert(self.data.get_assign_expr())}"
        return target_code


class Comparison(ProfileObject):
    """
    Comparison represents a comparison operation between two entities. It includes 
    methods to analyze and convert the comparison to a Go representation.
    """
    def __init__(self, data, m=None):
        self.data = data
        self.left = data[0]
        self.right = data[2]
        self.op = self.convert_comp_op(data[1][0].value)
        self.m = m

    def analyze(self, context=Context()):
        analyze(self.left, context)
        analyze(self.right, context)

    def convert_comp_op(self, op):
        """
        Converts a comparison operator to its equivalent representation in the Go.
        """
        op_mapping = {
            "==": "==",
            "!=": "!=",
            "in": "\\in",
        }
        if op in op_mapping:
            return op_mapping[op]
        return op

    def get_var(self):
        """
        Retrieves the variable involved in the comparison.
        """
        return self.left

    def is_in_op(self):
        """
        Checks if the comparison operation is an IN operation.
        """
        return self.op == "\\in"

    def convert(self, indent=Indent()):
        target = ""
        if isinstance(self.left, FuncCall) and self.left.is_procedure:
            target += f"{convert(self.left)}\nL{self.m.line}:\n"
            if isinstance(self.right, FuncCall) and self.right.is_procedure:
                target += f"{convert(self.left)}\nL{self.m.line}_1:\n"
                target += f"Head(Tail(__call_stack[self])) {self.op} Head(__call_stack[self]);\n"
                target += "__call_stack[self] := Tail(Tail(__call_stack[self]))"
            else:
                target += f"Head(__call_stack[self]) {self.op} {convert(self.right)}"
        else:
            if isinstance(self.right, FuncCall) and self.right.is_procedure:
                target += f"{convert(self.right)}\nL{self.m.line}:\n"
                target += f"{convert(self.left)} {self.op} Head(__call_stack[self]);\n"
                target += "__call_stack[self] := Tail(__call_stack[self])"
            else:
                target += f"{convert(self.left)} {self.op} {convert(self.right)}"
        return target


class Parameters(ProfileObject):
    """
    Parameters represents a collection of parameters. It includes methods to analyze
    and convert the parameters to a Go representation.
    """
    def __init__(self, data, m=None):
        self.data = data
        self.is_argu = None

    def analyze(self, context=Context()):
        self.is_argu = context.get("is_argu")
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
        target = ""
        line_end = '\n' if self.is_argu else ''
        for a in self.data:
            if a is None:
                continue
            target += f"{convert(a)}, " + line_end
        target = target[:-2-len(line_end)]
        return target

    def fetch_argus_from_stack(self):
        """
        Generates code to fetch arguments from a call stack.
        """
        target = ""
        j = 0
        for i, a in enumerate(self.data):
            if a is None:
                continue
            j += 1
            tail = "Tail("*i
            end = ")"*(i+1) + ";\n"
            target += f"{convert(a)} := Head(" + tail + \
                "__call_stack[name]" + end
        target += "__call_stack[name] := " + \
            "Tail("*j + "__call_stack[name]" + ")"*j + ";\n"
        return target


class FuncDef(ProfileObject):
    """
    FuncDef represents the definition of a function within a profile object. 
    It handles the analysis and conversion of function definitions, including arguments and suite of operations.
    """
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
        self.func_name = ""
        self.call_func_name = ""
        self.actor_name = ""
        self.call_actor_name = ""
      

    def analyze(self, context=Context()):
        self.profile = context["profile"]
        if self.profile is not None:
            self.prefix = f"{self.profile.get_name()}"
        def query(x):
            return isinstance(x, TypeCluster)
        has_type, ann = context.query_annotation(query)
        self.sig_type = ann if has_type else None
        context.enter_func(self)
        analyze(self.name, context)
        context["is_argu"] = True
        analyze(self.args, context)
        del context["is_argu"]
        analyze(self.suite, context)
        self.func_name = f"{self.prefix}{capitalize(convert(self.name))}"
        self.call_func_name = f"{self.profile.default_profile_state_instance()}.{self.prefix}{capitalize(convert(self.name))}"
        self.actor_name = f"{self.prefix}Actor{capitalize(convert(self.name))}"
        self.call_actor_name = f"{self.profile.default_profile_state_instance()}.{self.prefix}Actor{capitalize(convert(self.name))}"
        context.exit_func()

    def get_suite_statements(self):
        """
        Retrieves the suite of statements or operations defined in the function.
        """
        return self.suite.statements

    def set_type(self, def_type, prefix=""):
        """
        Sets the type and prefix for the function definition.
        """
        self.def_type = def_type
        self.prefix = prefix

    def get_args(self):
        """
        Generates and returns the string representation of function arguments for the function call.
        """
        inputs = {}
        if self.sig_type is not None:
            inputs, _ = self.sig_type.get_inputs_outputs()
        fetch_inputs = ""
        for i, k in enumerate(inputs):
            fetch_inputs += f"{k} := input[{i}].({inputs[k]})" + "\n"
        fetch_inputs = remove_blank_line(fetch_inputs)
        return fetch_inputs

    def push_results(self):
        """
        Generates and returns the string representation of code to push function results.
        """
        _, outputs = self.sig_type.get_inputs_outputs()
        fetch_outputs = ""
        for _, k in enumerate(outputs):
            fetch_outputs += f"output = append(output, {k})" + "\n"
        if len(fetch_outputs) > 0 and fetch_outputs[-1] == "\n":
            fetch_outputs = fetch_outputs[:-1]
        return fetch_outputs

    def get_result(self, all_vars, tmp_result):
        """
        Generates code to handle the function's result based on given variables and 
        a temporary result holder.
        """
        target = ""
        _, outputs = self.sig_type.get_inputs_outputs()
        if len(outputs) != len(all_vars):
            return target
        values = list(outputs.values())
        # print(values)
        for i, _ in enumerate(outputs):
            target += f"{all_vars[i]} = {tmp_result}[{i}].({values[i]})" + "\n"
        return target

    def call_func(self, inputs, outputs):
        """
        Generates the function call code based on the specified inputs and outputs.
        """
        target = ""
        if outputs is not None and len(outputs) > 0:
            result = ", ".join(outputs.keys())
            target = result + " := "
        target += f"{self.profile.default_profile_state_instance()}.{self.prefix}{capitalize(convert(self.name))}({', '.join(['ienv'] + list(inputs.keys()))})"
        return target

    def convert(self, indent=Indent()):
        sig_type = self.sig_type
        inputs = outputs = {}
        if sig_type is not None and isinstance(sig_type, TypeCluster):
            inputs, outputs = sig_type.get_inputs_outputs()

        target = ""
        func_def = self.convert_func(inputs, outputs)
        target += func_def + "\n\n"
        actor_def = self.convert_actor(inputs, outputs)
        target += actor_def
        return target

    def sig_convert(self, inputs, outputs):
        """
        Converts the function signature based on its inputs and outputs.
        """
        sig = "({args}) ({ret})"
        args = rets = ""
        if inputs is not None:
            args = ", ".join(['ienv stdp.PInterface'] +
                             [f"{k} {v}" for k, v in inputs.items()])
        if outputs is not None:
            rets = ", ".join([f"{k} {v}" for k, v in outputs.items()])
        sig = sig.format(args=args, ret=rets)
        if rets == "":
            sig = sig[:-2]
        return sig

    def convert_func(self, inputs, outputs, indent=Indent()):
        """
        Converts the function definition, including its signature, to a string 
        representation suitable for the Go.
        """
        indent = Indent()
        sig = self.sig_convert(inputs, outputs)
        ins = ""
        if self.profile is not None:
            ins = f"({self.profile.default_profile_state_instance()} *{self.profile.default_profile_state()})"
        target = f"{self.def_type} {ins} {self.func_name} {sig} {{\n"
        with indent:
            if "err" not in inputs and "err" not in outputs:
                target += indent("var err error") + "\n"
                target += indent("_ = err") + "\n"
            target += indent(self.suite.convert())+"\n"
        target += "}"
        return target

    def convert_actor(self, inputs, outputs, indent=Indent()):
        """
        Converts the actor version of the function definition, suitable for concurrency 
        handling in the Go.
        """
        ins = ""
        if self.profile is not None:
            ins = f"({self.profile.default_profile_state_instance()} *{self.profile.default_profile_state()})"
        target = f"{self.def_type} {ins} {self.actor_name}(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{{}}, outputs chan []interface{{}})  {{\n"

        with indent:
            target += indent(
                """for {
""")
            if outputs is not None and len(outputs) > 0:
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
                    if outputs is not None and len(outputs) > 0:
                        target += indent(self.push_results()) + "\n"
                        target += indent("outputs <- output") + "\n"
                        target += indent("output = []interface{}{}") + "\n"
                target += indent("}") + "\n"
            target += indent("}")
        target += "\n}"
        return target

    def expand_code(self, indent=Indent()):
        """
        Expands and formats the suite of operations within the function for the Go.
        """
        target = indent(self.suite.convert() + "\nreturn")
        return target

    def err_handle(self):
        """
        Generates error handling code for the function based on its signature.
        """
        if self.sig_type is None:
            return ""
        _, outputs = self.sig_type.get_inputs_outputs()
        if outputs is None or len(outputs) == 0:
            all_vars = ""
        else:
            all_vars = ", ".join(list(outputs.keys()))
        return f"if err != nil {{\n    return {all_vars}\n}}\n"


class ProcDef(FuncDef):
    """
    ProcDef represents the definition of a procedure, extending the functionalities of FuncDef. 
    It is specifically used for defining procedures within a profile.
    """

class ReturnStmt(ProfileObject):
    """
    ReturnStmt represents a return statement within a profile object.
    """
    def __init__(self, data, m=None) -> None:
        self.expr = data
        self.m = m

    def analyze(self, context=Context()):
        analyze(self.expr, context)

    def convert(self, indent=Indent()):
        target = "return"
        return target


class OpDef(FuncDef):
    """
    OpDef represents the definition of an operation, extending the functionalities of FuncDef. 
    It specifically deals with operations within a profile context.
    """
    def __init__(self, data, m=None) -> None:
        super().__init__(data)

    def analyze(self, context=Context()):
        context = deepcopy(context)
        context["scope"] = "op"
        context["op"] = self
        analyze(self.suite, context)
        profile = context.get("profile")
        if profile is not None:
            self.prefix = profile.name.get_name()

    def convert(self, indent=Indent()):
        indent = Indent()
        target = f"{self.prefix}_{convert(self.name)}({convert(self.args)}) == \n"
        with indent:
            target += indent(self.suite.convert())
        return target


class MacroDef(FuncDef):
    """
    MacroDef represents the definition of a macro, extending the functionalities of FuncDef.
    It is used for defining macros within a profile context.
    """
    def analyze(self, context=Context()):
        return super().analyze(context)

    def convert(self, indent=Indent()):
        return ""


class List(ProfileObject):
    """
    List represents a list of elements within a profile object.
    """
    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
        target = "{"
        for i in self.data:
            target += f"{convert(i)}, "
        if len(self.data) > 0:
            target = target[:-2]
        target += "}"
        return target

    def to_dict(self):
        ret = []
        for i in self.data:
            if isinstance(i, ProfileObject):
                ret.append(i.to_dict())
            else:
                ret.append(i)
        return ret


class Dict(ProfileObject):
    """
    Dict represents a dictionary or map structure within a profile object. 
    It is used for handling key-value pair data structures.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)
        self.data = data

    def to_dict(self):
        ret = {}
        for key_value in self.data:
            key = key_value[0]
            value = key_value[2]
            if isinstance(value, ProfileObject):
                value = value.to_dict()
            elif isinstance(value, str):
                value = "\"" + value + "\""
            ret[key] = value
        return ret

    def convert_key(self, key):
        """
        Converts a key into a suitable string format for conversion.
        """
        if isinstance(key, str):
            return key
        return convert(key)

    def analyze(self, context=Context()):
        for key_value in self.data:
            analyze(key_value[0], context)
            analyze(key_value[2], context)

    def convert(self, indent=Indent()):
        target = "{"
        for key_value in self.data:
            if key_value[1].value == "->":
                target += f"{self.convert_key(key_value[0])} : {convert(key_value[2])}, "
            else:
                target += f"{self.convert_key(key_value[0])} : {convert(key_value[2])}, "
        if len(self.data) > 0:
            target = target[:-2]
        target += "}"
        return target


class Set(ProfileObject):
    """
    Set represents a collection of elements within a profile object, similar to a mathematical or programming set.
    """
    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
        target = "{"
        for i in self.data:
            target += f"{convert(i)}, "
        target = target[:-2]
        target += "}"
        return target

    def to_dict(self):
        ret = []
        for i in self.data:
            if isinstance(i, ProfileObject):
                ret.append(i.to_dict())
            else:
                ret.append(i)
        return ret


class Term(ProfileObject):
    """
    Term represents a term within a mathematical or logical expression in a profile object.
    """
    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
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
    """
    Represents a logical 'or' expression derived from Term.
    """

class AndExpr(Term):
    """
    Represents a logical 'and' expression derived from Term.
    """


class XorExpr(Term):
    """
    Represents a logical 'xor' expression derived from Term.
    """
    def convert(self, indent=Indent()):
        return f"({convert(self.data[0])} ^ {convert(self.data[1])})"


class ArithExpr(Term):
    """
    Represents an arithmetic expression derived from Term.
    """


class ShiftExpr(Term):
    """
    Represents a shift expression (e.g., bit shift) derived from Term.
    """

class Factor(ProfileObject):
    """
    Represents a factor in an expression, potentially including an operation.

    Attributes:
        op (str): The operator associated with the factor, if any.
        data: The data representing the factor.
    """

    def __init__(self, data, m=None) -> None:
        try:
            self.op = data[0].value
        except Exception as e:
            print("error")
            print(e)
            print(data[0])
        self.data = data[1]
        # print(self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        has_space = " " if len(self.op) > 1 else ""
        return f"({self.op}" + has_space + f"{convert(self.data)})"


class Comment(ProfileObject):
    """
    Comment represents a comment or annotation within a profile object. 
    It can handle different types of comments including regular comments and annotations.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        if self.data.startswith("#@"):
            self.type = "annotation"
            self.ann = get_annotation(self.data[2:])
        elif self.data.strip().startswith("#}"):
            self.type = "end_annotation"
        else:
            self.type = "comment"

    def analyze(self, context=Context()):
        if self.type == "annotation":
            context.add_annotation(self.ann)
        elif self.type == "end_annotation":
            context.pop_annotation()
        else:
            pass

    def convert(self, indent=Indent()):
        return ""


class Newline(ProfileObject):
    """
    Newline represents a newline in the profile object, often used for formatting and readability purposes.
    """
    def __init__(self, data, m=None) -> None:
        self.data = []
        for i in data:
            if isinstance(i, Comment):
                self.data.append(i)

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
        target = ""
        for i in self.data:
            convi = convert(i)
            if len(convi) > 0:
                target += i.convert() + "\n"
        return target


class SimpleStmt(ProfileObject):
    """
    SimpleStmt represents a simple statement within a profile object. 
    It can handle various types of simple statements like assignments.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def simple_assign(self, types):
        """
        Identifies and returns a simple assignment operation from the statement if present.
        """
        for i in self.data:
            for typ in types:
                if isinstance(i, typ):
                    return i
        return None

    def analyze(self, context=Context()):
        """
        Analyzes each component within the simple statement in the given context.
        """
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
        target = ""
        for i in self.data:
            convi = convert(i)
            if len(convi) > 0:
                target += convi + "\n"
        if len(target) > 0 and target[-1] == "\n":
            target = target[:-1]
        return target


class Suite(ProfileObject):
    """
    Represents a collection of statements or expressions, often within a block or a function body.

    Attributes:
        statements: A list of statements or expressions that form the suite.
        is_expr (bool): Indicates whether the suite is part of an expression context.
    """

    def __init__(self, data, m=None) -> None:
        self.statements = data
        self.is_expr = False

    def analyze(self, context=Context()):
        self.is_expr = context.get(
            "op") is not None or context.get("is_expr") == True
        for statement in self.statements:
            analyze(statement, context)

    def convert(self, indent=Indent()):
        target_code = ""
        for statement in self.statements:
            try:
                convs = convert(statement)
                # if len(convs) > 0 and convs[-1] != ";"and convs[-1] != "\n" and not self.is_expr and not isinstance(statement, (LabelStmt)):
                if len(convs) > 0 and convs[-1] != ";" and convs[-1] != "\n" and not self.is_expr and not isinstance(statement, (LabelStmt)):
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
        return target_code


class AnnAssign(ProfileObject):
    """
    Represents an annotated assignment statement.
    """

    def __init__(self, data, m=None):
        self.label = data[1]

    def analyze(self, context=Context()):
        analyze(self.label, context)

    def convert(self, indent=Indent()):
        return f"{convert(self.label)}:"


class LabelStmt(ProfileObject):
    """
    Represents a label statement, used for marking atomic blocks in code.
    """

    def __init__(self, data, m=None):
        self.label = data[0]
        self.context = ""
        self.lock = ""

    def analyze(self, context=Context()):
        func = context.get("func")
        if func is not None:
            self.context = "__"+func.prefix + "_" + func.name.get_name()
        analyze(self.label, context)
        label_name = convert(self.label)
        if label_name.startswith("Atom") and not context.lock_state():
            self.lock = "lock"
            context.acquire_lock()
        elif context.lock_state():
            self.lock = "release"
            context.release_lock()
        else:
            self.lock = ""

    def convert(self, indent=Indent()):
        if self.lock == "lock":
            return f"ienv.Write(\"lock\", \"Acquire\")"
        elif self.lock == "release":
            return f"ienv.Write(\"lock\", \"Release\")"
        else:
            return ""


class AwaitExpr(ProfileObject):
    """
    Represents an 'await' expression.
    """

    def __init__(self, data, m=None):
        self.data = data[1]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return f"await {convert(self.data)}"


class Slice(ProfileObject):
    """
    Represents a slice operation on data structures like arrays or lists.
    """

    def __init__(self, data, m=None):
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)

    def convert(self, indent=Indent()):
        return f"{convert(self.data[0])}, ({convert(self.data[1])})"


class GetItem(ProfileObject):
    """
    Represents a 'get item' operation, typically used for accessing elements in a data
    structure by index or key.
    """

    def __init__(self, data, m=None):
        self.data = data
        self.type = None
        self.declared = False
        self.scope = ""

    def set_type(self, typ):
        """
        Sets the type of the item being accessed.
        """
        self.type = typ

    def get_declared(self):
        """
        Retrieves the declared status of the variable being accessed.
        """
        return self.declared

    def get_scope(self):
        """
        Retrieves the scope of the variable being accessed.
        """
        return self.scope

    def get_type(self, field=""):
        """
        Retrieves the type of the item or a specific field within a structured item being accessed.
        """
        if field == "":
            return self.type
        if self.type.is_struct():
            return self.type.get_field_type(field)
        return None

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)
        if isinstance(self.data[0], Variable):
            self.type = self.data[0].get_type(convert(self.data[1]))
            self.declared = self.data[0].get_declared()
            self.scope = self.data[0].get_scope()

    def convert_read(self):
        pass

    def convert_write(self):
        pass

    def convert(self, indent=Indent()):
        if self.data[0].is_compound():
            if isinstance(self.data[1], Slice):
                return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
            return f"({convert(self.data[0])})[{convert(self.data[1])}]"
        if isinstance(self.data[1], Slice):
            return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
        return f"{convert(self.data[0])}[{convert(self.data[1])}]"

    def typed_convert(self):
        """
        Converts the 'get item'.
        """
        return self.convert()

    def to_dict(self):
        return self.convert()


class GetAttr(Variable):
    """
    Represents an attribute access operation on an object, extending from the Variable class.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        self.obj = data[0]
        self.attr = data[1]
        self.extra_argu = ""
        self.type = None
        self.libs = None
        self.scope = None
        self.global_access = False
        self.name = self
        self.declared = True
        self.context = None

    def analyze(self, context=Context()):
        self.libs = context.get("libs")
        context.enable_add_var()
        analyze(self.obj, context)
        context.disable_add_var()
        analyze(self.attr, context)
        if isinstance(self.obj, Variable) and self.obj.get_scope() == "global":
            self.global_access = True
        self.context = context

    def get_var(self):
        """
        Return the variable of the getattr expression
        """
        return self

    def get_name(self):
        return self.attr.get_name()

    def get_obj_name(self):
        """ 
        Retrieves the name of the object being accessed.
        """
        return self.obj.get_name()

    def get_access(self):
        """ 
        Checks if the attribute access operation is a global access.
        """
        return self.global_access


    def init_code(self, init_process=False):
        init_op = self.init_op
        end = ";"
        if isinstance(self.init, Suite):
            target = ""
            indent = Indent()
            target += f"{convert(self.name)} {init_op}\n "
            with indent:
                target += f"{indent(self.init.convert())}"
            return target
        return f"{self.convert()} {init_op} {convert(self.init)}{end}"

    def convert_read(self, obj):
        """
        Generates a read operation string for a global object.
        """
        return f"ienv.Read(\"{obj}\", "

    def convert_write(self, obj):
        """
        Generates a write operation string for a global object.
        """
        return f"ienv.Write(\"{obj}\", "

    def convert_global(self):
        """
        Generates a Go opration string for accessing a global object.
        """
        action = convert(self.attr)
        obj = convert(self.obj)
        if action == "read":
            return obj, action, self.convert_read(obj)
        elif action == "write":
            return obj, action, self.convert_write(obj)
        else:
            return "", "", ""

    def get_global_access(self):
        """
        Checks if the attribute access operation is a global access.
        """
        return self.global_access

    def convert(self, indent=Indent()):
        attr = convert(self.attr)
        obj = convert(self.obj)
        if self.obj.is_compound():
            return f"({obj}).{attr}"
        return f"{obj}.{attr}"


class FuncCall(ProfileObject):
    """
    Represents a function call, encapsulating details about the function name, arguments, 
    and other properties.
    """

    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.args = data[1]
        self.is_procedure = False
        self.target = None
        self.global_access = False
        self.m = m
        self.profile = None
        self.retry = ""
        self.retry_annotation = ""
        self.context = None

    def analyze(self, context=Context()):
        profile = context.get("profile")
        analyze(self.name, context)
        analyze(self.args, context)
        self.profile = profile
        if profile is not None:
            try:
                if isinstance(self.name, GetAttr):
                    self.global_access = self.name.get_global_access()
                else:
                    self.global_access = False
            except Exception as e:
                print(e)
                traceback.print_exc()

        def retry_func(x):
            return isinstance(x, RetryAnnotation)
        self.retry, self.retry_annotation = context.query_annotation(
            retry_func)
        self.context = context

    def convert(self, indent=Indent()):
        def check_recv(func_name):
            splits = func_name.split(".")
            if len(splits) > 1 and splits[1] == "Recv":
                return True
            return False
        if self.target is not None:
            return self.target
        if self.global_access:
            obj, action, target = self.name.convert_global()
            if action == "write":
                target = f"err = {target}{', '.join(typed_convert(self.args))})"
                if self.retry:
                    target += "\n" + \
                        self.retry_annotation.retry_code(target, err_handle="")
            else:
                if self.args is not None and len(self.args) == 0:
                    raise Exception("global read must have args")
                global_var_name = f"global{capitalize(obj)}" + str(self.m.line)
                retry_code = f"{global_var_name}, err = {target}{', '.join(typed_convert(self.args[1:]))})\n"
                target = f"{global_var_name}, err := {target}{', '.join(typed_convert(self.args[1:]))})\n"
                if self.retry:
                    target += "\n" + \
                        self.retry_annotation.retry_code(
                            retry_code, err_handle="")
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
                    if self.profile is not None:
                        args_name = "ienv, " + \
                            f"{self.profile.default_profile_state_instance()}.{self.profile.get_name()}" + \
                            "Actor" + capitalize(args_name)
                func_name = UTIL_FUNC[func_name]
                target = f"{func_name}({args_name})"
            elif check_recv(func_name):
                if fn is None:
                    target = f"{func_name}({', '.join(convert(self.args))})"
                else:
                    all_vars = convert(self.args)
                    tmp_result = "outputTmp"+str(self.m.line)
                    target = f"{tmp_result} := {func_name}()" + "\n"
                    target += fn.get_result(all_vars, "outputTmp"+str(self.m.line))
            elif fn is not None:
                args_name = convert(self.args)
                if isinstance(args_name, list):
                    args_name = ", ".join(args_name)
                target = f"{fn.call_func_name}( {'ienv, ' + args_name})"
            else:
                target = f"{func_name}({', '.join(convert(self.args))})"
        return target

    def to_dict(self):
        return self.convert()


class Arguments(ProfileObject):
    """
    Represents arguments in a function or method call.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        for arg in self.data:
            analyze(arg, context)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def convert(self, indent=Indent()):
        return convert(self.data)

    def typed_convert(self):
        """
        Directly converts the arguments to a string representation.
        """
        return self.convert(self.data)


class Profile(ProfileObject):
    """
    Represents a profile object encapsulating various components like variables, procedures, 
    and processes.
    """
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
        self.local_shared_vars = {}

        self.__has_process = False
        self.__is_env = False

        self.init = None

    def is_env(self):
        """ 
        Check if the profile is an environment profile.
        """
        return self.__is_env

    def to_dict(self):
        ret = {}
        for var_name, var in self.vars.items():
            ret[var_name] = var.to_dict()
        return ret

    def has_init(self):
        """ 
        Check if the profile has an init function.
        """
        return self.init is not None

    def analyze(self, context=Context()):
        global_vars = context.get("global_vars")
        instances = context.get("instances")
        info = instances.get(self.name.get_name())
        if info is not None:
            if info.get("range") is not None:
                self.instances = info.get("range")
            else:
                self.instances = info.get("vars")
        else:
            self.instances = []

        context.enter_profile(self)
        global_vars = deepcopy(context.get("global_vars"))
        def query(x):
            return isinstance(x, AbstractTypeAnnotation)
        has_type, ann = context.query_annotation(query)
        if has_type and ann.is_type("env"):
            self.__is_env = True

        for statement in self.suite.statements:
            if isinstance(statement, SimpleStmt) and statement.simple_assign([Assign, ConstAssign, Comparison]) is not None:
                statement = statement.simple_assign(
                    [Assign, ConstAssign, Comparison])
            if isinstance(statement, Assign) or (isinstance(statement, Comparison) and statement.op == "\in"):
                var = statement.get_var()
                if var.get_name() not in global_vars:
                    self.vars[var.get_name()] = var
                    self.symbols[var.get_name()] = var
            elif isinstance(statement, FuncDef):
                self.symbols[statement.name.get_name()] = statement
                name = statement.name.get_name()
                if name == "init":
                    self.init = statement
                    self.process_init()
                    self.procedures[statement.name.get_name()] = statement
                else:
                    self.procedures[statement.name.get_name()] = statement
            elif isinstance(statement, OpDef):
                self.operators[statement.name.get_name()] = statement
            elif isinstance(statement, ProcDef):
                self.processes[statement.name.get_name()] = statement
                self.__has_process = True
            else:
                continue
        context.enter_signature()
        analyze(self.args, context)
        context.exit_signature()

        for statement in self.suite.statements:
            analyze(statement, context)
        self.local_shared_vars = context.get_local_shared_vars()
        context.exit_profile()

    def has_process(self):
        """
        Checks if the profile contains any process definitions.
        """
        return self.__has_process

    def get_process_name(self):
        """
        Return the default name of the main process.
        """
        if self.__has_process:
            return self.name.get_name() + "Main"
        return ""

    def get_vars_declare(self):
        """
        Generates declarations for all variables in the profile.
        """
        target = ""
        for _, var in self.vars.items():
            if var.type == "Default":
                target += f"{var.init_code(init_process=self.instances)}\n"
        if len(target) > 1:
            target = target[:-2]
        return target

    def process_init(self):
        """
        Determines if a given statement is an initialization statement. Initialization 
        can be an assignment,
        a comparison operation, or a 'get attribute' operation on the 'self' object.
        """
        def is_init(statement):
            if isinstance(statement, Assign) or (isinstance(statement, Comparison) and statement.op == "\\in"):
                return True
            if isinstance(statement, GetAttr) and convert(statement.obj) == "self" and isinstance(statement.attr, Name):
                return True
            return False
        statements = self.init.get_suite_statements()
        for statement in statements:
            if is_init(statement):
                var = statement.get_var()
                statement.set_init()
                self.vars[var.get_name()] = var
                self.symbols[var.get_name()] = var

    def convert_process(self, indent=Indent()):
        """
        Converts the process definitions in the profile to a string format.
        """
        target = ""
        profile_name = self.name.get_name()
        for _, proc in self.processes.items():
            gen_proc_name = profile_name+capitalize(proc.name.get_name())
            self.gen_processes.append(gen_proc_name)
            target += f"func ({self.default_profile_state_instance()} *{self.default_profile_state()}) {gen_proc_name}(ienv stdp.PInterface) (err error)" + "{\n"
            with indent:
                target += proc.expand_code() + "\n"
            target += "}"
            target += "\n"
        return target

    def convert_global_procedures(self):
        """
        Converts all global procedures in the profile to a string format.
        """
        target = ""
        for _, procedure in self.procedures.items():
            target += convert(procedure) + "\n\n"
        if len(target) > 2:
            target = target[:-2]
        return target

    def convert_global_operators(self):
        """
        Converts all global operators in the profile to a string format.
        """
        target = ""
        for _, operators in self.operators.items():
            target += convert(operators) + "\n\n"
        if len(target) > 2:
            target = target[:-2]
        return target

    def convert_global_variables(self, indent=Indent()):
        """
        Converts global variables to a string representation suitable for the target
        language. This method
        handles the conversion of variables marked as 'Default' type.
        """
        target = "variables\n"
        with indent:
            for _, var in self.vars.items():
                if var.type == "Default":
                    target += indent(f"{var.init_code()}") + "\n"
        return target[:-1]

    def get_procedure(self, name):
        """ 
        Retrieves a procedure by its name from the stored procedures.
        """
        return self.procedures.get(name)

    def convert_local_shared_vars(self):
        """ 
        Generate a struct declaration for local shared variables.
        """
        indent = Indent()
        name = self.name.get_name()
        target = f"type {default_profile_state(name)} struct {{\n"
        try:
            with indent:
                for var_name in self.local_shared_vars:
                    var = self.local_shared_vars[var_name]
                    target += indent(f"{var_name} {var.get_type().get_name()}")+"\n"
            target += "}\n"

        except:
            print("local_shared_vars", var_name)
        return target

    def default_profile_state(self):
        """
        Generates a default state name for the profile.
        """
        return default_profile_state(self.get_name())

    def default_profile_state_instance(self):
        """
        Generates a default state instance name for the profile.
        """
        return default_profile_state_instance(self.get_name())

    def get_name(self):
        return self.name.get_name()


class Condition(ProfileObject):
    """
    Represents a condition in a logical or mathematical expression.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        self.m = m

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        target = ", ".join(convert(self.data))
        return target


class QuantifierExpr(ProfileObject):
    """
    Represents a quantifier expression, such as 'forall' or 'exists', in mathematical logic.
    """

    def __init__(self, data, m=None) -> None:
        self.quantifier = data[0]
        self.conditions = data[1]

    def is_compound(self):
        return True

    def analyze(self, context=Context()):
        analyze(self.quantifier, context)
        analyze(self.conditions, context)

    def convert(self, indent=Indent()):
        target = ""
        target += f"{convert(self.quantifier)}: "
        target += f"{convert(self.conditions)}, "
        return target[:-2]


class QuantifierItem(ProfileObject):
    """
    Represents an individual item within a quantifier expression.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        target = ""
        for i in self.data:
            if isinstance(i, str):
                target += i + " "
            elif isinstance(i, Name):
                target += i.get_name() + ", "
            elif isinstance(i, Set) or isinstance(i, Variable) or isinstance(i, Range) or isinstance(i, FuncCall):
                target = target[:-2] + " \\in " + i.convert() + ", "
        target = target[:-2]
        return target


class IfStmt(ProfileObject):
    """
    Represents an 'if' statement, encapsulating the condition, suite of statements, and any 
    'elif' or 'else' clauses.
    """
    def __init__(self, data, m=None) -> None:
        self.data = data
        self.condition = data[0]
        self.suite = data[1]
        self.elifs = data[2]

        if len(data) > 3:
            self.else_suite = data[3]
        else:
            self.else_suite = None
        self.is_expr = False

    def analyze(self, context=Context()):
        self.is_expr = context.get(
            "is_expr") is not None or context.get("op") is not None
        analyze(self.condition, context)
        analyze(self.suite, context)
        analyze(self.elifs, context)
        analyze(self.else_suite, context)

    def convert(self, indent=Indent()):
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
        if self.elifs is not None:
            target += convert(self.elifs) + "\n"
        if self.else_suite:
            else_target = remove_blank_line(self.else_suite.convert())
            if len(else_target) > 0:
                target = remove_blank_line(target)
                target += f"{else_k}\n"
                with indent:
                    target += indent(else_target) + "\n"
                    target += f"{end_k} "
        return target


class ComprehensionVar(Assign):
    """
    Represents a variable within a comprehension construct, extending from the Assign class.
    """

    def __init__(self, data, m=None):
        super().__init__(data, m)
        self.var = data[0]
        self.suite = data[1]

    def analyze(self, context=Context()):
        context = deepcopy(context)
        context["is_expr"] = True
        analyze(self.var, context)
        analyze(self.suite, context)

    def convert(self, indent=Indent()):
        indent = Indent()
        target = ""
        target += convert(self.var) + " = \n"
        with indent:
            target += indent(self.suite.convert()) + "\n"
        return target


class LetStmt(ProfileObject):
    """
    Represents a 'let' statement used for defining local variables within an expression.
    """

    def __init__(self, data, m=None) -> None:
        self.let = data[0]
        self.in_expr = data[1]

    def analyze(self, context=Context()):
        context = deepcopy(context)
        context["is_expr"] = True
        analyze(self.let, context)
        analyze(self.in_expr, context)

    def convert(self, indent=Indent()):
        indent = Indent()
        target = "LET\n"
        with indent:
            target += indent(self.let.convert()) + "\n"
        target += "IN\n"
        with indent:
            target += indent(self.in_expr.convert())
        return target


class Elifs(ProfileObject):
    """
    Represents a collection of 'elif' clauses in conditional statements.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        for elif_ in self.data:
            analyze(elif_[0], context)
            analyze(elif_[1], context)

    def convert(self, indent=Indent()):
        target = ""
        indent = Indent()
        for elif_ in self.data:
            target += f"else if {convert(elif_[0])} {{\n"
            with indent:
                target += indent(convert(elif_[1])) + "\n"
            target += "}"
        return remove_blank_line(target)


class WhileStmt(ProfileObject):
    """
    Represents a 'while' loop statement, encapsulating the condition and the suite of 
    statements to execute.
    """

    def __init__(self, data, m=None) -> None:
        self.condition = data[0]
        self.suite = data[1]

    def analyze(self, context=Context()):
        analyze(self.condition, context)
        analyze(self.suite, context)

    def convert(self, indent=Indent()):
        indent = Indent()
        target = "for ;" + convert(self.condition) + "; {\n"
        with indent:
            target += indent(convert(self.suite)) + "\n"
        target += "}"
        return target


class WithItem(ProfileObject):
    """
    Represents an individual item within a 'with' statement.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return convert(self.data)


class WithItems(ProfileObject):
    """
    Represents a collection of items within a 'with' statement.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        for item in self.data:
            analyze(item, context)

    def convert(self, indent=Indent()):
        target = ""
        for item in self.data:
            target += convert(item) + ", "
        return target[:-2]


class WithStmt(ProfileObject):
    """
    Represents a 'with' statement, used for context management in code.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        self.items = data[0]
        self.suite = data[1]

    def analyze(self, context=Context()):
        analyze(self.items, context)
        analyze(self.suite, context)

    def convert(self, indent=Indent()):
        indent = Indent()
        target = "with " + convert(self.items) + " do\n"
        with indent:
            target += indent(convert(self.suite)) + "\n"
        target += "end with;"
        return target


class EitherClause(ProfileObject):
    """
    Represents an 'either' clause in a choice construct, typically used in non-deterministic
    operations.
    """

    def __init__(self, data, m=None) -> None:
        self.suite = data[0]

    def analyze(self, context=Context()):
        analyze(self.suite, context)

    def convert(self, indent=Indent()):
        target = "or\n"
        indent = Indent()
        with indent:
            target += indent(convert(self.suite)) + "\n"
        return target[:-1]


class EitherStmt(ProfileObject):
    """
    Represents an 'either' statement, which encapsulates multiple choice branches in a 
    non-deterministic operation.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        self.suite = data[0]
        self.either = data[1]

    def analyze(self, context=Context()):
        analyze(self.suite, context)
        for i in self.either:
            analyze(i, context)

    def convert(self, indent=Indent()):
        indent = Indent()
        target = "either\n"
        with indent:
            target += indent(convert(self.suite)) + "\n"
        for i in self.either:
            target += indent(convert(i)) + "\n"
        target += "end either;"
        return target


class RawCode(ProfileObject):
    """
    Represents raw code of Go that is directly included in the output without modification.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def convert(self, indent=Indent()):
        return self.data

    def analyze(self, context=Context()):
        analyze(self.data, context)


class Range(ProfileObject):
    """
    Represents a range construct in expressions or loops.
    This class is not used in Go, currently.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)

    def convert(self, indent=Indent()):
        return ""


class LogicTest(ProfileObject):
    """
    Represents a logical test expression that can be a part of complex logical statements.
    """

    def __init__(self, data, m, op) -> None:
        self.data = data
        self.op = op
        self.m = m

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
        target = ""
        for i in self.data:
            target += convert(i) + self.op
        return "(" + target[:-4] + ")"


class AndTest(LogicTest):
    """
    Represents a logical 'AND' test, derived from LogicTest.
    """
    def __init__(self, data, m=None) -> None:
        super().__init__(data, m, " && ")


class OrTest(LogicTest):
    """
    Represents a logical 'OR' test, derived from LogicTest.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, m, " || ")


class NotTest(ProfileObject):
    """
    Represents a logical 'NOT' test.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return "!" + convert(self.data)


class AssertStmt(ProfileObject):
    """
    Represents an assertion statement, typically used for debugging or validating conditions.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        target = convert(self.data)
        statements = target.split("\n")
        statements[-1] = "assert " + statements[-1] + ";"
        target = "\n".join(statements)
        return target


class DottedName(ProfileObject):
    """
    Represents a name with dots, commonly used for qualified naming in programming languages.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return convert(self.data)


class DottedAsName(ProfileObject):
    """
    Represents a dotted name with an 'as' clause, often used in import statements.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return convert(self.data)


class DottedAsNames(ProfileObject):
    """
    Represents a collection of dotted names with 'as' clauses.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return convert(self.data)


class ImportName(ProfileObject):
    """
    Represents an import name statement, used for including external modules or libraries.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return convert(self.data)


class ImportStmt(ProfileObject):
    """
    Represents an import statement, which is used to include code from other modules or libraries.
    """

    def __init__(self, data, m) -> None:
        self.data = data[0]
        self.m = m
        self.libs = convert(self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return ""

class ExtendStmt(ProfileObject):
    """
    The extend statements will be ignored in Go.
    """


class FileInput(ProfileObject):
    """
    Represents the input of a file, encapsulating a PerfCal module.
    """

    def __init__(self, data, folder, m=None, tranformer=None, parse=None) -> None:
        self.statements = data
        self.transformer = tranformer
        self.parser = parse
        self.folder = folder
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

         """  # change to import
        self.symbols = {}
        self.vars = {}
        self.prof_vars = {}
        self.profiles = {}
        self.libs = {}
        self.is_anonymous = False
        self.const_declare = []
        self.target = ""
        self.analyze()

    def __auto_default_var(self):
        """
        Automatically defines default variables if no profile variable is present.
        """
        if len(self.prof_vars) == 0:
            for name, profile in self.profiles.items():
                var_name = name + "_var"
                var = Variable(var_name)
                var.set_type(type_annotation("Profile"))
                self.prof_vars[var_name] = var
                profile["vars"].append(var_name)
                self.vars[var_name] = var
                self.symbols[var_name] = var

    def analyze(self, context=Context()):
        for statement in self.statements:
            if isinstance(statement, SimpleStmt):
                inner = statement.simple_assign(
                    [Assign, ConstAssign, Comparison, FuncCall])
                if inner is not None:
                    statement = inner

            if isinstance(statement, Profile):
                name = statement.name.get_name()
                add_var_to_dict(self.profiles, name, {
                                "profile_declare": statement, "vars": [], "range": None})
                add_var_to_dict(self.symbols, name, statement)

            if isinstance(statement, Assign):
                var = statement.get_var()
                statement.analyze()
                if isinstance(statement.exprs[0], FuncCall):
                    called = statement.exprs[0].name.get_name()
                    if called in self.symbols:
                        called_obj = self.symbols[called]
                        if isinstance(called_obj, Profile):
                            var.set_type(type_annotation("Profile"))
                            self.prof_vars[var.get_name()] = var
                            self.profiles[called_obj.name.get_name()]["vars"].append(
                                var.get_name())
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

            if isinstance(statement, ImportStmt):
                for lib in statement.libs:
                    self.libs[lib] = None

            if isinstance(statement, ConstAssign):
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
        """
        Parses libraries used in the file and integrates them into the current context.
        """
        for lib in self.libs:
            if lib in self.libs and self.libs[lib] is not None:
                continue
            try:
                source_code = load_source_code(lib, self.folder, ".go")
                lib_profile = self.transformer().transform(self.parser(source_code))
                self.libs[lib] = lib_profile
                self.libs = {**self.libs, **lib_profile.libs}
            except Exception as e:
                print("lib ", lib, " failed")
                print(e)

    def to_dict(self):
        result = {}
        for name, profile in self.profiles:
            result[name] = profile["profile_declare"].to_dict()
        return result

    def convert(self, indent=Indent(), module="main"):
        indent.reset()
        target = "package " + module + "\n"
        target += self.extends + "\n"
        for const in self.const_declare:
            target += convert(const) + "\n"
        for typ in self.types:
            target += convert(typ) + "\n"
        target += util.newline(self.__convert_local_shared_vars(), n=1)
        target += util.newline(self.__convert_procedures(), n=1)
        target += util.newline(self.__convert_process(), n=1)
        self.target = target
        return target

    @staticmethod
    def convert_variables(prof, indent=Indent()):
        """
        Converts the variables of a given profile into a string representation suitable for the Go.
        """
        if prof is None:
            print("prof is None")
            return ""
        target = ""
        for _, var in prof.vars:
            if var.type == "Default":
                target += f"{var.init_code()}" + "\n"
        if len(target) > len(";\n"):
            target = target[:-1]
        else:
            target = ""
        return target

    def __convert_local_shared_vars(self):
        target = ""
        for _, profile in self.profiles.items():
            target += profile["profile_declare"].convert_local_shared_vars() + "\n"
        return target


    def convert_operators(self):
        """
        TODO: This function need to be completed later.
        """
        return ""

    @staticmethod
    def convert_procs(obj):
        """
        Converts processes defined in a given object (containing profiles) into a 
        string representation suitable for the go_code.
        """
        if obj is None:
            return ""
        target = ""
        for name in obj.profiles:
            profile = obj.profiles[name]
            target += profile["profile_declare"].convert_global_procedures() + "\n"
        return target

    def __convert_procedures(self):
        """
        Converts procedures defined in all profiles and libraries into a string
        representation suitable for Go.
        """
        target = FileInput.convert_procs(self)
        for name in self.libs:
            lib = self.libs[name]
            target += FileInput.convert_procs(lib)
        return target

    def __convert_process(self, indent=Indent()):
        target = ""
        for _, profile_info in self.profiles.items():
            if profile_info["profile_declare"].has_process():
                target += profile_info["profile_declare"].convert_process() + "\n"
        for name, profile_info in self.profiles.items():
            profile = profile_info["profile_declare"]
            if profile.is_env():
                continue
            process_name = profile.get_process_name()
            processes = [profile.default_profile_state_instance(
            )+"."+e for e in profile.gen_processes]
            gen_processes = ", ".join(processes)

            if profile.has_init():
                init_func = f"        Init: {profile.default_profile_state_instance()}.{name}Init,\n"
            else:
                init_func = ""
            target += \
                f"func {name} () stdp.Profile {{ \n\
    var {profile.default_profile_state_instance()} *{profile.default_profile_state()} = &{profile.default_profile_state()}{{}} \n \
    return stdp.Profile {{ \n\
        Name: \"{name}\",\n\
        Main: {profile.default_profile_state_instance()}.{process_name},\n\
        State: {profile.default_profile_state_instance()}, \n\
        Processes: []stdp.Proc{{{gen_processes}}},\n{init_func}\
    }} \n}}\n"
        target += "\nfunc init() {\n"
        with indent:
            for t in self.types:
                if isinstance(t, NewStruct):
                    target += indent(t.register()) + "\n"
        target += "}"
        return target


class MODULE(ProfileObject):
    """
    Represents a module in the profile object model, encapsulating various statements and
    constructs.
    """

    def __init__(self, data, m=None):
        self.data = data


def get_package_name_from_file(output):
    """
    Extracts the package name from a given file path. This function assumes that the 
    package name is the same as the base filename (without the extension) of the 
    provided path.
    """
    output = output.split("/")[-1]
    output = output.split(".")[0]
    return output


def save(go_code, output):
    """
    Saves the given Go code to a file. This function automatically determines the 
    package name from the output file path and uses it to convert the Go code into
    a complete module before writing it to the file.

    :param go_code: The Go code object to be saved.
    :param output: The file path where the Go code will be saved.
    """
    package = get_package_name_from_file(output)
    code = go_code.convert(module=package)
    with open(output, "w", encoding='utf-8') as f:
        f.write(code)
