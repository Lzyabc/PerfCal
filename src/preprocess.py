"""
This module is for processing annotations in source code.
"""


def complete_ann(source_code):
    """
    Adds closing '#}' comments to lines that start with '#@' and
    do not end with '{'.
    Args:
        source_code (str): The source code to process.

    Returns:
        str: The modified source code with closing comments added.
    """
    lines = source_code.split('\n')
    stack = []
    for i, _ in enumerate(lines):
        line = lines[i].strip()
        if line.startswith('#@') and not line.endswith('{'):
            stack.append(i)
        else:
            lines[i] = lines[i] + "\n#} "*len(stack)
            stack = []
    return '\n'.join(lines)
