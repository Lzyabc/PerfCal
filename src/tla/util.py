import os
import json
from . import config

def GetConvert(env):
    def convert(obj):
        if obj is None:
            return ""
        if hasattr(obj, 'convert'):
            res = obj.convert()
            # if "andlerequestvoteresponse" in res and "\n" not in res and " " not in res:
            #     print("GetConvert", res)
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
            # PlusCal不支持浮点数
            # print("float", obj)
            return str(int(obj))
        elif isinstance(obj, str):
            return f"\"{obj}\""
        else:
            return str(obj)
    return convert

def analyze(obj, context={}):
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
        # print("analyze unknown type", obj, type(obj), hasattr(obj, "analyze"))
        pass

def load_source_code(lib):
    filename = os.path.join(config.module_path, lib + ".prc")
    with open(filename) as f:
        source_code = f.read()
    return source_code

def count_lines(src):
    n = 0
    for i in range(len(src)):
        if src[len(src)-i-1] == "\n":
            n += 1
        else:
            return n 
    return n

def newline(src, n=1, m=0):
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
    try:
        return json.loads(s)
    except:
        return s