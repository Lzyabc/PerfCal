def complete_ann(source_code):
    lines = source_code.split('\n')
    stack = []
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith('#@') and not line.endswith('{'):
            stack.append(i)
        else:
            lines[i] = lines[i] + "\n#} "*len(stack)
            stack = []
    return '\n'.join(lines)