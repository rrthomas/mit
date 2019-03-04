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

def stack_item_has_var(item):
    return item != VARIADIC_NAME

def _stack_item_to_var(item):
    assert stack_item_has_var(item)
    return item

def stack_item_name(item):
    return _stack_item_to_var(item).split(":")[0]

def stack_item_type(item):
    l = _stack_item_to_var(item).split(":")
    return l[1] if len(l) > 1 else 'smite_WORD'

# Calculate (symbolic) depth of stack picture
def item_size(item):
    if stack_item_has_var(item):
        return '(sizeof({}) / smite_word_size)'.format(stack_item_type(item))
    else:
        return '(smite_UWORD)COUNT'

def stack_depth(stack):
    depth = ' + '.join([item_size(item) for item in stack])
    return '({})'.format(depth if depth != '' else '0')

# Variable creator
def make_vars(stack):
    return '\n'.join(['{} {};'.format(stack_item_type(v), stack_item_name(v))
                      for v in stack if stack_item_has_var(v)])

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

def check_static_args(args):
    return disable_warnings(['-Wtype-limits', '-Wunused-variable'], '''\
if ((S->STACK_DEPTH < {nargs})) {{
    S->BAD_ADDRESS = {nargs};
    const smite_UWORD args = 0;
    RAISE(3);
}}'''.format(nargs=len([arg for arg in args if stack_item_has_var(arg)])))

def check_dynamic_args_and_results(args, results):
    return disable_warnings(['-Wtype-limits'], '''\
if ((S->STACK_DEPTH < {nargs}) || (S->STACK_SIZE - (S->STACK_DEPTH - {nargs}) < {nresults})) {{
    S->BAD_ADDRESS = {nresults} - {nargs};
    RAISE(2);
}}'''.format(nargs=stack_depth(args), nresults=stack_depth(results)))

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
    code = []
    pos = ['-1']
    for arg in reversed(args):
        pos.append(str(item_size(arg)))
        if stack_item_has_var(arg):
            code.append(load_var("+".join(pos), arg))
    code.append('const smite_UWORD args = {};'.format(len([arg for arg in args if stack_item_has_var(arg)])))
    return '\n'.join(code)

def store_var(pos, var):
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
        if stack_item_has_var(result):
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
            make_vars(action.value.args),
            make_vars(action.value.results),
            check_static_args(action.value.args),
            load_args(action.value.args),
            check_dynamic_args_and_results(action.value.args, action.value.results),
            'S->STACK_DEPTH -= args;',
            textwrap.dedent(action.value.code.rstrip()),
            'S->STACK_DEPTH += {nresults} - ({nargs} - {nstatic_args});'.format(nargs=stack_depth(action.value.args), nresults=stack_depth(action.value.results), nstatic_args=len([arg for arg in action.value.args if stack_item_has_var(arg)])),
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
