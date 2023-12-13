import sys

from lark import Lark, Transformer, v_args
from pparser import parse_source_code
# from tla.env import convert
from check import Model

import tla.env as tla_env
import go.env as go_env
import go.package as go_package
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Compile input file to either Go or TLA+')
    subparsers = parser.add_subparsers(dest='mode', required=True)

    # cgo subcommand
    go_parser = subparsers.add_parser('go', help='Compile input file to Go')
    go_parser.add_argument('-i', '--input', type=str, required=True, help='Input file path')
    go_parser.add_argument('-o', '--output', type=str, required=True, help='Output file path')

    # tla subcommand
    tla_parser = subparsers.add_parser('tla', help='Compile input file to TLA+')
    tla_parser.add_argument('-i', '--input', type=str, required=True, help='Input file path')
    tla_parser.add_argument('-o', '--output', type=str, required=True, help='Output file path')
    tla_parser.add_argument('-a', '--action', type=str, default='all', help='Action to perform on the TLA+ file')

    args = vars(parser.parse_args())
    return args


def to_tla(args):
    path = args["input"]
    mode = args["action"]
    with open(path) as f:
        source_code = f.read()
    profiles = parse_source_code(tla_env, source_code+"\n")
    name = path.split("/")[-1].split(".")[0]
    # print(profiles, type(profiles))
    # ret = profiles.to_json()
    # print(ret)
    
    print("name", name)

    # print(profiles, type(profiles))
    print("converted:\n")
    print(tla_env.convert(profiles))
    model = Model(name, profiles)
    model.save()
    print(mode)
    if mode == "all" or mode == "cp":
        model.trans()
    if mode == "all" or mode == "run":
        model.run()

def to_go(args):
    input = args["input"]
    output = args["output"]
    with open(input) as f:
        source_code = f.read()
    goCode = parse_source_code(go_env, source_code+"\n")
    goPackage = go_env.save(goCode, output)

if __name__ == "__main__":
    args = parse_args()
    if args["mode"] == "tla":
        to_tla(args)
    elif args["mode"] == "go":
        to_go(args)
    else:
        raise Exception("Invalid mode")
