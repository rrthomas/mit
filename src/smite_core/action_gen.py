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


# Utility functions for StackPicture
def stack_item_name(item):
    return item.split(":")[0]

def stack_item_type(item):
    l = item.split(":")
    return l[1] if len(l) > 1 else 'smite_WORD'

def item_size(item):
    '''Return a C expression for the size in stack words of a stack item.'''
    return '(sizeof({}) / smite_word_size)'.format(stack_item_type(item))

def load_var(pos, var):
    if stack_item_type(var) != 'smite_WORD':
        fmt = 'UNCHECKED_LOAD_STACK_TYPE({pos}, {type}, &{var})'
    else:
        fmt = 'UNCHECKED_LOAD_STACK({pos}, &{var})'
    return fmt.format(
        pos=pos,
        var=stack_item_name(var),
        type=stack_item_type(var)) + ';'

def store_var(pos, var):
    if stack_item_type(var) != 'smite_WORD':
        fmt = 'UNCHECKED_STORE_STACK_TYPE({pos}, {type}, {var})'
    else:
        fmt = 'UNCHECKED_STORE_STACK({pos}, {var})'
    return fmt.format(
        pos=pos,
        var=stack_item_name(var),
        type=stack_item_type(var)) + ';'


class StackPicture:
    '''
    Represents a description of the topmost items on the stack. The effect
    of an instruction can be described using two StackPictures: one for the
    arguments and one for the results.

    Variadic instructions (such as POP, DUP, SWAP) have an argument called
    "COUNT" which is (N.B.!) one less than the number of additional
    (unnamed) items are on the stack. The `is_variadic` flag is
    per-StackPicture, not per instruction. For example, POP has variadic
    arguments but non-variadic results.

    Public fields:

     - named_items - list of str - the names of the non-variadic items,
       which must be on the top of the stack, and might include "COUNT".
       Each name may optionally be followed by ":TYPE" to give the C type of
       the underlying quantity, if it might be bigger than one stack word.

     - is_variadic - bool - If `True`, there are `COUNT` more items underneath
       the non-variadic items.
    '''
    def __init__(self, named_items, is_variadic=False):
        assert len(set(named_items)) == len(named_items)
        self.named_items = named_items
        self.is_variadic = is_variadic

    @staticmethod
    def from_list(stack):
        '''
         - stack - a stack picture as found in `vm_data.Action`, i.e. a list of
           str. The first item is 'ITEMS' if the stack picture is variadic.
           All other items are the names of items.
        Returns a StackPicture.
        '''
        if stack and stack[0] == 'ITEMS':
            return StackPicture(stack[1:], is_variadic=True)
        else:
            return StackPicture(stack)

    def static_depth(self):
        '''
        Return a C expression for the number of stack words occupied by the
        static items in a StackPicture.
        '''
        depth = ' + '.join([item_size(item) for item in self.named_items])
        return '({})'.format(depth if depth != '' else '0')

    def dynamic_depth(self):
        '''
        Returns a C expression that computes the total number of items,
        including the variadic items. Assumes:
         - the C variable `COUNT` contains the number of variadic items.
        '''
        depth = self.static_depth()
        if self.is_variadic:
            depth = '((smite_UWORD)COUNT + 1 + {})'.format(depth)
        return depth

    def declare_vars(self):
        '''Returns C variable declarations for all of `self.named_items`.'''
        return '\n'.join(['{} {};'.format(stack_item_type(i), stack_item_name(i))
                          for i in self.named_items])

    def load(self):
        '''
        Returns C source code to read the named items from the stack into C
        variables.
        `S->STACK_DEPTH` is not modified.
        '''
        code = []
        pos = ['-1']
        for i in reversed(self.named_items):
            pos.append(item_size(i))
            code.append(load_var("+".join(pos), i))
        return '\n'.join(code)

    def store(self):
        '''
        Returns C source code to write the named items from C variables into
        the stack.
        `S->STACK_DEPTH` must be modified first.
        '''
        code = []
        pos = ['-1']
        for i in reversed(self.named_items):
            pos.append(item_size(i))
            code.append(store_var("+".join(pos), i))
        return '\n'.join(code)


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
    S->BAD = {num_pops};
    const smite_UWORD static_args = 0;
    RAISE(3);
}}'''.format(num_pops=num_pops))

def check_pops_then_pushes(num_pops, num_pushes):
    return disable_warnings(['-Wtype-limits', '-Wtautological-compare'], '''\
if ({num_pushes} > {num_pops} && (S->STACK_SIZE - S->STACK_DEPTH < {num_pushes} - {num_pops})) {{
    S->BAD = {num_pushes} - {num_pops};
    RAISE(2);
}}'''.format(num_pops=num_pops, num_pushes=num_pushes))

def gen_case(event):
    # Concatenate the pieces.
    args = StackPicture.from_list(event.args)
    results = StackPicture.from_list(event.results)
    dynamic_args = args.dynamic_depth()
    dynamic_results = results.dynamic_depth()
    code = '\n'.join([
        args.declare_vars(),
        results.declare_vars(),
        'const smite_UWORD static_args = {};'.format(args.static_depth()),
        check_pops('static_args'),
        args.load(),
        check_pops(dynamic_args),
        check_pops_then_pushes(dynamic_args, dynamic_results),
        'S->STACK_DEPTH -= static_args;',
        textwrap.dedent(event.code.rstrip()),
        'S->STACK_DEPTH += {num_pushes} - ({num_pops} - {nstatic_args});'.format(num_pops=dynamic_args, num_pushes=dynamic_results, nstatic_args='static_args'),
        results.store(),
    ])
    # Remove newlines resulting from empty strings in the above.
    code = re.sub('\n+', '\n', code, flags=re.MULTILINE).strip('\n')
    return code

def dispatch(actions, prefix, undefined_case):
    '''Generate dispatch code for some Actions.

    actions - Enum of Actions.
    '''
    output = '        switch (I) {\n'
    for (instruction, action) in actions.__members__.items():
        output += '''\
        case {prefix}{instruction}:
            {{
{code}
            }}
            break;\n'''.format(
                    instruction=instruction,
                    prefix=prefix,
                    code=textwrap.indent(gen_case(action.value), '                '))
    output += '''
        default:
{}
            break;
        }}'''.format(undefined_case)
    return output
