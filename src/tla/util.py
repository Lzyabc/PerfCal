"""
This module provides utilities for converting, analyzing, and loading various types of data. 
It includes functions for generic data conversion based on object type, analyzing objects
within a given context, loading source code from files, counting newline characters, and 
loading JSON data. It also handles specific environmental settings for data conversion and
integrates configurations for file paths.
"""
import os
import json
from . import config

def get_convert(env):
    """
    Returns a conversion function based on the specified environment.
    """
    def convert(obj):
        if obj is None:
            return ""
        if hasattr(obj, 'convert'):
            res = obj.convert()
            return res
        elif isinstance(obj, list):
            return [convert(x) for x in obj]
        elif isinstance(obj, tuple):
            return tuple(convert(x) for x in obj)
        elif isinstance(obj, dict):
            return {convert(k): convert(v) for k, v in obj.items()}
        elif isinstance(obj, bool):
            if env == "tla":
                return str(obj).upper()
            else:
                return str(obj).lower()
        elif isinstance(obj, int):
            return str(obj)
        elif isinstance(obj, float):
            return str(int(obj))
        elif isinstance(obj, str):
            return f"\"{obj}\""
        else:
            return str(obj)
    return convert

def analyze(obj, context=None):
    """
    Analyzes an object within a given context.
    """
    if obj is None:
        return False
    if hasattr(obj, 'analyze'):
        obj.analyze(context)
    elif isinstance(obj, list):
        for x in obj:
            analyze(x, context)
    elif isinstance(obj, tuple):
        for x in obj:
            analyze(x, context)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            analyze(k, context)
            analyze(v, context)
    else:
        pass

def load_source_code(lib, folder, suffix=".prc"):
    """
    Loads source code from a file located in the specified folder or a default module path.
    """
    filename = os.path.join(folder, lib + suffix)
    if not os.path.exists(filename):
        filename = os.path.join(config.module_path, lib + suffix)
    if not os.path.exists(filename):
        print("load_source_code", filename, "not exists")
        return ""
    with open(filename, encoding="utf-8") as f:
        source_code = f.read()
    return source_code

def count_lines(src):
    """
    Counts the number of newline characters at the end of a string.
    """
    n = 0
    for i in range(len(src)):
        if src[len(src)-i-1] == "\n":
            n += 1
        else:
            return n
    return n

def newline(src, n=1, m=0):
    """
    Ensures that a string ends with a specified number of newline characters.
    """
    if len(src) > m:
        blank_lines = count_lines(src[m:])
        if blank_lines > n:
            return src[:n-blank_lines]
        elif blank_lines == n:
            return src
        else:
            return src + "\n"*(n-blank_lines)
    return src


def load_json(s):
    """
    Loads a JSON object from a string, with error handling for invalid JSON.
    """
    try:
        return json.loads(s)
    except Exception as e:
        print(e)
        return s
