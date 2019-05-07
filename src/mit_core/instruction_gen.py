'''
Generate code for instructions.

Copyright (c) 2009-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

The main entry point is dispatch().
'''

import functools
import re
import textwrap

from .type_sizes import type_sizes


@functools.total_ordering
class Size:
    '''
    Represents the size of some stack items.

     - size - int.
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
     - depth - If this StackItem is part of a StackPicture, the total size of
       the StackItems above this one, otherwise `None`.
    '''
    def __init__(self, name, type_):
        self.name = name
        self.type = type_
        if self.name == 'ITEMS':
            self.size = Size(0, count=1)
        else:
            self.size = Size((type_sizes[self.type] +
                              (type_sizes['mit_WORD'] - 1)) //
                             type_sizes['mit_WORD'])
        self.depth = None

    @staticmethod
    def of(name_and_type):
        '''
        The name is optionally followed by ":TYPE" to give the C type of the
        underlying quantity; the default is mit_WORD.
        '''
        l = name_and_type.split(":")
        return StackItem(
            l[0],
            l[1] if len(l) > 1 else 'mit_WORD',
        )

    def __eq__(self, item):
        return (self.name == item.name and
                self.type == item.type and
                self.size == item.size)

    def __repr__(self):
        return "{}:{}".format(self.name, self.type)

    def __hash__(self):
        return hash((self.name, self.type, self.size))

    # Cf. mit.h PUSH/POP_STACK_TYPE macros.
    def load(self):
        '''
        Returns C source code to load `self` from the stack to its C variable.
        '''
        code = [
            'size_t temp = (mit_UWORD)(*UNCHECKED_STACK({}));'
            .format(self.depth)
        ]
        for i in range(self.size - 1):
            code.append('temp <<= mit_WORD_BIT;')
            code.append(
                'temp |= (mit_UWORD)(*UNCHECKED_STACK({}));'
                .format(self.depth + i + 1)
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
        for i in reversed(range(self.size - 1)):
            code.append(
                '*UNCHECKED_STACK({}) = (mit_UWORD)(temp & mit_WORD_MASK);'
                .format(self.depth + i + 1)
            )
            code.append('temp >>= mit_WORD_BIT;')
        code.append(
            '*UNCHECKED_STACK({}) = (mit_UWORD)(temp & mit_WORD_MASK);'
            .format(self.depth)
        )
        return '''\
{{
{}
}}'''.format(textwrap.indent('\n'.join(code), '    '))


class StackPicture:
    '''
    Represents the top few items on the stack.

    Each of `items` is augmented with an extra field 'depth' (a Size),
    which gives the stack position of its top-most word.

    Public fields:

     - items - [StackItem] - the StackItems, ending with the topmost.
     - by_name - {str: StackItem} - `items` indexed by `name`.
     - size - Size - the total size of `items`, or `None` if unknown.
    '''
    def __init__(self, items):
        self.items = items
        self.by_name = {i.name: i for i in items}
        self.size = Size(0)
        for item in reversed(items):
            item.depth = self.size
            self.size += item.size

    @staticmethod
    def of(strs):
        '''
         - strs - list of str acceptable to `StackItem.of()`.
        '''
        return StackPicture([StackItem.of(s) for s in strs])


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

    Public fields:

     - args - StackPicture
     - results - StackPicture
    '''
    def __init__(self, args, results):
        '''
        Items with the same name are the same item, so their type must be
        the same.
        '''
        # Check that `args` is duplicate-free.
        assert len(args.by_name) == len(args.items)
        # Check that 'ITEMS' does not move.
        if 'ITEMS' in args.by_name and 'ITEMS' in results.by_name:
            arg_pos = args.size - args.by_name['ITEMS'].depth
            result_pos = args.size - args.by_name['ITEMS'].depth
            assert arg_pos == result_pos
        # Check that `results` is type-compatible with `args`.
        for item in results.items:
            if item.name in args.by_name:
                assert item == args.by_name[item.name]
        self.args = args
        self.results = results

    def declare_vars(self):
        '''
        Returns C variable declarations for arguments and results other than
        'ITEMS'.
        '''
        return '\n'.join([
            '{} {};'.format(item.type, item.name)
            for item in set(self.args.items + self.results.items)
            if item.name != 'ITEMS'
        ])

    def load_args(self):
        '''
        Returns C source code to read the arguments from the stack into C
        variables. `S->STACK_DEPTH` is not modified.
        '''
        return '\n'.join([
            item.load()
            for item in self.args.items
            if item.name != 'ITEMS' and item.name != 'COUNT'
        ])

    def store_results(self):
        '''
        Returns C source code to write the results from C variables into the
        stack. `S->STACK_DEPTH` must be modified first.
        '''
        return '\n'.join([
            item.store()
            for item in self.results.items
            if item.name != 'ITEMS'
        ])


def check_underflow(num_pops):
    '''
    Returns C source code to check that the stack contains enough items to
    pop the specified number of items.
     - num_pops - Size
    '''
    if num_pops <= 0: return ''
    return '''\
if ((S->STACK_DEPTH < (mit_UWORD)({num_pops}))) {{
    S->BAD = {num_pops} - 1;
    RAISE(MIT_ERR_STACK_READ);
}}'''.format(num_pops=num_pops)

def check_overflow(num_pops, num_pushes):
    '''
    Returns C source code to check that the stack contains enough space to
    push `num_pushes` items, given that `num_pops` items will first be
    popped.
     - num_pops - Size.
     - num_pushes - Size.
    '''
    depth_change = num_pushes - num_pops
    if depth_change <= 0: return ''
    return '''\
if (((S->stack_size - S->STACK_DEPTH) < (mit_UWORD)({depth_change}))) {{
    S->BAD = ({depth_change}) - (S->stack_size - S->STACK_DEPTH);
    RAISE(MIT_ERR_STACK_OVERFLOW);
}}'''.format(depth_change=depth_change)

def gen_case(instruction):
    '''
    Generate the code for an Instruction.

    In the code, S is the mit_state, and errors are reported by calling
    RAISE().

     - instruction - Instruction.
    '''
    if instruction.args is None and instruction.results is None:
        effect = None
    else:
        effect = StackEffect(
            StackPicture.of(instruction.args),
            StackPicture.of(instruction.results),
        )
    code = []
    if effect is not None:
        # Load the arguments into C variables.
        code.append(effect.declare_vars())
        count = effect.args.by_name.get('COUNT')
        if count is not None:
            # If we have COUNT, check its stack position is valid, and load it
            code.extend([
                check_underflow(count.depth + count.size),
                count.load(),
            ])
        code.extend([
            check_underflow(effect.args.size),
            check_overflow(effect.args.size, effect.results.size),
            effect.load_args(),
        ])
    code.append(textwrap.dedent(instruction.code.rstrip()))
    if effect is not None:
        # Store the results from C variables.
        code.extend([
            'S->STACK_DEPTH += {};'.format(
                effect.results.size - effect.args.size),
            effect.store_results(),
        ])
    # Remove newlines resulting from empty strings in the above.
    return re.sub('\n+', '\n', '\n'.join(code), flags=re.MULTILINE).strip('\n')

def dispatch(instructions, prefix, undefined_case):
    '''
    Generate dispatch code for some Instructions.

    instructions - Enum of Instructions.
    '''
    code = ['    switch (opcode) {']
    for instruction in instructions:
        code.append('''\
    case {prefix}{instruction}:
        {{
{code}
        }}
        break;'''.format(
            instruction=instruction.name,
            prefix=prefix,
            code=textwrap.indent(
                gen_case(instruction),
                '            ',
            ),
        ))
    code.append('''
    default:
{}
        break;
    }}'''.format(undefined_case)
    )
    # Remove newlines resulting from empty strings in the above.
    return re.sub('\n+', '\n', '\n'.join(code), flags=re.MULTILINE).strip('\n')
