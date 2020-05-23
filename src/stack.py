'''
Model and generate code for the VM stack.

Copyright (c) 2009-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import re
from functools import total_ordering

from code_util import Code, unrestrict, disable_warnings


# Enough for the core
# FIXME: Should be able to assume pointers fit in a word
type_wordses = {'mit_word_t': 1, 'mit_uword_t': 1, 'mit_word_t *': 1, 'mit_fn *': 1, 'char **':1}

# Set to 0 to allow type_words to work without types information
TYPE_SIZE_UNKNOWN = None
def type_words(type):
    '''
    Return the number of words occupied by 'type', or `TYPE_SIZE_UNKNOWN` if
    unknown: `TYPE_SIZE_UNKNOWN` can be set to a number to allow the
    generation of (incorrect!) code before the type sizes are known.
    '''
    type = unrestrict(type)
    ret = type_wordses.get(type, TYPE_SIZE_UNKNOWN)
    if ret is None:
        import sys
        print(f'type {type} not found; type_words: "{type_wordses}"', file=sys.stderr)
    return ret

def load_stack(name, depth=0, type='mit_word_t'):
    '''
    Generate C code to load the variable `name` of type `type` occupying
    stack slots `depth`, `depth+1`, ... . Does not check the stack.

    Returns a Code.
    '''
    code = Code()
    code.append(
        f'mit_max_stack_item_t temp = (mit_uword_t)(*mit_stack_pos(stack, stack_depth, {depth}));'
    )
    for i in range(1, type_words(type)):
        code.append('temp <<= MIT_WORD_BIT;')
        code.append(
            f'temp |= (mit_uword_t)(*mit_stack_pos(stack, stack_depth, {depth + i}));'
        )
    code.extend(disable_warnings(
        ['-Wint-to-pointer-cast'],
        Code(f'{name} = ({type})temp;'),
    ))
    return Code('{', code, '}')

def store_stack(value, depth=0, type='mit_word_t'):
    '''
    Generate C code to store the value `value` of type `type` occupying
    stack slots `depth`, `depth+1`, ... . Does not check the stack.

    Returns a Code.
    '''
    code = Code()
    code.extend(disable_warnings(
        ['-Wpointer-to-int-cast', '-Wbad-function-cast'],
        Code(f'mit_max_stack_item_t temp = (mit_max_stack_item_t){value};'),
    ))
    for i in reversed(range(1, type_words(type))):
        code.append(
            f'*mit_stack_pos(stack, stack_depth, {depth + i}) = (mit_uword_t)(temp & MIT_UWORD_MAX);'
        )
        code.append('temp >>= MIT_WORD_BIT;')
    code.append(
        '*mit_stack_pos(stack, stack_depth, {}) = (mit_uword_t)({});'
        .format(
            depth,
            'temp & MIT_UWORD_MAX' if type_words(type) > 1 else 'temp',
        )
    )
    return Code('{', code, '}')

def pop_stack(name, type='mit_word_t'):
    code = Code()
    code.extend(check_underflow(Size(type_words(type))))
    code.extend(load_stack(name, type=type))
    code.append(f'stack_depth -= {type_words(type)};')
    return code

def push_stack(value, type='mit_word_t'):
    code = Code()
    code.extend(check_overflow(Size(0), Size(type_words(type))))
    code.extend(store_stack(value, depth=-type_words(type), type=type))
    code.append(f'stack_depth += {type_words(type)};')
    return code


@total_ordering
class Size:
    '''
    Represents the size of some stack items.

     - size - int.
     - count - int - ±1 to indicate that there are variadic 'ITEMS',
       otherwise 0.
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
        raise TypeError(f'cannot convert {type(value)} to Size')

    def __int__(self):
        if self.count != 0:
            raise ValueError(f'{self} cannot be represented as an integer')
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
        '''
        The returned string is a C expression.
        '''
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
        return self + (-value)

    def __rsub__(self, value):
        return Size.of(value) - self


class StackItem:
    '''
    Represents a stack item, which may occupy more than one word.

    Public fields:

     - name - str
     - type - str - C type of the item (ignore if `name` is 'ITEMS').
     - size - Size, or `None` if unknown - the number of words occupied by
       the item.
     - depth - if this StackItem is part of a StackPicture, the total size of
       the StackItems above this one, otherwise `None`.
    '''
    def __init__(self, name, type):
        self.name = name
        self.type = type
        if self.name == 'ITEMS':
            self.size = Size(0, count=1)
        else:
            self.size = Size(type_words(self.type))
        self.depth = None

    @staticmethod
    def of(name_type):
        '''
        `name_type` has the syntax `NAME[:TYPE]`, where `NAME` is a C
        identifier and `TYPE` a C type (defaulting to `mit_word_t`).
        '''
        m = re.match('([^:=]+)(?::([^:]+))?$', name_type)
        return StackItem(
            m.group(1),
            m.group(2) or 'mit_word_t',
        )

    def __eq__(self, item):
        return (self.name == item.name and
                self.type == item.type and
                self.size == item.size)

    def __repr__(self):
        return f"{self.name}:{self.type}"

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

    The `depth` field of each item is set (see StackItem).

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

    def __str__(self):
        return ' '.join(i.name for i in self.items)

    def __repr__(self):
        return f'StackPicture.of(\'{str(self)}\')'

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
    the number of words in 'ITEMS'. If 'ITEMS' appears in `results`, it must
    be at the same position relative to the bottom of the stack as in
    `args`.

    Public fields:

     - args - StackPicture
     - results - StackPicture
     - by_name - {str: StackItem} - the StackItems in `args` and `results`
       indexed by `name`. If the same name occurs in both `args` and `results`,
       the result is used.
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
            result_pos = results.size - results.by_name['ITEMS'].depth
            assert arg_pos == result_pos
        # Check that `results` is type-compatible with `args`.
        for item in results.items:
            if item.name in args.by_name:
                assert item == args.by_name[item.name]
        self.args = args
        self.results = results
        self.by_name = {i.name: i for i in args.items + results.items}

    def __str__(self):
        return f'{self.args} -- {self.results}'

    def __repr__(self):
        return f'StackEffect.of(\'{self.args}\', \'{self.results}\')'

    @staticmethod
    def of(args, results):
        '''
         - args - list acceptable to `StackPicture.of()`.
         - results - list acceptable to `StackPicture.of()`.
        '''
        return StackEffect(StackPicture.of(args), StackPicture.of(results))

    def declare_vars(self):
        '''
        Returns a Code to declare C variables for arguments and results other
        than 'ITEMS'.
        '''
        return Code(*[
            f'{item.type} {item.name};'
            for item in self.by_name.values()
            if item.name != 'ITEMS'
        ])

    def load_args(self):
        '''
        Returns a Code to read the arguments from the stack into C
        variables, skipping 'ITEMS' and 'COUNT'.

        `stack_depth` is not modified.
        '''
        code = Code()
        for item in self.args.items:
            if item.name != 'ITEMS' and item.name != 'COUNT':
                code.extend(item.load())
        return code

    def store_results(self):
        '''
        Returns a Code to write the results from C variables into the stack,
        skipping 'ITEMS'.

        `stack_depth` must be modified first.
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
     - num_pops - Size, with non-negative `count`.
    '''
    assert isinstance(num_pops, Size)
    assert num_pops >= 0, num_pops
    if num_pops == 0: return Code()
    tests = []
    tests.append(f'unlikely(stack_depth < (mit_uword_t)({num_pops.size}))')
    if num_pops.count == 1:
        tests.append(
            f'unlikely(stack_depth - (mit_uword_t)({num_pops.size}) < (mit_uword_t)(COUNT))'
        )
    return Code(
        'if ({}) {{'.format(' || '.join(tests)),
        Code('RAISE(MIT_ERROR_INVALID_STACK_READ);'),
        '}',
    )

def check_overflow(num_pops, num_pushes):
    '''
    Returns a Code to check that the stack contains enough space to
    push `num_pushes` items, given that `num_pops` items will first be
    popped successfully.
     - num_pops - Size.
     - num_pushes - Size.
    `num_pops` and `num_pushes` must both be variadic or both not.
    '''
    assert isinstance(num_pops, Size)
    assert isinstance(num_pushes, Size)
    assert num_pops >= 0
    assert num_pushes >= 0
    depth_change = num_pushes - num_pops
    if depth_change <= 0: return Code()
    # Ensure comparison will not overflow
    assert depth_change.count == 0
    return Code(f'''\
        if (unlikely(stack_words - stack_depth < {depth_change}))
            RAISE(MIT_ERROR_STACK_OVERFLOW);'''
    )
