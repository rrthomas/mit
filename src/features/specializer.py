'''
Generate code for instructions.

Copyright (c) 2009-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

The main entry point is dispatch().
'''

import re, textwrap

from mit_core.type_sizes import type_sizes
from mit_core.instruction_gen import (
    Size, StackItem, StackPicture, StackEffect)


class CacheState:
    '''
    As an optimization, StackItems that have recently been pushed are cached
    in C variables, as they are likely to be popped soon.
    This class represents the current cacheing situation.

    Caching items does not affect `S->STACK_DEPTH`.
    If `item.depth < self.depth`, then `item` is cached in variable
    `self.var(item.depth)`.

    Public fields:
     - depth - the number of items that are cached. Usually we ensure that a
       C variable `cached_depth` equals `self.depth`. Usually it is a
       compile-time constant.
    '''
    def __init__(self, depth):
        self.depth = depth

    def check_underflow(self, num_pops):
        '''
        Returns C source code to check that the stack contains enough items to
        pop the specified number of items.
         - num_pops - Size
        '''
        if num_pops <= self.depth: return ''
        return '''\
if ((S->STACK_DEPTH < (mit_UWORD)({num_pops}))) {{
    S->BAD = {num_pops} - 1;
    RAISE(MIT_ERR_STACK_READ);
}}'''.format(num_pops=num_pops)

    def check_overflow(self, num_pops, num_pushes):
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

    def load(self, item):
        '''
        Returns C source code to load `item` into the C variable `item.name`.

         - item - StackItem.
        '''
        if item.depth < self.depth:
            # The item is cached.
            assert item.size == 1
            return '{var} = {cache_var};'.format(
                var=item.name,
                cache_var=self.var(item.depth),
            )
        else:
            # Get it from memory.
            return item.load()

    def store(self, item):
        '''
        Returns C source code to store `item` from the C variable `item.name`.

         - item - StackItem.
        '''
        if item.depth < self.depth:
            # The item is cached.
            assert item.size == 1
            return '{cache_var} = {var};'.format(
                var=item.name,
                cache_var=self.var(item.depth),
            )
        else:
            # Put it in memory.
            return item.store()

    def load_args(self, args):
        '''
        Returns C source code to read the arguments from the stack into C
        variables. `S->STACK_DEPTH` is not modified.

         - args - StackPicture.
        '''
        return '\n'.join([
            self.load(item)
            for item in args.items
            if item.name != 'ITEMS' and item.name != 'COUNT'
        ])

    def store_results(self, results):
        '''
        Returns C source code to write the results from C variables into the
        stack. `S->STACK_DEPTH` must be modified first.

         - results - StackPicture.
        '''
        return '\n'.join([
            self.store(item)
            for item in results.items
            if item.name != 'ITEMS'
        ])

    def add(self, depth_change):
        '''
        Returns C source code to update the variable `cached_depth` to reflect
        a change in the stack depth.

         - depth_change - int (N.B. not Size)
        '''
        assert type(depth_change) is int
        if depth_change == 0: return ''
        self.depth += depth_change
        if self.depth < 0: self.depth = 0
        return 'cached_depth = {};'.format(self.depth)

    @staticmethod
    def var_for_depth(pos, depth):
        assert 0 <= pos < depth
        return 'stack_{}'.format(depth - 1 - pos)

    def var(self, pos):
        '''
        Calculate the name of the stack cache variable for position pos.
        This is chosen so that `pop()` and `push()` do not require moving
        values between variables.
        '''
        return self.var_for_depth(pos, self.depth)

    def flush(self, depth_limit=0):
        '''
        Decrease the number of stack items that are cached in C variables,
        if necessary. Returns C source code to move values between variables
        and to memory. Also updates the C variable `cached_depth`.
        '''
        if self.depth <= depth_limit: return ''
        code = []
        for pos in reversed(range(depth_limit, self.depth)):
            code.append('*UNCHECKED_STACK({pos}) = {var};'.format(
                pos=pos,
                var=self.var(pos),
            ))
        for pos in reversed(range(depth_limit)):
            code.append('{} = {};'.format(
                self.var_for_depth(pos, depth_limit),
                self.var(pos),
            ))
        self.depth = depth_limit
        code.append('cached_depth = {};'.format(self.depth))
        return '\n'.join(code)


def cache_limit(picture):
    '''
    Computes the depth of the shallowest uncacheable item, or `None` if
    unknown. An item is cacheable if its size is exactly 1.

     - picture - StackPicture.
    '''
    for i, item in enumerate(reversed(picture.items)):
        if item.size != 1:
            return i
    return None

def gen_case(instruction, cache_state, exit_depth):
    '''
    Generate the code for an Instruction.

    In the code, S is the mit_state, and errors are reported by calling
    RAISE(). When calling RAISE(), the C variable `cached_depth` will contain
    the number of stack items cached in C locals.

     - instruction - Instruction.
     - cache_state - CacheState - Which StackItems are cached.
       Updated in place.
     - exit_depth - int - the `cached_depth` desired on exit.
    '''
    assert instruction.args is not None and instruction.results is not None
    effect = StackEffect(
        StackPicture.of(instruction.args),
        StackPicture.of(instruction.results),
    )
    code = []
    # Flush cached items, if necessary.
    args_limit = cache_limit(effect.args)
    if args_limit is not None:
        code.append(cache_state.flush(args_limit))
    # Load the arguments into C variables.
    code.append(effect.declare_vars())
    count = effect.args.by_name.get('COUNT')
    if count is not None:
        # If we have COUNT, check its stack position is valid, and load it
        code.extend([
            cache_state.check_underflow(count.depth + count.size),
            cache_state.load(count),
        ])
    code.extend([
        cache_state.check_underflow(effect.args.size),
        cache_state.check_overflow(effect.args.size, effect.results.size),
        cache_state.load_args(effect.args),
        'S->STACK_DEPTH -= {};'.format(effect.args.size),
    ])
    # Adjust cache_state.
    if args_limit is None:
        code.append(cache_state.add(-int(effect.args.size)))
    else:
        code.append(cache_state.add(-args_limit))
        assert cache_state.depth == 0
    # Inline `instruction.code`.
    # Note: `S->STACK_DEPTH` and `cached_depth` must be correct for RAISE().
    code.append(textwrap.dedent(instruction.code.rstrip()))
    # Adjust cache_state.
    results_limit = cache_limit(effect.args)
    if results_limit is None:
        num_pushes = int(effect.results.size)
        code.append(cache_state.flush(max(0, exit_depth - num_pushes)))
        code.append(cache_state.add(exit_depth - cache_state.depth))
    else:
        code.append(cache_state.flush())
        assert exit_depth <= results_limit
        code.append(cache_state.add(exit_depth))
    # Store the results from C variables.
    code.extend([
        'S->STACK_DEPTH += {};'.format(effect.results.size),
        cache_state.store_results(effect.results),
    ])
    assert cache_state.depth == exit_depth
    # Remove newlines resulting from empty strings in the above.
    return re.sub('\n+', '\n', '\n'.join(code), flags=re.MULTILINE).strip('\n')
