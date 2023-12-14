import sys

from lark import Lark, Transformer, v_args
from lark.indenter import PythonIndenter
from preprocess import complete_ann
# from tla import env

# kwargs = dict(postlex=PythonIndenter(), start='file_input')
kwargs = dict(start='file_input')

profile_parser = Lark.open('perfcal.lark', rel_to=__file__, parser='lalr', propagate_positions=True, **kwargs)
parse = profile_parser.parse

class TreeToObject(Transformer):
    def __init__(self, env, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens)
        self.env = env

    @v_args(meta=True)
    def comment(self, m, data):
        # print("comment", data, m)
        if self.env.Comment is None:
            return None
        # print("comment", data[0], m)
        return self.env.Comment(data[0], m)

    @v_args(meta=True)
    def newline(self, m, data):
        # print("newline", data)
        # for d in data:
        #     if isinstance(d, self.env.Comment):
                # print("newline", d, d.convert())
        return self.env.Newline(data, m)

    @v_args(inline=True)
    def string(self, s):
        return s[1:-1].replace('\\"', '"')

    @v_args(meta=True)
    def profiledef(self, m, s):
        # print("profile", s)
        # print(s.data)
        return self.env.Profile(s)
    
    @v_args(meta=True)
    def name(self, m, data):
        # print(t[0], type(t))
        return self.env.Name(data[0].value)

    @v_args(meta=True)
    def number(self, m, data):
        # print("number", data)
        return self.env.Number(data, m)
    
    @v_args(meta=True)
    def assign(self, m, data):
        # print(t, t[0], t[1])
        # print(data[0])
        return self.env.Assign(data, m)
    
    @v_args(meta=True)
    def const_assign(self, m, data):
        return self.env.ConstAssign(data, m)

    @v_args(meta=True)
    def comp_op(self, m, data):
        # print("comp_op", data)
        return data
    
    @v_args(meta=True)
    def expr_stmt(self, m, data):
        if len(data) == 1:
            # print("expr_stmt", data)
            return data[0]
        else:
            print("expr_stmt", data)
            return data
        
    @v_args(meta=True)
    def simple_stmt(self, m, data):
        # print("simple_stmt", data)
        return self.env.SimpleStmt(data, m)

    @v_args(meta=True)
    def comparison(self, m, data):
        return self.env.Comparison(data, m)

    @v_args(meta=True)
    def assign_stmt(self, m, data):
        # print(data, m)
        return data[0]

    @v_args(meta=True)
    def quantifier_expr(self, m, data):
        # print(data, m)
        return self.env.QuantifierExpr(data, m)
    
    @v_args(meta=True)
    def quantifier_op(self, m, data):
        # print(data, m)
        return data[0].value
    
    @v_args(meta=True)
    def quantifier_item(self, m, data):
        # print(data, m)
        return self.env.QuantifierItem(data, m)

    @v_args(meta=True)
    def suite(self, m, data):
        # print(data, m)
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
        # PlusCal
        return self.env.WithItems(data, m)

    @v_args(meta=True)
    def with_item(self, m, data):
        # print(data, m)
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
        # print(data, m)
        return self.env.Variable(data, m)

    @v_args(meta=True)
    def process(self, m, data):
        # print("process", data)
        return self.env.Process(data, m)

    @v_args(meta=True)
    def file_input(self, m, data):
        # print("fileinput", data)
        return self.env.FileInput(data, m, TreeToObject, parse)


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
        # print("arith_expr", data)
        return self.env.ArithExpr(data, m)
    
    @v_args(meta=True)
    def shift_expr(self, m, data):
        return self.env.ShiftExpr(data, m)
    
    @v_args(meta=True)
    def fThreadpool(self, m, data):
        # print("fThreadpool", data)
        return self.env.FThreadpool(data, m)

    @v_args(meta=True)
    def term(self, m, data):
        # print("term", data)
        return self.env.Term(data, m)

    @v_args(meta=True)
    def funccall(self, m, data):
        # print("funccall", data)
        return self.env.FuncCall(data, m)

    @v_args(meta=True)
    def list(self, m, data):
        # print("list", data)
        return self.env.List(data, m)

    @v_args(meta=True)
    def set(self, m, data):
        # print("set", data)
        return self.env.Set(data, m)
    
    @v_args(meta=True)
    def key_value(self, m, data):
        # print("key_value", data)
        return data

    @v_args(meta=True)
    def dict(self, m, data):
        # print("dict", data)
        return self.env.Dict(data, m)

    @v_args(meta=True)
    def getattr(self, m, data):
        # print("getattr", data)
        return self.env.GetAttr(data, m)
    
    @v_args(meta=True)
    def annassign(self, m, data):
        # print("annassign", data)
        return self.env.AnnAssign(data, m)

    @v_args(meta=True)
    def await_expr(self, m, data):
        # print("await_expr", data)
        return self.env.AwaitExpr(data, m)


    @v_args(meta=True)
    def opdef(self, m, data):
        return self.env.OpDef(data, m)

    @v_args(meta=True)
    def comprehension_var(self, m, data):
        return self.env.ComprehensionVar(data, m)


    @v_args(meta=True)
    def getitem(self, m, data):
        # print("getitem", data)
        return self.env.GetItem(data, m)


    @v_args(meta=True)
    def let_stmt(self, m, data):
        # print("let_stmt", data)
        return self.env.LetStmt(data, m)

    @v_args(meta=True)
    def label_stmt(self, m, data):
        # print("label_stmt", data[0], type(data, m))
        return self.env.LabelStmt(data, m)

    @v_args(meta=True)
    def tuple(self, m, data):
        # print("tuple", data)
        return data

    @v_args(meta=True)
    def range(self, m, data):
        # print("range", data)
        return self.env.Range(data, m)

    @v_args(meta=True)
    def and_test(self, m, data):
        # print("and_test", data)
        return self.env.AndTest(data, m)

    @v_args(meta=True)
    def or_test(self, m, data):
        # print("or_test", data)
        return self.env.OrTest(data, m)

    @v_args(meta=True)
    def not_test(self, m, data):
        # print("not_test", data)
        return self.env.NotTest(data, m)

    @v_args(meta=True)
    def and_expr(self, m, data):
        # print("xor_test", data)
        return self.env.AndExpr(data, m)

    @v_args(meta=True)
    def or_expr(self, m, data):
        # print("xor_test", data)
        return self.env.OrExpr(data, m)
    
    @v_args(meta=True)
    def xor_expr(self, m, data):
        # print("xor_test", data)
        return self.env.XorExpr(data, m)

    @v_args(meta=True)
    def assert_stmt(self, m, data):
        # print("assert_stmt", data)
        return self.env.AssertStmt(data, m)

    @v_args(meta=True)
    def return_stmt(self, m, data):
        # print("return_stmt", data)
        return self.env.ReturnStmt(data, m=m)

    @v_args(meta=True)
    def condition(self, m, data):
        # print("condition", data)
        return self.env.Condition(data, m)

    @v_args(meta=True)
    def dotted_name(self, m, data):
        # print("DottedName", data)
        return self.env.DottedName(data, m)
    
    @v_args(meta=True)
    def dotted_as_name(self, m, data):
        # print("dotted_as_name", data)
        return self.env.DottedAsName(data, m)

    @v_args(meta=True)
    def dotted_as_names(self, m, data):
        # print("dotted_as_names", data)
        return self.env.DottedAsNames(data, m)

    @v_args(meta=True)
    def import_name(self, m, data):
        # print("import_name", data)
        return self.env.ImportName(data, m)

    @v_args(meta=True)
    def import_stmt(self, m, data):
        # print("import_stmt", data)
        return self.env.ImportStmt(data, m)

    @v_args(meta=True)
    def slice(self, m, data):
        # print("slice", data)
        return self.env.Slice(data, m)
        

    # list = list
    # key_value = tuple
    # dict = dict
    set = set
    number = v_args(inline=True)(float)

    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False
    const_true = lambda self, _: True
    const_false = lambda self, _: False

def parse_source_code(env, source_code):
    source_code = complete_ann(source_code)
    with open("tmp.prc", "w") as f:
        f.write(source_code)
    return TreeToObject(env).transform(parse(source_code))


### Create the JSON parser with Lark, using the Earley algorithm
# json_parser = Lark(json_grammar, parser='earley', lexer='basic')
# def parse(x):
#     return TreeToJson().transform(json_parser.parse(x))

### Create the JSON parser with Lark, using the LALR algorithm
# json_parser = Lark(json_grammar, parser='lalr',
#                    propagate_positions=True,
#                    start='value'
#                    )



