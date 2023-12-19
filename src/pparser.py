"""
This module provides functionalities for parsing and transforming trees into custom 
objects. It uses the Lark parser to interpret a specific grammar defined in 'perfcal.lark'.

Classes:
    TreeToObject: A Transformer class that converts a parse tree into a series of 
                  self-defined objects.

The module begins by defining parser configurations and creating a Lark parser instance
for the specific grammar. The `TreeToObject` class inherits from `Transformer` and is 
used to transform the parse tree into a series of objects defined in an environment.

Each method in the `TreeToObject` class corresponds to a different type of node in the 
parse tree, such as comments, strings, profile definitions, names, numbers, assignments,
and constant assignments. These methods are decorated with `v_args` to modify their 
behavior, and some capture metadata about the tree nodes.

Key Functionalities:
    - Parse and transform various elements of a given grammar (like comments, strings, assignments).
    - Support for inline transformations and capturing metadata.
    - Conversion of specific grammar constructs into corresponding Python objects.
"""
from lark import Lark, Transformer, v_args
from preprocess import complete_ann

kwargs = dict(start='file_input')

profile_parser = Lark.open('perfcal.lark', rel_to=__file__,
                           parser='lalr', propagate_positions=True, **kwargs)
parse = profile_parser.parse


class TreeToObject(Transformer):
    """
    This class transforms a tree to self-defined object.
    """

    def __init__(self, env, folder, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens)
        self.env = env
        self.folder = folder

    @v_args(meta=True)
    def comment(self, m, data):
        """
        Comment like "# This is a comment".
        """
        if self.env.Comment is None:
            return None
        return self.env.Comment(data[0], m)

    @v_args(meta=True)
    def newline(self, m, data):
        """Blank line."""
        return self.env.Newline(data, m)

    @v_args(inline=True)
    def string(self, s):
        """String literal."""
        return s[1:-1].replace('\\"', '"')

    @v_args(meta=True)
    def profiledef(self, m, s):
        """A profile definition."""
        return self.env.Profile(s, m)

    @v_args(meta=True)
    def name(self, m, data):
        return self.env.Name(data[0].value, m)

    @v_args(meta=True)
    def number(self, m, data):
        return self.env.Number(data, m)

    @v_args(meta=True)
    def assign(self, m, data):
        return self.env.Assign(data, m)

    @v_args(meta=True)
    def assign_link(self, m, data):
        """Assign link like "a = b $"
            will be parsed "a := b ||" in PlusCal
        """
        return self.env.AssignLink(data, m)

    @v_args(meta=True)
    def const_assign(self, m, data):
        return self.env.ConstAssign(data, m)

    @v_args(meta=True)
    def comp_op(self, m, data):
        return data

    @v_args(meta=True)
    def expr_stmt(self, m, data):
        if len(data) == 1:
            return data[0]
        else:
            print("expr_stmt", data)
            return data

    @v_args(meta=True)
    def simple_stmt(self, m, data):
        return self.env.SimpleStmt(data, m)

    @v_args(meta=True)
    def comparison(self, m, data):
        return self.env.Comparison(data, m)

    @v_args(meta=True)
    def assign_stmt(self, m, data):
        return data[0]

    @v_args(meta=True)
    def quantifier_expr(self, m, data):
        return self.env.QuantifierExpr(data, m)

    @v_args(meta=True)
    def quantifier_op(self, m, data):
        # print(data, m)
        return data[0].value

    @v_args(meta=True)
    def quantifier_item(self, m, data):
        return self.env.QuantifierItem(data, m)

    @v_args(meta=True)
    def suite(self, m, data):
        return self.env.Suite(data, m)

    @v_args(meta=True)
    def if_stmt(self, m, data):
        return self.env.IfStmt(data, m)

    @v_args(meta=True)
    def elifs(self, m, data):
        return self.env.Elifs(data, m)

    @v_args(meta=True)
    def elif_(self, m, data):
        return data

    @v_args(meta=True)
    def while_stmt(self, m, data):
        return self.env.WhileStmt(data, m)

    @v_args(meta=True)
    def with_stmt(self, m, data):
        return self.env.WithStmt(data, m)

    @v_args(meta=True)
    def with_items(self, m, data):
        return self.env.WithItems(data, m)

    @v_args(meta=True)
    def with_item(self, m, data):
        return self.env.WithItem(data, m)

    @v_args(meta=True)
    def either_clause(self, m, data):
        return self.env.EitherClause(data, m)

    @v_args(meta=True)
    def either_clauses(self, m, data):
        return data

    @v_args(meta=True)
    def either_stmt(self, m, data):
        return self.env.EitherStmt(data, m)

    @v_args(meta=True)
    def arguments(self, m, data):
        return self.env.Arguments(data, m)

    @v_args(meta=True)
    def var(self, m, data):
        return self.env.Variable(data, m)

    @v_args(meta=True)
    def process(self, m, data):
        return self.env.Process(data, m)

    @v_args(meta=True)
    def file_input(self, m, data):
        return self.env.FileInput(data, self.folder, m, TreeToObject, parse)

    @v_args(meta=True)
    def parameters(self, m, data):
        return self.env.Parameters(data, m)

    @v_args(meta=True)
    def funcdef(self, m, data):
        return self.env.FuncDef(data, m)

    @v_args(meta=True)
    def procdef(self, m, data):
        return self.env.ProcDef(data, m)

    @v_args(meta=True)
    def macrodef(self, m, data):
        return self.env.MacroDef(data, m)

    @v_args(meta=True)
    def arith_expr(self, m, data):
        return self.env.ArithExpr(data, m)

    @v_args(meta=True)
    def shift_expr(self, m, data):
        return self.env.ShiftExpr(data, m)

    @v_args(meta=True)
    def factor(self, m, data):
        return self.env.Factor(data, m)

    @v_args(meta=True)
    def term(self, m, data):
        return self.env.Term(data, m)

    @v_args(meta=True)
    def funccall(self, m, data):
        return self.env.FuncCall(data, m)

    @v_args(meta=True)
    def list(self, m, data):
        return self.env.List(data, m)

    @v_args(meta=True)
    def set(self, m, data):
        return self.env.Set(data, m)

    @v_args(meta=True)
    def key_value(self, m, data):
        return data

    @v_args(meta=True)
    def dict(self, m, data):
        return self.env.Dict(data, m)

    @v_args(meta=True)
    def getattr(self, m, data):
        return self.env.GetAttr(data, m)

    @v_args(meta=True)
    def annassign(self, m, data):
        return self.env.AnnAssign(data, m)

    @v_args(meta=True)
    def await_expr(self, m, data):
        return self.env.AwaitExpr(data, m)

    @v_args(meta=True)
    def opdef(self, m, data):
        return self.env.OpDef(data, m)

    @v_args(meta=True)
    def comprehension_var(self, m, data):
        return self.env.ComprehensionVar(data, m)

    @v_args(meta=True)
    def getitem(self, m, data):
        return self.env.GetItem(data, m)

    @v_args(meta=True)
    def let_stmt(self, m, data):
        return self.env.LetStmt(data, m)

    @v_args(meta=True)
    def label_stmt(self, m, data):
        return self.env.LabelStmt(data, m)

    @v_args(meta=True)
    def tuple(self, m, data):
        return data

    @v_args(meta=True)
    def range(self, m, data):
        return self.env.Range(data, m)

    @v_args(meta=True)
    def and_test(self, m, data):
        return self.env.AndTest(data, m)

    @v_args(meta=True)
    def or_test(self, m, data):
        return self.env.OrTest(data, m)

    @v_args(meta=True)
    def not_test(self, m, data):
        return self.env.NotTest(data, m)

    @v_args(meta=True)
    def and_expr(self, m, data):
        return self.env.AndExpr(data, m)

    @v_args(meta=True)
    def or_expr(self, m, data):
        return self.env.OrExpr(data, m)

    @v_args(meta=True)
    def xor_expr(self, m, data):
        return self.env.XorExpr(data, m)

    @v_args(meta=True)
    def assert_stmt(self, m, data):
        return self.env.AssertStmt(data, m)

    @v_args(meta=True)
    def return_stmt(self, m, data):
        return self.env.ReturnStmt(data, m=m)

    @v_args(meta=True)
    def condition(self, m, data):
        return self.env.Condition(data, m)

    @v_args(meta=True)
    def dotted_name(self, m, data):
        return self.env.DottedName(data, m)

    @v_args(meta=True)
    def dotted_as_name(self, m, data):
        return self.env.DottedAsName(data, m)

    @v_args(meta=True)
    def dotted_as_names(self, m, data):
        return self.env.DottedAsNames(data, m)

    @v_args(meta=True)
    def import_name(self, m, data):
        return self.env.ImportName(data, m)

    @v_args(meta=True)
    def import_stmt(self, m, data):
        return self.env.ImportStmt(data, m)

    @v_args(meta=True)
    def extend_name(self, m, data):
        return self.env.ExtendName(data, m)

    @v_args(meta=True)
    def extend_stmt(self, m, data):
        return self.env.ExtendStmt(data, m)

    @v_args(meta=True)
    def slice(self, m, data):
        return self.env.Slice(data, m)

    set = set
    number = v_args(inline=True)(float)

    def null(self, _): return None
    def true(self, _): return True
    def false(self, _): return False
    def const_true(self, _): return True
    def const_false(self, _): return False


def parse_source_code(env, source_code, folder):
    source_code = complete_ann(source_code)
    with open("tmp.prc", "w", encoding="utf-8") as f:
        f.write(source_code)
    return TreeToObject(env, folder).transform(parse(source_code))
