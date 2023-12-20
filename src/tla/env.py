"""
The module contains classes for converting and manipulating TLA+ profile objects.
"""
from copy import deepcopy
import traceback
import logging
from . import util
from .util import get_convert, analyze, load_source_code

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')


def c(*args):
    """A log function that safely handles any type of parameters.
    Convert all parameters to strings and connect them with spaces.
    """
    debug_message = ' '.join(str(arg) for arg in args)
    return debug_message


debug = logging.debug


def default_profile_state(name):
    """Default profile state name"""
    return name+"State"


def default_profile_state_instance(name):
    """Default profile instance name"""
    return name+"Ins"


convert = get_convert("tla")

PERFORMANCE_VARS = [
    "Time", "Report"
]

NOT_DECLARE_VARS = ["pID"]

UTIL_FUNC = {
    "print": "print(<<{args}>>)",
    "len": "Len({args})",
}


def remove_last_line(s):
    """
    Removes the last line from a given string.
    """
    for i in range(len(s)-1, -1, -1):
        if s[i] == "\n":
            return s[:i]
    return s


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


def convert_performance(func_name, args):
    """
    Converts a performance function name and arguments into a specific expression.
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
        """
        Initializes the Context object with default values for various context-related data.
        """
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

    def enter_macro(self, macro):
        """
        Enters a macro context.
        """
        self.data["in_macro"] = True
        if macro not in self.data["macros"]:
            self.data["macros"].append(macro)

    def exit_macro(self):
        """
        Exits the current macro context.
        """
        self.data["in_macro"] = False

    def is_macro(self, name):
        """
        Checks if a given name corresponds to a macro.
        """
        name = name.replace(".", "_")
        return name in self.data["macros"]

    def in_macro(self):
        """
        Checks if currently in a macro context.
        """
        return self.data["in_macro"]

    def enter_assign(self, init_expr, init_op):
        """
        Enters an assignment context with initial expressions and operators.
        """
        self.data["init_expr"] = init_expr
        self.data["init_op"] = init_op

    def exit_assign(self):
        """
        Exits the current assignment context.
        """
        self.data["init_expr"] = None
        self.data["init_op"] = ""

    def exit_assign_inner(self):
        """
        Handles exiting from an inner assignment context, storing the last initial expression.
        """
        self.data["init_expr_last"] = self.data["init_expr"]
        self.data["init_expr"] = None

    def restore_assign(self):
        """
        Restores the last initial expression for the assignment context.
        """
        self.data["init_expr"] = self.data["init_expr_last"]
        self.data["init_expr_last"] = None

    def enable_add_var(self):
        """
        Enables the addition of variables to the context unless within a macro context.
        """
        self.data["add_var"] = True and not self.in_macro()

    def disable_add_var(self):
        """
        Disables the addition of variables to the context.
        """
        self.data["add_var"] = False

    def can_add_var(self):
        """
        Determines if variables can be added to the context.
        """
        return self.data["add_var"]

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

    def set_global_vars(self, global_vars):
        """
        Sets the global variables in the context.
        """
        self.data["global_vars"] = global_vars

    def get_global_vars(self):
        """
        Retrieves the global variables from the context.
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
        Retrieves a specific global variable from the context by its name.
        """
        return self.data["global_vars"].get(name)

    def del_global_var(self, name):
        """
        Deletes a global variable from the context.
        """
        if name in self.data["global_vars"]:
            del self.data["global_vars"][name]

    def add_local_shared_var(self, name, var, typ=None):
        """
        Adds a locally shared variable to the context.
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

    def get_type(self):
        """Return a default type name"""
        return "Default"

    def get_local_shared_vars(self):
        """
        Retrieves all locally shared variables from the context.
        """
        return self.data["local_shared_vars"]

    def get_local_shared_var(self, name):
        """
        Retrieves a specific locally shared variable from the context by its name.
        """
        return self.data["local_shared_vars"].get(name)

    def del_local_shared_var(self, name):
        """
        Deletes a locally shared variable from the context.
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
        Retrieves a specific local variable from the context by its name.
        """
        return self.data["local_vars"].get(name)

    def del_local_var(self, name):
        """
        Deletes a local variable from the context.
        """
        if name in self.data["local_vars"]:
            del self.data["local_vars"][name]

    def get_local_vars(self):
        """
        Retrieves all local variables from the context.
        """
        return self.data["local_vars"]

    def enter_func(self, func):
        """
        Enters a function context, setting the current function and resetting local
        variables and constants.
        """
        self.data["func"] = func
        self.data["local_vars"] = {}
        self.data["local_const"] = {}

    def exit_func(self):
        """
        Exits the current function context, resetting the function, local variables,
        and constants.
        """
        self.data["func"] = None
        self.data["local_vars"] = {}
        self.data["local_const"] = {}

    def enter_signature(self):
        """
        Enters a signature context, enabling variable addition and setting the signature flag.
        """
        self.enable_add_var()
        self.data["signature"] = True

    def exit_signature(self):
        """
        Exits the signature context, disabling variable addition and unsetting the
        signature flag.
        """
        self.disable_add_var()
        self.data["signature"] = False

    def is_signature(self):
        """
        Checks if currently in a signature context.
        """
        return self.data["signature"]

    def get_func(self):
        """
        Retrieves the current function from the context.
        """
        return self.data.get("func")

    def backup_global_vars(self):
        """
        Backs up the current global variables and constants.
        """
        self.data["global_vars_backup"] = {}
        self.data["const_backup"] = {}
        for k, v in self.data["global_vars"].items():
            self.data["global_vars_backup"][k] = v
        for k, v in self.data["const"].items():
            self.data["const_backup"][k] = v

    def restore_global_vars(self):
        """
        Restores the global variables and constants from the backup.
        """
        self.data["global_vars"] = self.data["global_vars_backup"]
        self.data["global_vars_backup"] = {}
        self.data["const"] = self.data["const_backup"]
        self.data["const_backup"] = {}

    def enter_profile(self, prof):
        """
        Enters a profile context.
        This method changes the current scope to 'profile', backs up global variables, and
        prepares the context for handling operations within a profile-specific environment.
        """
        self.backup_global_vars()
        self.data["profile"] = prof
        self.data["scope"] = "profile"
        self.data["local_shared_vars"] = {}

    def exit_profile(self):
        """
        Exits the current profile context.
        """
        self.data["profile"] = None
        self.data["scope"] = "global"
        self.restore_global_vars()
        self.data["local_shared_vars"] = {}

    def get_scope(self):
        """
        Retrieves the current scope of the context.
        """
        if self.data["scope"] == "global":
            return "global"
        if self.data.get("func") is not None:
            return "local"
        if self.data["signature"]:
            return "global"
        # print(self.data.get("scope"))
        return "local_shared"

    def is_global_var(self, name):
        """
        Checks if a variable name corresponds to a global variable
        """
        # If in the function, and the variable name is a local variable, return False
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

        Args:
            name (str): The name of the flag to set.
            value: The value to assign to the flag.

        This method allows setting custom flags within the context, which can be used to
        control various aspects of the context's behavior.
        """
        self.data["flags"][name] = value

    def get_flag(self, name):
        """
        Retrieves the value of a flag from the context.
        """
        return self.data["flags"].get(name)


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
        super().__init__(data)
        self.data = data[0]
        # print(self.value[0])

    def convert(self, indent=Indent()):
        return int(self.data)

    def get_name(self):
        return self.data


class KeyValue(ProfileObject):
    """
    Represents a key-value pair as a profile object.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data)
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
        self.type = "Default"
        self.is_profile_var = False
        self.scope = None
        self.profile = None
        self.func = None
        self.init = None
        self.init_op = "="
        self.is_declare = False
        self.is_var = True
        self.var = None

    def set_type(self, typ):
        """
        Sets the type of the variable.
        """
        self.type = typ

    def get_scope(self):
        """
        Retrieves the scope (global, local shared or local) of the variable.
        """
        return self.scope

    def analyze(self, context=Context()):
        code_scope = context.get_scope()
        declared, var, scope = context.add_var(
            self.get_name(), self, code_scope)
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
            if not context.can_add_var():
                self.is_var = False

    def get_init(self):
        """
        Retrieves the initialization value or expression of the variable.
        """
        return self.init

    def get_name(self):
        # access the variable (except init)
        n = self.name.get_name()
        # A temporary processing method, which needs to be modified later
        if n == "self":
            return "pID"
        return n

    def convert(self, indent=Indent()):
        if self.scope == "local_shared" and self.is_var:
            name = f"{default_profile_state_instance(self.profile.name.get_name())}[pID].{convert(self.name)}"
            # traceback.print_stack()
        else:
            name = self.get_name()

        return name

    def to_dict(self):
        """
        Converts the Variable object to a dict representation.
        """
        return self.convert()

    def init_code(self, init_process=None):
        """
        Generates the initialization code for the variable.
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
                target = f"{self.convert()} = [p \\in {process_set} |-> {convert(self.init)}];"
            else:
                target = f"{self.convert()} \\in [{process_set} -> {convert(self.init)}];"
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
    Represents an assignment statement as a profile object.
    """

    def __init__(self, data, m=None):
        self.m = m
        self.vars = [data[0]]
        self.exprs = [data[1]]
        self.is_expr = False
        self.in_func = False
        self.func = None

    def analyze(self, context=Context()):
        self.func = context.get("func")
        if self.func is not None:
            self.in_func = True
        else:
            self.in_func = False
        context.enter_assign(self.exprs[0], "=")
        context.enable_add_var()
        analyze(self.vars[0], context)
        context.disable_add_var()
        analyze(self.exprs[0], context)
        if context.get("op") is not None:
            self.is_expr = True
        context.exit_assign()

    def get_var(self):
        """
        Retrieves the variable of the assignment.
        """
        return self.vars[0]

    def get_expr(self):
        """
        Retrieves the expression of the assignment.
        """
        return self.exprs[0]

    def convert(self, indent=Indent()):
        target_code = ""
        target_code += f"{self.vars[0].convert()}"
        if self.is_expr:
            target_code += " = "
        else:
            target_code += " := "
        if isinstance(self.exprs[0], FuncCall) and self.exprs[0].is_procedure:
            target_code = f"{convert(self.exprs[0])}\nL{self.m.line}:\n" + \
                target_code + "Head(__call_stack[self]);\n"
            target_code += "__call_stack[self] := Tail(__call_stack[self]);\n"
        elif isinstance(self.exprs[0], FuncCall) and self.exprs[0].is_macro:
            target_code = f"{self.exprs[0].macro_call(self.vars[0].convert())}, "
        else:
            target_code += f"{convert(self.exprs[0])}, "
        if not self.is_expr:
            target_code = target_code[:-2] + ";"
        else:
            target_code = target_code[:-2]
        return target_code


class AssignLink(ProfileObject):
    """
    Represents an assignment statement with the ends of "$" as a profile object.
    """

    def __init__(self, data, m=None):
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        target = self.data.convert()
        if target.endswith(";"):
            target = target[:-1]
        return target + " ||"


class Comparison(ProfileObject):
    """
    Represents a comparison operation as a profile object.

    Attributes:
        data: The comparison data including the operands and operator.
        left: The left-hand operand of the comparison.
        right: The right-hand operand of the comparison.
        op: The operator used in the comparison.
        m: Additional metadata or information.
    """

    def __init__(self, data, m=None):
        self.data = data
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
        """
        Converts the comparison operator to a PlusCal format.
        """
        op_mapping = {
            "==": "=",
            "!=": "/=",
            "in": "\\in",
        }
        if op in op_mapping:
            return op_mapping[op]
        else:
            return op

    def get_var(self):
        """
        Retrieves the variable involved in the IN comparison.
        For example: clients in CLIENTS
        """
        return self.left

    def is_in_op(self):
        """
        Checks if the operator in the comparison is an IN operation.
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
    Represents a collection of parameters as a profile object.
    """

    def __init__(self, data, m=None):
        self.data = data
        self.is_argu = None

    def analyze(self, context=Context()):
        self.is_argu = context.get("is_argu")
        for i in self.data:
            analyze(i, context)
        func = context.get("func")
        if self.is_argu and func is not None:
            for i in self.data:
                if i is not None:
                    context.add_local_var(i.get_name(), Variable([i]))

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
        Fetches arguments from the stack for procedure calls.
        """
        target = ""
        j = 0
        for i, a in enumerate(self.data):
            if a is None:
                continue
            j += 1
            tail = "Tail("*i
            end = ")"*(i+1) + " ||\n"
            target += f"{convert(a)} := Head(" + tail + \
                "__call_stack[name]" + end
        target += "__call_stack[name] := " + \
            "Tail("*j + "__call_stack[name]" + ")"*j + ";\n"
        return target


class FuncDef(ProfileObject):
    """
    Represents a function definition as a profile object.

    Attributes:
        name: The name of the function.
        m: Additional metadata or information.
        args: The arguments of the function.
        local_vars: List of local variables within the function.
        suite: The suite of statements that make up the function body.
        def_type (str): The type of definition (e.g., 'procedure' or 'process').
        prefix_name (str): Prefix for the function name.
    """

    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.m = m
        self.args = data[1]
        self.local_vars = []
        self.suite = data[3]
        self.def_type = "procedure"
        self.prefix_name = ""
        self.prefix = None
        # print("funcdef", convert(self.name), self.args)

    def analyze(self, context=Context()):
        profile = context["profile"]
        if profile is not None:
            self.prefix_name = profile.get_procedure_name(convert(self.name))
        context.enter_func(self)
        context["func"] = self
        analyze(self.name, context)
        context["is_argu"] = True
        debug(
            c("args", self.args, context.data["add_var"], convert(self.args)))
        analyze(self.args, context)
        debug(c(self.name.get_name(), context.get_local_vars()))

        del context["is_argu"]
        # Analyze all variables that appear in the function body
        # Extract all undefined variables (not in profile.vars)
        analyze(self.suite, context)

        self.local_vars = context.get_local_vars()

        context.exit_func()

    def get_suite_statements(self):
        """
        Retrieves the suite of statements from the function body.
        """
        return self.suite.statements

    def set_type(self, def_type, prefix=""):
        """
        Sets the type and prefix for the function definition.
        """
        self.def_type = def_type
        self.prefix = prefix

    def convert(self, indent=Indent()):
        target = f"{self.def_type} {self.prefix_name}(name, pID)\n"
        if len(self.local_vars) > 0:
            target += "variables\n"
            with indent:
                for var in self.local_vars:
                    if var is not None and var != "":
                        target += f"{var};"
            target += "\n"
            target += "__Profile = " + convert(self.prefix) + ";\n"
        target += "begin\n"
        with indent:
            if self.args is not None:
                target += indent(f"L{self.m.line}:\n" +
                                 self.args.fetch_argus_from_stack() + self.suite.convert())
            else:
                target += indent(f"L{self.m.line}:\n" + self.suite.convert())
        if target.endswith(":"):
            target = remove_last_line(target)
        target += f"\n    return;\nend {self.def_type};"
        return target

    def expand_code(self, pmap, indent=Indent()):
        """
        Expands the function definition into a complete code representation.
        """
        target = ""
        target += "variables\n    "
        for var in self.local_vars:
            target += f"{var}, "
        target = target + f"{pmap};\n"
        target += "begin\n"
        target += indent(self.suite.convert())
        if target.endswith(":"):
            target = remove_last_line(target)
        return target


class ProcDef(FuncDef):
    """
    Represents a process definition as a profile object.
    """
    # def __init__(self, data, m=None) -> None:
    #     super().__init__(data, m)


class ReturnStmt(ProfileObject):
    """
    Represents a return statement as a profile object.
    """

    def __init__(self, data, m=None) -> None:
        self.expr = data
        self.m = m
        # print("return", self.expr)

    def analyze(self, context=Context()):
        analyze(self.expr, context)

    def convert(self, indent=Indent()):
        target = "__call_stack[name] := <<"
        for expr in self.expr:
            target += convert(expr) + ", "
        if len(self.expr) > 0:
            target = target[:-2] + ">> \\o __call_stack[name];\n"
        target += f"\nL{self.m.line}:\nreturn;"
        return target


class OpDef(FuncDef):
    """
    Represents an operator definition, extending functionality from FuncDef.
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
        target = f"{self.prefix}_{convert(self.name)}({convert(self.args)}) == \n"
        with indent:
            target += indent(self.suite.convert())
        return target


class List(ProfileObject):
    """
    Represents a list structure in the profile object model.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("data", self.data)

    def analyze(self, context=Context()):
        for i in self.data:
            analyze(i, context)

    def convert(self, indent=Indent()):
        target = "<<"
        for i in self.data:
            target += f"{convert(i)}, "
        if len(self.data) > 0:
            target = target[:-2]
        target += ">>"
        return target

    def to_dict(self):
        """
        Converts the Variable object to a dict representation.
        """
        ret = []
        for i in self.data:
            if isinstance(i, ProfileObject):
                ret.append(i.to_dict())
            else:
                ret.append(i)
        return ret


class Dict(ProfileObject):
    """
    Represents a dictionary structure in the profile object.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)
        self.data = data
        # print(self.data)

    def to_dict(self):
        """
        Converts the Dict object to a dictionary representation.
        """
        ret = {}
        for key_value in self.data:
            key = key_value[0]
            value = key_value[2]
            if isinstance(value, ProfileObject):
                value = value.to_dict()
            ret[key] = value
        return ret

    def convert_key(self, key):
        """
        Converts a key to a string format for use in the dictionary representation.
        """
        if isinstance(key, str):
            return key
        return convert(key)

    def analyze(self, context=Context()):
        for key_value in self.data:
            analyze(key_value[0], context)
            analyze(key_value[2], context)

    def convert(self, indent=Indent()):
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
    """
    Represent a set as a profile object.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        # print("data", self.data)

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
    Represents a generic term in an expression, capable of handling various operations.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        self.m = m

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
                if op == "/":
                    stack.append(f"Div({op1}, {op2})")
                else:
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
            # print(data)
        except Exception as e:
            print("error")
            print(e)
            print(data[0])
        self.data = data[1]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        has_space = " " if len(self.op) > 1 else ""
        return f"({self.op}" + has_space + f"{convert(self.data)})"


class Suite(ProfileObject):
    """
    Represents a collection of statements or expressions, often within a block or a function body.

    Attributes:
        statements: A list of statements or expressions that form the suite.
        is_expr (bool): Indicates whether the suite is part of an expression context.
    """

    def __init__(self, data, m=None) -> None:
        # print(data)
        self.statements = data
        self.is_expr = False

    def analyze(self, context=Context()):
        self.is_expr = context.get(
            "op") is not None or context.get("is_expr")
        for statement in self.statements:
            analyze(statement, context)

    def convert(self, indent=Indent()):
        target_code = ""
        for _, statement in enumerate(self.statements):
            try:
                target_code += convert(statement)
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
        target_code = remove_blank_line(target_code)
        if target_code.endswith(":"):
            target_code = remove_last_line(target_code)
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

    def analyze(self, context=Context()):
        analyze(self.label, context)

    def convert(self, indent=Indent()):
        return f"{convert(self.label)}:"


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
        return f"({convert(self.data[0])})+1, ({convert(self.data[1])})"


class GetItem(ProfileObject):
    """
    Represents a 'get item' operation, typically used for accessing elements in a data
    structure by index or key.
    """

    def __init__(self, data, m=None):
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)

    def convert(self, indent=Indent()):
        if self.data[0].is_compound():
            if isinstance(self.data[1], Slice):
                return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
            return f"({convert(self.data[0])})[({convert(self.data[1])})+1]"
        if isinstance(self.data[1], Slice):
            return f"Slice({convert(self.data[0])}, {convert(self.data[1])})"
        return f"{convert(self.data[0])}[({convert(self.data[1])})]"

    def to_dict(self):
        return self.convert()


class GetAttr(Variable):
    """
    Represents an attribute access operation on an object, extending from the Variable class.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)
        self.data = data
        self.obj = data[0]
        self.attr = data[1]
        self.extra_argu = ""
        self.type = "Default"
        self.env = None
        self.libs = None
        self.scope = None
        self.global_access = False
        self.name = self
        self.declared = True
        self.context = None

    def analyze(self, context=Context()):
        profile = context.get("profile")
        if profile is not None and context.get("scope") == "profile":
            self.env = {"name": profile.name.get_name(
            ), "procedures": profile.procedures}
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

    def set_env(self, env):
        """
        Sets the environment context for the GetAttr operation.
        """
        self.env = env

    def init_code(self, init_process=False):
        """
        Generates initialization code for the GetAttr operation.
        """
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
        Generates a read operation string for a given object.
        """
        return f"Read(\"{obj}\", "

    def convert_write(self, obj):
        """
        Generates a write operation string for a given object.
        """
        return f"Write(\"{obj}\", "

    def split_get_attr(self):
        """
        Splits the attribute access operation into object, action, and additional string components.
        """
        action = convert(self.attr)
        obj = convert(self.obj)
        if action == "read":
            return obj, action, self.convert_read(obj)
        elif action == "write":
            return obj, action, self.convert_write(obj)
        else:
            return obj, action, ""

    def get_global_access(self):
        """
        Checks if the attribute access operation is a global access.
        """
        return self.global_access

    def convert(self, indent=Indent()):
        attr = convert(self.attr)
        if self.obj.get_name() == "self":
            if attr in self.env.get('procedures'):
                self.extra_argu = "self"
                return f"__{self.env.get('name')}_{convert(self.attr)}"
            return f"__{self.env.get('name')}_{convert(self.attr)}[self]"
        if self.libs is not None and self.obj.get_name() in self.libs:
            return f"__{convert(self.obj)}_{convert(self.attr)}"
        if self.obj.is_compound():
            return f"({convert(self.obj)}).{convert(self.attr)}"
        return f"{convert(self.obj)}.{convert(self.attr)}"


class FuncCall(ProfileObject):
    """
    Represents a function call, encapsulating details about the function name, arguments, 
    and other properties.
    """

    def __init__(self, data, m=None) -> None:
        self.name = data[0]
        self.args = data[1]
        self.is_procedure = False
        self.global_access = False
        self.profile = None
        self.m = m
        self.is_macro = False
        if self.name.get_name() == "TLA":
            self.target = ', '.join(convert(self.args))
            if len(self.target) < 2:
                raise ValueError("TLA must have at least one string argument")
            self.target = self.target[1:-1]
        else:
            self.target = None

    def analyze(self, context=Context()):
        profile = context.get("profile")
        context.exit_assign_inner()
        context.disable_add_var()
        analyze(self.name, context)
        analyze(self.args, context)
        context.restore_assign()
        self.is_macro = context.is_macro(convert(self.name))
        self.profile = profile
        if profile is not None:
            try:
                if isinstance(self.name, GetAttr):
                    self.is_procedure = convert(
                        self.name.obj) in context.get("libs")
                    self.global_access = self.name.get_global_access()
                else:
                    self.is_procedure = convert(
                        self.name) in profile.procedures
                    self.global_access = False
            except Exception as e:
                debug(c(e))
                self.is_procedure = False

    def macro_call(self, var):
        """
        Generates a macro call in PlusCal.
        """
        target = ""
        if isinstance(self.name, GetAttr):
            obj, action, _ = self.name.split_get_attr()
            idxs = ", ".join(convert(self.args))
            if idxs == "":
                args = f"{var}"
            else:
                args = f"{var}, {idxs}"
            target = f"{obj}_{action}(<<{args}>>)"
            return target

        func_name = convert(self.name)
        args = convert(self.args)
        if isinstance(args, list):
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

    def convert(self, indent=Indent()):
        if self.target is not None:
            return self.target
        target = ""
        if self.is_procedure:
            target = "__call_stack[self] := <<"
            target += f"{', '.join(convert(self.args))}>> \\o __call_stack[self];\n"
            prefix_name = self.profile.get_procedure_name(convert(self.name))
            target += f"call {prefix_name}(self, pID);"
        else:
            if self.global_access:
                obj, action, _ = self.name.split_get_attr()
                idxs = ", ".join(convert(self.args))
                target = f"{obj}_{action}({idxs})"
                return target
            func_name = convert(self.name)
            if func_name in PERFORMANCE_VARS:
                target = convert_performance(func_name, self.args)
            elif func_name in UTIL_FUNC:
                target = UTIL_FUNC[func_name].format(
                    args=', '.join(convert(self.args)))
            else:
                target = f"{convert(self.name)}({', '.join(convert(self.args))})"
        return target

    def to_dict(self):
        return self.convert()


class Comment(ProfileObject):
    """
    Represents a comment in the profile object model, typically used for documentation or
    code explanation.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data
        # print(self.data)

    def convert(self, indent=Indent()):
        return ""


class Arguments(ProfileObject):
    """
    Represents arguments in a function or method call.
    """

    def __init__(self, data, m=None) -> None:
        # print("Arguments", data, type(data))
        self.data = data

    def analyze(self, context=Context()):
        for arg in self.data:
            analyze(arg, context)

    def head(self):
        """
        Retrieves the first argument in the list of arguments.
        """
        if len(self.data) > 0:
            return self.data[0]
        logging.warning(c("get head of empty list"))
        return None

    def tail(self):
        """
        Retrieves all but the first argument in the list of arguments.
        """
        if len(self.data) > 1:
            return self.data[1:]
        logging.warning(c("get tail of empty list"))
        return None

    def convert(self, indent=Indent()):
        return convert(self.data)


class Profile(ProfileObject):
    """
    Represents a profile object encapsulating various components like variables, procedures, and processes.
    """

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
        self.global_vars = {}
        self.local_shared_vars = {}
        self.__has_process = False
        self.init = None

        self.instance_type = ""

    def to_dict(self):
        ret = {}
        for var_name, var in self.vars.items():
            ret[var_name] = var.to_dict()
        return ret

    def analyze(self, context=Context()):
        global_vars = context.get("global_vars")
        p_name = self.name.get_name()
        instances = context.get("instances")
        info = instances.get(p_name)
        if info is not None:
            if info.get("range") is not None:
                self.instances = info.get("range").to_dict()
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
            if isinstance(statement, Assign) or (isinstance(statement, Comparison) and statement.op == "\\in"):
                var = statement.get_var()
                # Set the variable type of var to Profile
                if var.get_name() not in global_vars:
                    self.vars[var.get_name()] = var
                    self.symbols[var.get_name()] = var
            elif isinstance(statement, FuncDef):
                self.symbols[statement.name.get_name()] = statement
                name = statement.name.get_name()
                if name == "init":
                    self.init = statement
                    self.process_init()
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

        # logging.debug(c("analyze profile", context.get_global_vars(), self.args))
        self.global_vars = context.get_global_vars()
        for statement in self.suite.statements:
            analyze(statement, context)
        self.local_shared_vars = context.get_local_shared_vars()
        context.exit_profile()

    def get_procedure_name(self, p_name):
        """
        Retrieves the full name of a procedure within the profile context.
        """
        if p_name in self.procedures:
            return "__" + self.name.get_name() + "_" + p_name
        return "Error"

    def has_process(self):
        """
        Checks if the profile contains any process definitions.
        """
        return self.__has_process

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
        Processes and initializes variables within the profile based on the 'init' function.
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

    def __convert_process_header(self, profile_name, process_name):
        """
        Generates a process header string.
        """
        instances = ""
        if self.instance_type == "range":
            instances = "\", \"".join(
                [self.convert_process_ins(i, process_name) for i in self.instances])
            instances = "\\in {\"" + instances + "\"}"
        else:
            instances = "\", \"".join(self.instances)
            instances = "\\in {\"" + instances + "\"}"
        target = f"process {self.convert_process_ins(profile_name, process_name)} {instances}"
        return target

    def get_process_instances(self):
        """
        Retrieves instances of processes defined in the profile.
        """
        process_name = [p for p in self.processes]
        process_instances = []
        for i in self.instances:
            for p in process_name:
                process_instances.append(self.convert_process_ins(i, p))
        return process_instances

    def convert_process_ins(self, p_name, proc_name):
        """
        Converts process instance names to a specific format.
        """
        if isinstance(p_name, float):
            p_name = str(p_name)
        return p_name + capitalize(proc_name)

    def get_pmap(self, process_name):
        """
        Generates a mapping for process names.
        """
        pmap = "pmap=["
        if self.instance_type == "range":
            for i in self.instances:
                pmap += f"{self.convert_process_ins(i, process_name)} |-> {i},"
            if len(self.instances) > 0:
                pmap = pmap[:-1] + "], pID=pmap[self]"
        else:
            pass
        return pmap

    def convert_process(self, indent=Indent()):
        """
        Converts the process definitions in the profile to a string format.
        """
        target = ""
        profile_name = self.name.get_name()
        for _, proc in self.processes.items():
            process_name = proc.name.get_name()
            gen_proc_name = self.convert_process_ins(
                profile_name, process_name)
            self.gen_processes.append(gen_proc_name)
            target += self.__convert_process_header(
                profile_name, process_name) + "\n"
            pmap = self.get_pmap(process_name)
            with indent:
                target += proc.expand_code(pmap) + "\n"
            target += "end process;\n\n"
        target = keep_one_blank_line(target)
        return target

    def convert_global_procedures(self):
        """
        Converts all global procedures in the profile to a string format.
        """
        target = ""
        for _, procedure in self.procedures.items():
            procedure.set_type("procedure", "__"+self.name.get_name())
            target += convert(procedure) + "\n\n"
        if len(target) > 2:
            target = target[:-2]
        return target

    def convert_global_operators(self):
        """
        Converts all global operators in the profile to a string format.
        """
        target = ""
        for _, operators in self.operators:
            target += convert(operators) + "\n\n"
        if len(target) > 2:
            target = target[:-2]
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

    def get_instances(self):
        """
        Retrieves instances defined in the profile.
        """
        ins = ""
        if self.instance_type == "range":
            ins = str(self.instances).replace(
                "'", "").replace("[", "{").replace("]", "}")
        else:
            ins = "\", \"".join(self.instances)
        return ins

    def gen_default_profile_state(self):
        """
        Generates the default profile state based on variables and their initializations.
        """
        target = "["
        for var_name in self.local_shared_vars:
            target += f"{var_name} |-> {convert(self.local_shared_vars[var_name].get_init())},"
        if len(self.local_shared_vars) > 0:
            target = target[:-1]
        return target + "]"

    def get_name(self):
        return self.name.get_name()

    def convert_local_shared_declare(self):
        """
        Converts local shared variable declarations in the profile to a string format.
        """
        target = ""
        if self.local_shared_vars is None or len(self.local_shared_vars) == 0:
            return target
        target += f"{self.default_profile_state_instance()} = [r \\in {self.get_instances()} |-> {self.gen_default_profile_state()}]"
        return target


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
            elif isinstance(i, Set) or isinstance(i, Variable) or isinstance(i, Range)\
                    or isinstance(i, FuncCall):
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
            then_k = "then"
            else_k = "else"
            end_k = "end if;"

        target = f"{if_k} {convert(self.condition)} {then_k}\n"
        with indent:
            target += indent(self.suite.convert())
            target = remove_blank_line(target)
            if target.endswith(":"):
                target = remove_last_line(target)
        if self.elifs is not None:
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
    """
    Represents a variable within a comprehension construct, extending from the Assign class.
    """

    def __init__(self, data, m=None):
        super().__init__(data, m)
        self.var = data[0]
        self.suite = data[1]

    def analyze(self, context=Context()):
        context = deepcopy(context)
        context["init_expr"] = self.suite
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
            target += f"elsif {convert(elif_[0])} then\n"
            with indent:
                target += indent(convert(elif_[1])) + "\n"
        return target[:-1]


class WhileStmt(ProfileObject):
    """
    Represents a 'while' loop statement, encapsulating the condition and the suite of statements to execute.
    """

    def __init__(self, data, m=None) -> None:
        self.condition = data[0]
        self.suite = data[1]

    def analyze(self, context=Context()):
        analyze(self.condition, context)
        analyze(self.suite, context)

    def convert(self, indent=Indent()):
        indent = Indent()
        target = "while " + convert(self.condition) + " do\n"
        with indent:
            target += indent(convert(self.suite))
        target = remove_blank_line(target)
        if target.endswith(":"):
            target = remove_last_line(target)
        target += "\nend while;"
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
        # print("with items", self.convert())

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
    Represents raw code of TLA+ that is directly included in the output without modification.
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
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def analyze(self, context=Context()):
        analyze(self.data[0], context)
        analyze(self.data[1], context)

    def convert(self, indent=Indent()):
        return convert(self.data[0]) + ".." + convert(self.data[1])


class LogicTest(ProfileObject):
    """
    Represents a logical test expression that can be a part of complex logical statements.
    """

    def __init__(self, data, op) -> None:
        self.data = data
        self.op = op

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
        super().__init__(data, " /\\ ")


class OrTest(LogicTest):
    """
    Represents a logical 'OR' test, derived from LogicTest.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, " \\/ ")


class NotTest(ProfileObject):
    """
    Represents a logical 'NOT' test.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]
        # print(self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        # return "~"
        return "~" + convert(self.data)


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
        debug(c(data))

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return ""


class ExtendName(ProfileObject):
    """
    Represents a name used in an extend statement, typically for extending functionalities
    from other modules.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data[0]

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return convert(self.data)


class ExtendStmt(ProfileObject):
    """
    Represents an extend statement, commonly used for including additional functionalities
    or modules.
    """

    def __init__(self, data, m) -> None:
        self.data = data[0]
        self.m = m
        self.libs = convert(self.data)

    def analyze(self, context=Context()):
        analyze(self.data, context)

    def convert(self, indent=Indent()):
        return ""


class FileInput(ProfileObject):
    """
    Represents the input of a file, encapsulating a PerfCal module.
    """

    def __init__(self, data, folder, m=None, tranformer=None, parse=None) -> None:
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
        self.const_vars = []
        self.is_anonymous = False
        self.folder = folder
        self.target = ""
        self.analyze()

    def __auto_default_var(self):
        """
        Automatically defines default variables if no profile variable is present.
        """
        # If there is no profile variable, automatically define
        if len(self.prof_vars) == 0:
            for name, profile in self.profiles:
                var_name = name + "_var"
                var = Variable(var_name)
                var.set_type("Profile")
                self.prof_vars[var_name] = var
                profile["vars"].append(var_name)
                self.vars[var_name] = var
                self.symbols[var_name] = var

    def analyze(self, context=Context()):
        for statement in self.statements:
            if isinstance(statement, MacroDef):
                self.macros.append(statement)
            if isinstance(statement, SimpleStmt):
                statement = statement.extract()

            if isinstance(statement, Profile):
                name = statement.name.get_name()
                add_var_to_dict(self.profiles, name, {
                                "profile_declare": statement, "vars": [], "range": None})
                add_var_to_dict(self.symbols, name, statement)

            if isinstance(statement, Assign):
                var = statement.get_var()
                analyze(statement, context)
                if isinstance(statement.exprs[0], FuncCall):
                    called = statement.exprs[0].name.get_name()
                    if called in self.symbols:
                        called_obj = self.symbols[called]
                        if isinstance(called_obj, Profile):
                            var.set_type("Profile")
                            self.prof_vars[var.get_name()] = var
                            self.profiles[called_obj.name.get_name()]["vars"].append(
                                var.get_name())
                self.vars[var.get_name()] = var
                self.symbols[var.get_name()] = var
            if isinstance(statement, Comparison) and statement.op == "\\in":
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
                self.const_vars.append(statement)

        self.__parse_libs()

        self.__auto_default_var()

        context["global_vars"] = self.vars
        context["instances"] = {}
        for p_name, profile in self.profiles:
            context["instances"][p_name] = {"range": profile.get(
                "range"), "vars": profile.get("vars")}
        context["libs"] = list(self.libs.keys())
        for statement in self.statements:
            analyze(statement, context)

    def __parse_libs(self):
        """
        Parses libraries used in the file and integrates them into the current context.
        """
        for lib in self.libs:
            if lib in self.libs and self.libs[lib] is not None:
                continue
            try:
                source_code = load_source_code(lib, folder=self)
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
        # Generate Module head
        target = "------------------------------- MODULE " + \
            module + " -------------------------------\n"
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

    @staticmethod
    def convert_variables(prof, indent=Indent()):
        """
        Converts variables in the given profile to a string representation.
        """
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

    def __convert_const(self, indent=Indent()):
        """
        Converts constant assignments to a string representation.
        """
        target = ""
        for statement in self.const_vars:
            target += convert(statement) + "\n"
        return target

    def __convert_extends(self, indent=Indent()):
        """
        Converts 'extends' statements to a string representation.
        """
        target = ""
        for lib in self.extends_libs:
            code = load_source_code(lib, self.folder, ".tla")
            target += code + "\n"
        return target

    def __convert_global_variables(self, indent=Indent()):
        """
        Converts global variables to a string representation.
        """
        target = "variables\n"
        proc_instances = set()
        with indent:
            var_str = FileInput.convert_variables(self, indent)
            if len(var_str) > 0:
                target += indent(var_str) + "\n"
            if not self.is_anonymous:
                for _, profile in self.profiles.items():
                    proc_instances = proc_instances | set(
                        profile["profile_declare"].get_process_instances())
                proc_instances = str(proc_instances).replace("'", '"')
                target += indent(
                    f"__call_stack = [p \\in {proc_instances} |-> <<>>];") + "\n"
            target += indent("__path = 0;") + "\n"
            for _, profile in self.profiles.items():
                local_shared_declare = f"{profile['profile_declare'].convert_local_shared_declare()}"
                if len(local_shared_declare) > 0:
                    target += f"{indent(local_shared_declare)}" + ";\n"
            for lib in self.libs:
                lib_profile = self.libs[lib]
                target += indent("\\* Variables from " + lib) + "\n"
                target += indent(FileInput.convert_variables(lib_profile)) + "\n"
        return target[:-1]

    def __convert_operators(self):
        """
        Converts operators defined in the file to a string representation.
        """
        indent = Indent()
        target = "define\n"
        with indent:
            for _, profile in self.profiles.items():
                op_target = profile["profile_declare"].convert_global_operators(
                )
                if op_target == "":
                    continue
                target += indent(op_target) + "\n"
        if target == "define\n":
            return ""
        target += "end define;"
        return target

    def __convert_macros(self):
        """
        Converts macros defined in the file to a string representation.
        """
        target = "\n"
        for m in self.macros:
            target += convert(m) + "\n"
        return target

    @staticmethod
    def convert_procs(obj):
        """
        Converts procedures in the given object to a string representation.
        """
        if obj is None:
            return ""
        target = ""
        for _, profile in obj.profiles.items():
            target += profile["profile_declare"].convert_global_procedures() + \
                "\n"
        return target

    def __convert_procedures(self):
        """
        Converts procedures defined in the file to a string representation.
        """
        target = FileInput.convert_procs(self)
        for name in self.libs:
            lib = self.libs[name]
            target += FileInput.convert_procs(lib)
        return target

    def __convert_process(self, indent=Indent()):
        """
        Converts process constructs defined in the file to a string representation.
        """
        target = ""
        for _, profile in self.profiles.items():
            if profile["profile_declare"].has_process():
                target += profile["profile_declare"].convert_process() + "\n"
        return target


class Newline(ProfileObject):
    """
    Represents a newline character in the profile object model, typically used for
    formatting output.
    """

    def convert(self, indent=Indent()):
        return ""


class ConstAssign(ProfileObject):
    """
    Represents a constant assignment in the profile object model.
    """

    def __init__(self, data, m=None):
        self.data = data[0]
        self.m = m

    def convert(self, indent=Indent()):
        target = ""
        var = self.data.get_var()
        expr = self.data.get_expr()
        if var is not None and expr is not None:
            target = f"{convert(var)} == {convert(expr)}"

        return target


class SimpleStmt(ProfileObject):
    """
    Represents a simple statement, potentially containing multiple sub-statements, in the
    profile object model.
    """

    def __init__(self, data, m=None) -> None:
        self.data = data

    def simple_assign(self, types):
        """
        Identifies if the simple statement contains an assignment of specified types.
        """
        for i in self.data:
            for typ in types:
                if isinstance(i, typ):
                    return i
        return None

    def extract(self):
        """
        Extracts and returns the first sub-statement from the simple statement.
        """
        if len(self.data) >= 1:
            return self.data[0]
        return self

    def analyze(self, context=Context()):
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


class Process(ProfileObject):
    """
    Represents a process in the profile object model, typically used in parallel or
    concurrent computations.
    """


class MacroDef(FuncDef):
    """
    Represents a macro definition in the profile object model, extending from the FuncDef class.
    """

    def __init__(self, data, m=None) -> None:
        super().__init__(data, m)
        self.data = data
        self.m = m
        self.m_name = self.data[0]
        self.m_params = self.data[1]
        self.m_suite = self.data[3]

    def analyze(self, context=Context()):
        context.enter_macro(convert(self.m_name))
        analyze(self.data, context)
        context.exit_macro()

    def convert(self, indent=Indent()):
        indent = Indent()
        target = f"macro {convert(self.m_name)} ({convert(self.m_params)}) begin" + "\n"
        with indent:
            target += indent(convert(self.m_suite)) + "\n"
        target += "end macro;"
        return target


class MODULE(ProfileObject):
    """
    Represents a module in the profile object model, encapsulating various statements and
    constructs.
    """

    def __init__(self, data, m=None):
        self.data = data
