'''
action_gen

Generate code for actions.

The main entry point is dispatch.
'''

import re
import textwrap

class Action:
    '''VM action instruction descriptor.

     - opcode - int - SMite opcode number.
     - args - list - list of stack arguments.
     - results - list - list of stack results.
     - code - str - C source code.

    C variables are created for the arguments and results; the arguments are
    pushed and results popped.

    The code should RAISE any error before writing any state, so that if an
    error is raised, the state of the VM is not changed.
    '''
    def __init__(self, opcode, args, results, code):
        self.opcode = opcode
        self.args = args
        self.results = results
        self.code = code

# Stack picture utilities
COUNT_NAME = 'COUNT'
VARIADIC_NAME = 'ITEMS'

def is_named_stack_item(item):
    return item != VARIADIC_NAME

def _stack_item_to_var(item):
    assert is_named_stack_item(item)
    return item

def stack_item_name(item):
    return _stack_item_to_var(item).split(":")[0]

def stack_item_type(item):
    l = _stack_item_to_var(item).split(":")
    return l[1] if len(l) > 1 else 'smite_WORD'

# Calculate (symbolic) depth of stack picture
def item_size(item):
    if is_named_stack_item(item):
        return '(sizeof({}) / smite_word_size)'.format(stack_item_type(item))
    else:
        return '(smite_UWORD)COUNT'

def stack_depth(stack):
    depth = ' + '.join([item_size(item) for item in stack])
    return '({})'.format(depth if depth != '' else '0')

# Variable creator
def declare_vars(stack):
    return '\n'.join(['{} {};'.format(stack_item_type(v), stack_item_name(v))
                      for v in stack if is_named_stack_item(v)])

def disable_warnings(warnings, c_source):
    '''
    Returns `c_source` wrapped in "#pragmas" to suppress the given list
    `warnings` of warning flags.
    '''
    return '''\
#pragma GCC diagnostic push
{pragmas}
{c_source}
#pragma GCC diagnostic pop'''.format(c_source=c_source,
                                     pragmas='\n'.join(['#pragma GCC diagnostic ignored "{}"'.format(w)
                                                        for w in warnings]))

def check_pops(num_pops):
    '''
    Returns C source code to check that the stack contains enough items to
    pop the specified number of items.
     - num_pops - a C expression giving the number of items to pop.
    Assumes:
     - No items have been popped so far. This is needed in the error case.
    '''
    return disable_warnings(['-Wtype-limits', '-Wunused-variable', '-Wshadow'], '''\
if ((S->STACK_DEPTH < {num_pops})) {{
    S->BAD_ADDRESS = {num_pops};
    const smite_UWORD static_args = 0;
    RAISE(3);
}}'''.format(num_pops=num_pops))

def check_pops_then_pushes(num_pops, num_pushes):
    return disable_warnings(['-Wtype-limits', '-Wtautological-compare'], '''\
if ({num_pushes} > {num_pops} && (S->STACK_SIZE - S->STACK_DEPTH < {num_pushes} - {num_pops})) {{
    S->BAD_ADDRESS = {num_pushes} - {num_pops};
    RAISE(2);
}}'''.format(num_pops=num_pops, num_pushes=num_pushes))

def load_var(pos, var):
    if stack_item_type(var) != 'smite_WORD':
        fmt = 'UNCHECKED_LOAD_STACK_TYPE({pos}, {type}, &{var})'
    else:
        fmt = 'UNCHECKED_LOAD_STACK({pos}, &{var})'
    return fmt.format(
        pos=pos,
        var=stack_item_name(var),
        type=stack_item_type(var)) + ';'

def load_args(args):
    '''
    Returns C source code to read the named arguments from the stack into C
    variables.
    `S->STACK_DEPTH` is not modified.
    '''
    code = []
    pos = ['-1']
    for arg in reversed(args):
        pos.append(str(item_size(arg)))
        if is_named_stack_item(arg):
            code.append(load_var("+".join(pos), arg))
    return '\n'.join(code)

def store_var(pos, var):
    '''
    Returns C source code to write the named arguments from C variables into
    the stack.
    `S->STACK_DEPTH` must be modified first.
    '''
    if stack_item_type(var) != 'smite_WORD':
        fmt = 'UNCHECKED_STORE_STACK_TYPE({pos}, {type}, {var})'
    else:
        fmt = 'UNCHECKED_STORE_STACK({pos}, {var})'
    return fmt.format(
        pos=pos,
        var=stack_item_name(var),
        type=stack_item_type(var)) + ';'

def store_results(args, results):
    code = []
    pos = ['-1']
    for result in reversed(results):
        pos.append(str(item_size(result)))
        if is_named_stack_item(result):
            code.append(store_var("+".join(pos), result))
    return '\n'.join(code)

def dispatch(actions, prefix, undefined_case):
    '''Generate dispatch code for some Actions.

    actions - Enum of Actions.
    '''
    output = '        switch (I) {\n'
    for (instruction, action) in actions.__members__.items():
        # Concatenate the pieces.
        code = '\n'.join([
            declare_vars(action.value.args),
            declare_vars(action.value.results),
            'const smite_UWORD static_args = {};'.format(stack_depth([arg for arg in action.value.args if is_named_stack_item(arg)])),
            check_pops('static_args'),
            load_args(action.value.args),
            check_pops(stack_depth(action.value.args)),
            check_pops_then_pushes(stack_depth(action.value.args), stack_depth(action.value.results)),
            'S->STACK_DEPTH -= static_args;',
            textwrap.dedent(action.value.code.rstrip()),
            'S->STACK_DEPTH += {num_pushes} - ({num_pops} - {nstatic_args});'.format(num_pops=stack_depth(action.value.args), num_pushes=stack_depth(action.value.results), nstatic_args='static_args'),
            store_results(action.value.args, action.value.results),
        ])
        # Remove newlines resulting from empty strings in the above.
        code = re.sub('\n+', '\n', code, flags=re.MULTILINE).strip('\n')
        output += '''\
        case {prefix}{instruction}:
            {{
{code}
            }}
            break;\n'''.format(
                    instruction=instruction,
                    prefix=prefix,
                    code=textwrap.indent(code, '                '))
    output += '''
        default:
{}
            break;
        }}'''.format(undefined_case)
    return output
