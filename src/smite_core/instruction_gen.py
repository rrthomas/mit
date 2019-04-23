'''
Generate code for instructions.

Copyright (c) 2009-2019 SMite authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

The main entry point is dispatch().
'''

import re
import textwrap

try:
    from .type_sizes import type_sizes
except ImportError:
    type_sizes = None # We can't generate code


def print_enum(instructions, prefix):
    '''Utility function to print an instruction enum.'''
    print('\nenum {')
    for (name, instruction) in instructions.__members__.items():
        print("    INSTRUCTION({}{}, {:#x})".format(prefix, name, instruction.value.opcode))
    print('};')

class Instruction:
    '''
    VM instruction instruction descriptor.

     - opcode - int - opcode number
     - effect - StackEffect (or None for arbitrary stack effect)
     - code - str - C source code

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    The code should RAISE any error before writing any state, so that if an
    error is raised, the state of the VM is not changed.
    '''
    def __init__(self, opcode, args, results, code):
        '''
         - args, results - lists of str acceptable to StackEffect(); if both are
           None, then the instruction has an arbitrary stack effect, like `EXT`.
        '''
        self.opcode = opcode
        if args is None or results is None:
            assert args is None and results is None
            self.effect = None
        else:
            self.effect = StackEffect(args, results)
        self.code = code


class StackItem:
    '''
    Represents a stack item, which may occupy more than one word.

    Public fields:

     - name - str
     - type - str - C type of the item, or None if unknown
     - size - str - C expression for the size of the item
    '''
    def __init__(self, name_and_type):
        '''
        Each name is optionally followed by ":TYPE" to give the C type of the
        underlying quantity; the default is smite_WORD.

        Items of unknown type are indicated by a colon with no type
        following. The `size` field of such StackItems may be set later.
        '''
        l = name_and_type.split(":")
        self.name = l[0]
        self.type = l[1] if len(l) > 1 else 'smite_WORD'
        self.size = None
        if self.type == '':
            self.type = None
        elif type_sizes is not None:
            self.size = ((type_sizes[self.type] +
                          (type_sizes['smite_WORD'] - 1)) //
                         type_sizes['smite_WORD'])

    def __eq__(self, item):
        return (self.name == item.name and
                self.type == item.type and
                self.size == item.size)

class StackEffect:
    '''
    Represents the effect of an instruction on the stack, in the form of
    'args' and 'results' stack pictures, which describe the topmost items on
    the stack.

    If the instruction is variadic, a pseudo-item 'ITEMS' represents the
    unnamed items; one of the arguments above that must be 'COUNT', which is
    the number of words in 'ITEMS'. If 'ITEMS' appears in 'results', it must
    be at the same position relative to the bottom of the stack as in
    'args'.

    'args' and 'results' are augmented with an extra field 'depth' which
    gives the stack position of their top-most word, and is either int or
    str (a C expression).

    Public fields:

     - items - a dict of str: StackItem
     - args - list of StackItem
     - results - list of StackItem
    '''
    def __init__(self, args_str, results_str):
        '''
         - args, results - list of str

        Items with the same name are the same item, so their type must be
        the same.
        '''
        if 'ITEMS:' in args_str and 'ITEMS:' in results_str:
            # FIXME: Assert the depth is the same, not the index.
            assert args_str.index('ITEMS:') == results_str.index('ITEMS:')
        self.args = [StackItem(arg_str) for arg_str in args_str]
        self.results = [StackItem(result_str) for result_str in results_str]
        self.items = {}
        for item in self.args + self.results:
            if item.name not in self.items:
                self.items[item.name] = item
            else: # Check repeated item is consistent
                assert item == self.items[item.name]
        count_index = None
        if 'COUNT' in args_str:
            count_index = args_str.index('COUNT')
        self._set_depths(self.args, count_index)
        self._set_depths(self.results, count_index)

    @staticmethod
    def _set_depths(items, count_index):
        depth = 0
        for item in reversed(items):
            item.depth = depth
            if item.name == 'ITEMS':
                item.size = 'COUNT'
            if type(depth) == int and type(item.size) == int:
                depth += item.size
            else:
                depth = '{} + {}'.format(depth, item.size)

    # In load_item & store_item, casts to size_t avoid warnings when `var` is
    # a pointer and sizeof(void *) > WORD_BYTES, but the effect is identical.
    def load_item(self, item):
        '''Load `item` from the stack to its C variable.'''
        code = ['{} = 0;'.format(item.name)]
        for i in reversed(range(item.size)):
            code.append('temp = *UNCHECKED_STACK({} + {});'.format(item.depth, i))
            if i < item.size - 1:
                code.append('{var} = ({type})((size_t){var} << smite_WORD_BIT);'.format(var=item.name, type=item.type))
            code.append('{var} = ({type})((size_t){var} | (smite_UWORD)temp);'.format(var=item.name, type=item.type))
        return '''\
{{
    smite_WORD temp;
{}
}}'''.format(textwrap.indent('\n'.join(code), '    '))

    def store_item(self, item):
        '''
        Store `item` to the stack from its C variable.
        The variable is corrupted.
        '''
        code = []
        for i in range(item.size):
            code.append('*UNCHECKED_STACK({} + {}) = (smite_UWORD)((size_t){} & smite_WORD_MASK);'.format(item.depth, i, item.name))
            if i < item.size - 1:
                code.append('{var} = ({type})((size_t){var} >> smite_WORD_BIT);'.format(var=item.name, type=item.type))
        return '\n'.join(code)

    def declare_vars(self):
        '''
        Returns C variable declarations for `self.items.values()` other than
        any 'ITEMS'.
        '''
        return '\n'.join(['{} {};'.format(item.type, item.name)
                          for item in self.items.values()
                          if item.name != 'ITEMS'])

    def load_args(self):
        '''
        Returns C source code to read the arguments from the stack into C
        variables. `S->STACK_DEPTH` is not modified.
        '''
        return '\n'.join([self.load_item(item)
                          for item in self.args
                          if item.name != 'ITEMS' and item.name != 'COUNT'])

    def store_results(self):
        '''
        Returns C source code to write the results from C variables into the
        stack. `S->STACK_DEPTH` must be modified first.
        '''
        return '\n'.join([self.store_item(item)
                          for item in self.results if item.name != 'ITEMS'])


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
    return disable_warnings(['-Wtype-limits', '-Wsign-compare'], '''\
if ((S->STACK_DEPTH < {num_pops})) {{
    S->BAD = {num_pops} - 1;
    RAISE(SMITE_ERR_STACK_READ);
}}'''.format(num_pops=num_pops))

def check_overflow(num_pops, num_pushes):
    '''
    Returns C source code to check that the stack contains enough space to
    push `num_pushes` items, given that `num_pops` items will first be
    popped.
    '''
    return disable_warnings(['-Wtype-limits', '-Wtautological-compare', '-Wsign-compare', '-Wstrict-overflow'], '''\
if ({num_pushes} > {num_pops} && (S->stack_size - S->STACK_DEPTH < {num_pushes} - {num_pops})) {{
    S->BAD = ({num_pushes} - {num_pops}) - (S->stack_size - S->STACK_DEPTH);
    RAISE(SMITE_ERR_STACK_OVERFLOW);
}}'''.format(num_pops=num_pops, num_pushes=num_pushes))

def gen_case(instruction):
    '''
    Generate the code for an Instruction.

    In the code, S is the smite_state, and errors are reported by calling
    RAISE().

     - instruction - Instruction.
    '''
    # Concatenate the pieces.
    effect = instruction.effect
    code = []
    if effect is not None:
        code.append(effect.declare_vars())
        if 'COUNT' in effect.items:
            # If we have COUNT, check its stack position is valid, and load it
            code += [
                check_underflow('({} + {})'.format(
                    effect.items['COUNT'].depth,
                    effect.items['COUNT'].size,
                )),
                effect.load_item(effect.items['COUNT']),
            ]
        args_size = ' + '.join(str(item.size) for item in effect.args) or '0'
        results_size = ' + '.join(str(item.size) for item in effect.results) or '0'
        code += [
            check_underflow(args_size),
            check_overflow(args_size, results_size),
            effect.load_args(),
        ]
    code += [textwrap.dedent(instruction.code.rstrip())]
    if effect is not None:
        code += [
            'S->STACK_DEPTH += {} - ({});'.format(results_size, args_size),
            effect.store_results(),
        ]
    # Remove newlines resulting from empty strings in the above.
    return re.sub('\n+', '\n', '\n'.join(code), flags=re.MULTILINE).strip('\n')

def dispatch(instructions, prefix, undefined_case):
    '''Generate dispatch code for some Instructions.

    instructions - Enum of Instructions.
    '''
    output = '    switch (opcode) {\n'
    for instruction in instructions:
        output += '''\
    case {prefix}{instruction}:
        {{
{code}
        }}
        break;\n'''.format(
            instruction=instruction.name,
            prefix=prefix,
            code=textwrap.indent(gen_case(instruction.value), '            '))
    output += '''
    default:
{}
        break;
    }}'''.format(undefined_case)
    return output
