'''
Generate code for instructions.

Copyright (c) 2009-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

The main entry point is dispatch().
'''

import functools

from .code_buffer import Code
from .opcode_frequency import counts
from .code_util import disable_warnings


type_wordses = {'mit_word': 1} # Enough for the core

def type_words(type):
    '''
    Return the number of words occupied by 'type', or -1 if unknown: this
    can be used in numeric calculations to generate C, but will cause
    compilation errors if it is erroneously compiled.
    '''
    return type_wordses.get(type, -1)

def load_stack(name, depth=0, type='mit_word'):
    '''
    Generate C code to load the variable `name` of type `type` occupying
    stack slots starting at position `depth`. Does not check the stack.

    Returns a Code.
    '''
    code = Code()
    code.append(
        'mit_max_stack_item_t temp = (mit_uword)(*UNCHECKED_STACK(S->stack, S->STACK_DEPTH, {}));'
        .format(depth)
    )
    for i in range(type_words(type) - 1):
        code.append('temp <<= MIT_WORD_BIT;')
        code.append(
            'temp |= (mit_uword)(*UNCHECKED_STACK(S->stack, S->STACK_DEPTH, {}));'
            .format(depth + i + 1)
        )
    code.extend(disable_warnings(
        ['-Wint-to-pointer-cast'],
        Code('{} = ({})temp;').format(name, type)
    ))
    return Code('{', code, '}')

def store_stack(value, depth=0, type='mit_word'):
    '''
    Generate C code to store the value `value` of type `type` occupying
    stack slots starting at position `depth`. Does not check the stack.

    Returns a Code.
    '''
    code = Code()
    code.extend(disable_warnings(
        ['-Wpointer-to-int-cast', '-Wbad-function-cast'],
        Code('mit_max_stack_item_t temp = (mit_max_stack_item_t){};')
            .format(value),
    ))
    for i in reversed(range(type_words(type) - 1)):
        code.append(
            '*UNCHECKED_STACK(S->stack, S->STACK_DEPTH, {}) = (mit_uword)(temp & MIT_WORD_MASK);'
            .format(depth + i + 1)
        )
        code.append('temp >>= MIT_WORD_BIT;')
    code.append(
        '*UNCHECKED_STACK(S->stack, S->STACK_DEPTH, {}) = (mit_uword)({});'
        .format(
            depth,
            'temp & MIT_WORD_MASK' if type_words(type) > 1 else 'temp',
        )
    )
    return Code('{', code, '}')

def pop_stack(name, type='mit_word'):
    code = Code()
    code.extend(check_underflow(type_words(type)))
    code.extend(load_stack(name, type=type))
    code.append(
        'S->STACK_DEPTH -= {};'.format(type_words(type)),
    )
    return code

def push_stack(value, type='mit_word'):
    code = Code()
    code.extend(check_overflow(type_words(type), 0))
    code.extend(store_stack(value, type=type))
    code.append(
        'S->STACK_DEPTH += {};'.format(type_words(type)),
    )
    return code


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
            self.size = Size(type_words(self.type))
        self.depth = None

    @staticmethod
    def of(name_and_type):
        '''
        The name is optionally followed by ":TYPE" to give the C type of the
        underlying quantity; the default is mit_word.
        '''
        l = name_and_type.split(":")
        return StackItem(
            l[0],
            l[1] if len(l) > 1 else 'mit_word',
        )

    def __eq__(self, item):
        return (self.name == item.name and
                self.type == item.type and
                self.size == item.size)

    def __repr__(self):
        return "{}:{}".format(self.name, self.type)

    def __hash__(self):
        return hash((self.name, self.type, self.size))

    def load(self):
        '''
        Returns a Code to load `self` from the stack to its C variable.
        '''
        return load_stack(self.name, self.depth, self.type)

    def store(self):
        '''
        Returns a Code to store `self` to the stack from its C variable.
        '''
        return store_stack(self.name, self.depth, self.type)


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
        Returns a Code to declare C variables for arguments and results other
        than 'ITEMS'.
        '''
        return Code(*[
            '{} {};'.format(item.type, item.name)
            for item in set(self.args.items + self.results.items)
            if item.name != 'ITEMS'
        ])

    def load_args(self):
        '''
        Returns a Code to read the arguments from the stack into C
        variables. `S->STACK_DEPTH` is not modified.
        '''
        code = Code()
        for item in self.args.items:
            if item.name != 'ITEMS' and item.name != 'COUNT':
                code.extend(item.load())
        return code

    def store_results(self):
        '''
        Returns a Code to write the results from C variables into the
        stack. `S->STACK_DEPTH` must be modified first.
        '''
        code = Code()
        for item in self.results.items:
            if item.name != 'ITEMS':
                code.extend(item.store())
        return code


def check_underflow(num_pops):
    '''
    Returns a Code to check that the stack contains enough items to
    pop the specified number of items.
     - num_pops - Size
    '''
    if num_pops <= 0: return Code()
    return Code(
        'if ((S->STACK_DEPTH < (mit_uword)({num_pops}))) {{',
        Code (
            'S->BAD = {num_pops} - 1;',
            'RAISE(MIT_ERROR_INVALID_STACK_READ);',
        ),
        '}}',
    ).format(num_pops=num_pops)

def check_overflow(num_pops, num_pushes):
    '''
    Returns a Code to check that the stack contains enough space to
    push `num_pushes` items, given that `num_pops` items will first be
    popped.
     - num_pops - Size.
     - num_pushes - Size.
    '''
    depth_change = num_pushes - num_pops
    if depth_change <= 0: return Code()
    return Code(
        'if (((S->stack_size - S->STACK_DEPTH) < (mit_uword)({depth_change}))) {{',
        Code(
            'S->BAD = ({depth_change}) - (S->stack_size - S->STACK_DEPTH);',
            'RAISE(MIT_ERROR_STACK_OVERFLOW);',
        ),
        '}}',
    ).format(depth_change=depth_change)

def gen_case(instruction):
    '''
    Generate a Code for an Instruction.

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
    code = Code()
    if instruction.terminal:
        code.append('if (S->I != 0) RAISE(MIT_ERROR_INVALID_OPCODE);')
    if effect is not None:
        # Load the arguments into C variables.
        code.extend(effect.declare_vars())
        count = effect.args.by_name.get('COUNT')
        if count is not None:
            # If we have COUNT, check its stack position is valid, and load it
            code.extend(check_underflow(count.depth + count.size))
            code.extend(count.load())
        code.extend(check_underflow(effect.args.size))
        code.extend(check_overflow(effect.args.size, effect.results.size))
        code.extend(effect.load_args())
    code.extend(instruction.code)
    if effect is not None:
        # Store the results from C variables.
        code.append('S->STACK_DEPTH += {};'.format(
            effect.results.size - effect.args.size
        ))
        code.extend(effect.store_results())
    return code

def dispatch(Instruction, prefix, undefined_case, trace=None):
    '''
    Generate dispatch code for some Instructions.

     - Instruction - InstructionEnum.
     - prefix - instruction name prefix.
     - undefined_case - a Code defining the fallback behaviour.
     - trace - an opcode trace to use to improve the dispatch code.
    '''
    assert isinstance(undefined_case, Code)
    code = Code()
    else_text = ''
    order = enumerate(Instruction)
    if trace is not None:
        order = counts(Instruction, trace)
    for (_, instruction) in order:
        code.append('{else_text}if (opcode == {prefix}{instruction}) {{'.format(
            else_text=else_text,
            instruction=instruction.name,
            prefix=prefix,
        ))
        code.append(gen_case(instruction))
        code.append('}')
        else_text = 'else '
    code.append('else {')
    code.append(undefined_case)
    code.append('}')
    return code
