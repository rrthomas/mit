'''
Generate code for instructions.

Copyright (c) 2009-2019 SMite authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

The main entry point is dispatch().
'''

import functools
import re
import textwrap

try:
    from .type_sizes import type_sizes
except ImportError:
    type_sizes = None # We can't generate code


def print_enum(instructions, prefix):
    '''Utility function to print an instruction enum.'''
    print('\nenum {')
    for instruction in instructions:
        print("    INSTRUCTION({}{}, {:#x})".format(
            prefix,
            instruction.name,
            instruction.value.opcode,
        ))
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

@functools.total_ordering
class Size:
    '''
    Represents the size of some stack items.

     - size - int or Size.
     - count - int - ±1 if the size includes variadic 'ITEMS'
    '''
    def __init__(self, size, count=0):
        assert type(size) is int
        assert type(count) is int
        self.size = size
        if not(-1 <= count <= 1):
            raise ValueError
        self.count = count

    @staticmethod
    def of(value):
        '''Convert `value` to a Size or raise NotImplemented.'''
        if isinstance(value, Size):
            return value
        if type(value) is int:
            return Size(value)
        raise TypeError('cannot convert {} to Size'.format(type(value)))

    def __int__(self):
        if self.count != 0:
            raise ValueError('{} cannot be represented as an integer'.format(
                self))
        return self.size

    def __index__(self):
        return self.__int__()

    def __hash__(self):
        if self.count == 0:
            # In this case we must match `int.__hash__()`.
            return hash(self.size)
        return hash((self.size, self.count))

    def __eq__(self, value):
        value = Size.of(value)
        return self.size == value.size and self.count == value.count

    def __le__(self, value):
        value = Size.of(value)
        return self.size <= value.size and self.count <= value.count

    def __str__(self):
        if self.count == 0: s = '{}'
        elif self.count == 1: s = '{} + COUNT'
        elif self.count == -1: s = '{} - COUNT'
        else: assert False
        return s.format(self.size)

    def __neg__(self):
        return Size(-self.size, count=-self.count)

    def __add__(self, value):
        value = Size.of(value)
        return Size(self.size + value.size, count=self.count + value.count)

    def __radd__(self, value):
        return Size.of(value) + self

    def __sub__(self, value):
        value = Size.of(value)
        return self + (-value)

    def __rsub__(self, value):
        return Size.of(value) - self


class StackItem:
    '''
    Represents a stack item, which may occupy more than one word.

    Public fields:

     - name - str
     - type - str - C type of the item (ignore if `name` is 'ITEMS').
     - size - Size, or `None` if unknown - The number of words occupied by
       the item.
     - depth - If this StackItem is part of a StackEffect, the total size of
       the StackItems above this one, otherwise `None`.
    '''
    def __init__(self, name, type_):
        self.name = name
        self.type = type_
        if self.name == 'ITEMS':
            self.size = Size(0, count=1)
        else:
            if type_sizes is None:
                self.size = None
            else:
                self.size = Size((type_sizes[self.type] +
                                  (type_sizes['smite_WORD'] - 1)) //
                                 type_sizes['smite_WORD'])
        self.depth = None

    @staticmethod
    def of(name_and_type):
        '''
        The name is optionally followed by ":TYPE" to give the C type of the
        underlying quantity; the default is smite_WORD.
        '''
        l = name_and_type.split(":")
        return StackItem(
            l[0],
            l[1] if len(l) > 1 else 'smite_WORD',
        )

    def __eq__(self, item):
        return (self.name == item.name and
                self.type == item.type and
                self.size == item.size)

    def __hash__(self):
        return hash((self.name, self.type, self.size))

    # In `load()` & `store()`, casts to size_t avoid warnings when `type` is
    # a pointer and sizeof(void *) > WORD_BYTES, but the effect is identical.
    def load(self):
        '''
        Returns C source code to load `self` from the stack to its C variable.
        '''
        code = [
            'size_t temp = (smite_UWORD)(*UNCHECKED_STACK({}));'
            .format(self.depth + (self.size - 1))
        ]
        for i in reversed(range(self.size - 1)):
            code.append('temp <<= smite_WORD_BIT;')
            code.append(
                'temp |= (smite_UWORD)(*UNCHECKED_STACK({}));'
                .format(self.depth + i)
            )
        code.append('{} = ({})temp;'.format(self.name, self.type))
        return '''\
{{
{}
}}'''.format(textwrap.indent('\n'.join(code), '    '))

    def store(self):
        '''
        Returns C source code to store `self` to the stack from its C variable.
        '''
        code = ['size_t temp = (size_t){};'.format(self.name)]
        for i in range(self.size - 1):
            code.append(
                '*UNCHECKED_STACK({}) = (smite_UWORD)(temp & smite_WORD_MASK);'
                .format(self.depth + i)
            )
            code.append('temp >>= smite_WORD_BIT;')
        code.append(
            '*UNCHECKED_STACK({}) = (smite_UWORD)(temp & smite_WORD_MASK);'
            .format(self.depth + (self.size - 1))
        )
        return '''\
{{
{}
}}'''.format(textwrap.indent('\n'.join(code), '    '))


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

    'args' and 'results' are augmented with an extra field 'depth' (a Size),
    which gives the stack position of their top-most word.

    Public fields:

     - items - a dict of str: StackItem
     - args - list of StackItem
     - results - list of StackItem
     - args_size - total size of `args`.
     - results_size - total size of `results`.
    '''
    def __init__(self, args_str, results_str):
        '''
         - args_str, results_str - list of str

        Items with the same name are the same item, so their type must be
        the same.
        '''
        if 'ITEMS:' in args_str and 'ITEMS:' in results_str:
            # FIXME: Assert the stack address is the same, not the index.
            assert args_str.index('ITEMS:') == results_str.index('ITEMS:')
        self.args = [StackItem.of(arg_str) for arg_str in args_str]
        self.results = [StackItem.of(result_str) for result_str in results_str]
        self.items = {}
        for item in self.args + self.results:
            if item.name not in self.items:
                self.items[item.name] = item
            else: # Check repeated item is consistent
                assert item == self.items[item.name]
        if type_sizes is not None:
            self.args_size = self._set_depths(self.args)
            self.results_size = self._set_depths(self.results)

    @staticmethod
    def _set_depths(items):
        depth = Size(0)
        for item in reversed(items):
            item.depth = depth
            if item.name == 'ITEMS':
                item.size = Size(0, count=1)
            depth += item.size
        return depth

    def declare_vars(self):
        '''
        Returns C variable declarations for arguments and results other than
        'ITEMS'.
        '''
        return '\n'.join(['{} {};'.format(item.type, item.name)
                          for item in set(self.args + self.results)
                          if item.name != 'ITEMS'])

    def load_args(self):
        '''
        Returns C source code to read the arguments from the stack into C
        variables. `S->STACK_DEPTH` is not modified.
        '''
        return '\n'.join([item.load()
                          for item in self.args
                          if item.name != 'ITEMS' and item.name != 'COUNT'])

    def store_results(self):
        '''
        Returns C source code to write the results from C variables into the
        stack. `S->STACK_DEPTH` must be modified first.
        '''
        return '\n'.join([item.store()
                          for item in self.results if item.name != 'ITEMS'])


def check_underflow(num_pops):
    '''
    Returns C source code to check that the stack contains enough items to
    pop the specified number of items.
     - num_pops - a C expression giving the number of items to pop.
    '''
    if not num_pops <= 0:
        return '''\
if ((S->STACK_DEPTH < (smite_UWORD)({num_pops}))) {{
    S->BAD = {num_pops} - 1;
    RAISE(SMITE_ERR_STACK_READ);
}}'''.format(num_pops=num_pops)
    else:
        return ''

def check_overflow(num_pops, num_pushes):
    '''
    Returns C source code to check that the stack contains enough space to
    push `num_pushes` items, given that `num_pops` items will first be
    popped.
    '''
    depth_change = num_pushes - num_pops
    if not depth_change <= 0:
        return '''\
if (((S->stack_size - S->STACK_DEPTH) < (smite_UWORD)({depth_change}))) {{
    S->BAD = ({depth_change}) - (S->stack_size - S->STACK_DEPTH);
    RAISE(SMITE_ERR_STACK_OVERFLOW);
}}'''.format(depth_change=depth_change)
    else:
        return ''

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
                check_underflow(
                    effect.items['COUNT'].depth +
                    effect.items['COUNT'].size
                ),
                effect.items['COUNT'].load(),
            ]
        code += [
            check_underflow(effect.args_size),
            check_overflow(effect.args_size, effect.results_size),
            effect.load_args(),
        ]
    code += [textwrap.dedent(instruction.code.rstrip())]
    if effect is not None:
        code += [
            'S->STACK_DEPTH += {};'.format(
                effect.results_size - effect.args_size),
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
