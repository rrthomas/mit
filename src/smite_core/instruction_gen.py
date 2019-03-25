'''
Generate code for actions.

The main entry point is dispatch.
'''

import re
import textwrap


def print_enum(actions, prefix):
    '''Utility function to print an instruction enum.'''
    print('\nenum {')
    for (instruction, action) in actions.__members__.items():
        print("    INSTRUCTION({}{}, {:#x})".format(prefix, instruction, action.value.opcode))
    print('};')

class Action:
    '''VM action instruction descriptor.

     - opcode - int - SMite opcode number.
     - args - StackPicture.
     - results - StackPicture.
     - code - str - C source code.

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    The code should RAISE any error before writing any state, so that if an
    error is raised, the state of the VM is not changed.
    '''
    def __init__(self, opcode, args, results, code):
        '''
         - args - list acceptable to StackPicture.from_list.
         - results - list acceptable to StackPicture.from_list.
        '''
        self.opcode = opcode
        self.args = StackPicture.from_list(args)
        self.results = StackPicture.from_list(results)
        self.code = code


class StackPicture:
    '''
    Represents a description of the topmost items on the stack. The effect
    of an instruction can be described using two StackPictures: one for the
    arguments and one for the results.

    The first item is 'ITEMS' if the stack picture is variadic.
    All other items are the names of items.

    Variadic instructions (such as POP, DUP, SWAP) have an argument called
    "COUNT" which is (N.B.!) one less than the number of additional
    (unnamed) items are on the stack.

    Public fields:

     - named_items - list of str - the names of the non-variadic items,
       which must be on the top of the stack, and might include "COUNT".

     - is_variadic - bool - If `True`, there are `COUNT` more items underneath
       the non-variadic items.
    '''
    def __init__(self, named_items, is_variadic=False):
        assert len(set(named_items)) == len(named_items)
        assert 'ITEMS' not in named_items
        self.named_items = named_items
        self.is_variadic = is_variadic

    @classmethod
    def from_list(cls, stack):
        '''
         - stack - list of str - a stack picture.

        Returns a StackPicture.
        '''
        if stack and stack[0] == 'ITEMS':
            return cls(stack[1:], is_variadic=True)
        else:
            return cls(stack)

    @classmethod
    def load_var(cls, pos, var):
        return 'UNCHECKED_LOAD_STACK({pos}, &{var});'.format(pos=pos, var=var)

    @classmethod
    def store_var(cls, pos, var):
        return 'UNCHECKED_STORE_STACK({pos}, {var});'.format(pos=pos, var=var)

    def static_depth(self):
        '''
        Return a C expression for the number of stack words occupied by the
        static items in a StackPicture.
        '''
        return '{}'.format(len(self.named_items))

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
        return '\n'.join(['{} {};'.format('smite_WORD', item)
                          for item in self.named_items])

    def load(self):
        '''
        Returns C source code to read the named items from the stack into C
        variables.
        `S->STACK_DEPTH` is not modified.
        '''
        return '\n'.join([self.load_var(pos, item)
                          for pos, item in enumerate(reversed(self.named_items))
        ])

    def store(self):
        '''
        Returns C source code to write the named items from C variables into
        the stack.
        `S->STACK_DEPTH` must be modified first.
        '''
        return '\n'.join([self.store_var(pos, item)
                          for pos, item in enumerate(reversed(self.named_items))
        ])


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

def check_underflow(num_pops):
    '''
    Returns C source code to check that the stack contains enough items to
    pop the specified number of items.
     - num_pops - a C expression giving the number of items to pop.
    '''
    return disable_warnings(['-Wtype-limits', '-Wunused-variable', '-Wshadow'], '''\
if ((S->STACK_DEPTH < {num_pops})) {{
    S->BAD = {num_pops} - 1;
    RAISE(3);
}}'''.format(num_pops=num_pops))

def check_overflow(num_pops, num_pushes):
    '''
    Returns C source code to check that the stack contains enough space to
    push `num_pushes` items, given that `num_pops` items will first be
    popped.
    '''
    return disable_warnings(['-Wtype-limits', '-Wtautological-compare'], '''\
if ({num_pushes} > {num_pops} && (S->STACK_SIZE - S->STACK_DEPTH < {num_pushes} - {num_pops})) {{
    S->BAD = ({num_pushes} - {num_pops}) - (S->STACK_SIZE - S->STACK_DEPTH);
    RAISE(2);
}}'''.format(num_pops=num_pops, num_pushes=num_pushes))

def gen_case(action):
    '''
    Generate the code for an Action. In the code, S is the smite_state. Errors
    are reported by calling RAISE().

     - action - Action.
    '''
    # Concatenate the pieces.
    args = action.args
    results = action.results
    static_args = args.static_depth()
    dynamic_args = args.dynamic_depth()
    static_results = results.static_depth()
    dynamic_results = results.dynamic_depth()
    code = '\n'.join([
        args.declare_vars(),
        results.declare_vars(),
        check_underflow(static_args),
        args.load(),
        check_underflow(dynamic_args),
        check_overflow(dynamic_args, dynamic_results),
        'S->STACK_DEPTH -= {};'.format(static_args),
        textwrap.dedent(action.code.rstrip()),
        'S->STACK_DEPTH += {};'.format(static_args),
        'S->STACK_DEPTH -= {};'.format(dynamic_args),
        'S->STACK_DEPTH += {};'.format(dynamic_results),
        results.store(),
    ])
    # Remove newlines resulting from empty strings in the above.
    code = re.sub('\n+', '\n', code, flags=re.MULTILINE).strip('\n')
    return code

def dispatch(actions, prefix, undefined_case):
    '''Generate dispatch code for some Actions.

    actions - Enum of Actions.
    '''
    output = '    switch (I) {\n'
    for action in actions:
        output += '''\
    case {prefix}{instruction}:
        {{
{code}
        }}
        break;\n'''.format(
            instruction=action.name,
            prefix=prefix,
            code=textwrap.indent(gen_case(action.value), '            '))
    output += '''
    default:
{}
        break;
    }}'''.format(undefined_case)
    return output
