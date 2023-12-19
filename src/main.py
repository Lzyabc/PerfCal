"This file is the main entry point for the PerfCal compiler."
import os
import argparse
from pparser import parse_source_code
from check import Model
import tla.env as tla_env
import go.env as go_env


def parse_args():
    """
    Parse command line arguments.

    This function creates a command line argument parser and 
    defines two subparsers for different modes: 'go' and 'tla'.
    Each mode has its own set of arguments.

    Subparser 'go':
    - Compiles an input file to Go.
    - Requires 'input' and 'output' file paths as arguments.

    Subparser 'tla':
    - Compiles an input file to TLA+.
    - Requires 'input' and 'output' file paths as arguments.
    - Optionally takes an 'action' argument with a default value of 'all'.
    """
    parser = argparse.ArgumentParser(
        description='Compile input file to either Go or TLA+')
    subparsers = parser.add_subparsers(dest='mode', required=True)

    # cgo subcommand
    go_parser = subparsers.add_parser('go', help='Compile input file to Go')
    go_parser.add_argument('-i', '--input', type=str,
                           required=True, help='Input file path')
    go_parser.add_argument('-o', '--output', type=str,
                           required=True, help='Output file path')

    # tla subcommand
    tla_parser = subparsers.add_parser(
        'tla', help='Compile input file to TLA+')
    tla_parser.add_argument('-i', '--input', type=str,
                            required=True, help='Input file path')
    tla_parser.add_argument('-o', '--output', type=str,
                            required=True, help='Output file path')
    tla_parser.add_argument('-a', '--action', type=str,
                            default='all', help='Action to perform on the TLA+ file')
    return parser, vars(parser.parse_args())


def to_tla(cmd_args):
    """
    Convert input file to TLA+.

    Args:
        cmd_args (dict): Command line arguments.

    Returns:
        None
    """
    path = cmd_args["input"]
    mode = cmd_args["action"]
    with open(path, encoding="utf-8") as f:
        source_code = f.read()
    folder = os.path.dirname(path)
    profiles = parse_source_code(tla_env, source_code+"\n", folder)
    name = path.split("/")[-1].split(".")[0]
    model = Model(name, profiles)
    model.save()
    if mode == "all" or mode == "cp":
        model.trans()
    if mode == "all" or mode == "run":
        model.run()


def to_go(cmd_args):
    """
    Convert input file to Go.

    Args:
        cmd_args (dict): Command line arguments.

    Returns:
        None
    """
    path = cmd_args["input"]
    output = cmd_args["output"]
    with open(path, encoding="utf-8") as f:
        source_code = f.read()
    folder = os.path.dirname(path)
    go_code = parse_source_code(go_env, source_code+"\n", folder)
    go_env.save(go_code, output)


if __name__ == "__main__":
    pr, args = parse_args()
    if args["mode"] == "tla":
        to_tla(args)
    elif args["mode"] == "go":
        to_go(args)
    else:
        pr.print_help()
