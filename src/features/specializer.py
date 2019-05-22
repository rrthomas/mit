'''
Generate code for the specialized interpreter.

Copyright (c) 2018-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from mit_core.code_buffer import Code
from mit_core.instruction_gen import Size, StackItem, StackPicture, StackEffect


class CacheState:
    '''
    As an optimization, StackItems that have recently been pushed are cached
    in C variables, as they are likely to be popped soon.
    This class represents the current cacheing situation.

    Caching items does not affect `S->STACK_DEPTH`.
    If `item.depth < self.cached_depth`, then `item` is cached in variable
    `self.var(item.depth)`.

    Public fields:
     - cached_depth - the number of items that are cached. Usually we ensure
       that a C variable `cached_depth` equals `self.cached_depth`. Usually
       it is a compile-time constant.
     - checked_depth - the number of items that we know we can push without
       checking for stack overflow.
    '''
    def __init__(self, cached_depth, checked_depth):
        self.cached_depth = cached_depth
        self.checked_depth = checked_depth

    def __repr__(self):
        return 'CacheState({}, {})'.format(
            self.cached_depth,
            self.checked_depth,
        )

    def check_underflow(self, num_pops):
        '''
        Returns a Code to check that the stack contains enough items to
        pop the specified number of items.
         - num_pops - Size
        '''
        if num_pops <= self.cached_depth: return Code()
        return Code(
            'if ((S->STACK_DEPTH < (mit_uword)({num_pops}))) {{',
            Code(
                'S->BAD = {num_pops} - 1;',
                'RAISE(MIT_ERROR_INVALID_STACK_READ);',
            ),
            '}}',
        ).format(num_pops=num_pops)


    def check_overflow(self, num_pops, num_pushes):
        '''
        Returns a Code to check that the stack contains enough space to
        push `num_pushes` items, given that `num_pops` items will first be
        popped. Updates `checked_depth`.
         - num_pops - Size.
         - num_pushes - Size.
        '''
        depth_change = num_pushes - num_pops
        if depth_change <= self.checked_depth: return Code()
        return Code(
            'if (((S->stack_size - S->STACK_DEPTH) < (mit_uword)({depth_change}))) {{',
            Code(
                'S->BAD = ({depth_change}) - (S->stack_size - S->STACK_DEPTH);',
                'RAISE(MIT_ERROR_STACK_OVERFLOW);',
            ),
            '}}',
        ).format(depth_change=depth_change)

    def load(self, item):
        '''
        Returns a Code to load `item` into the C variable `item.name`.

         - item - StackItem.
        '''
        assert item.size == 1
        return Code('{var} = {loc};').format(
            var=item.name,
            loc=self.lvalue(item.depth),
        )

    def store(self, item):
        '''
        Returns a Code to store `item` from the C variable `item.name`.

         - item - StackItem.
        '''
        assert item.size == 1
        return Code('{loc} = {var};').format(
            var=item.name,
            loc=self.lvalue(item.depth),
        )

    def load_args(self, args):
        '''
        Returns a Code to read the arguments from the stack into C
        variables. `S->STACK_DEPTH` is not modified.

         - args - StackPicture.
        '''
        code = Code()
        for item in args.items:
            if item.name != 'ITEMS' and item.name != 'COUNT':
                code.extend(self.load(item))
        return code

    def store_results(self, results):
        '''
        Returns a Code to write the results from C variables into the
        stack. `S->STACK_DEPTH` must be modified first.

         - results - StackPicture.
        '''
        code = Code()
        for item in results.items:
            if item.name != 'ITEMS':
                code.extend(self.store(item))
        return code

    def add(self, depth_change):
        '''
        Returns a Code to update the variable `cached_depth` to reflect
        a change in the stack depth, e.g. by pushing or popping some items.
        Also updates `self`.

         - depth_change - int (N.B. not Size)
        '''
        assert type(depth_change) is int
        if depth_change == 0: return Code()
        self.cached_depth += depth_change
        if self.cached_depth < 0: self.cached_depth = 0
        self.checked_depth -= depth_change
        if self.checked_depth < 0: self.checked_depth = 0
        return Code('cached_depth = {};').format(self.cached_depth)

    @staticmethod
    def var_for_depth(pos, cached_depth):
        assert 0 <= pos < cached_depth
        return 'stack_{}'.format(cached_depth - 1 - pos)

    def var(self, pos):
        '''
        Calculate the name of the stack cache variable for position pos.
        This is chosen so that `pop()` and `push()` do not require moving
        values between variables.
        '''
        return self.var_for_depth(pos, self.cached_depth)

    def lvalue(self, pos):
        '''
        Returns a C L-value representing the current location of stack
        position `pos`, whether or not it is cached.
        '''
        if pos < self.cached_depth:
            # The item is cached.
            return self.var(pos)
        else:
            # The item is really on the stack.
            return '*UNCHECKED_STACK({})'.format(pos)

    def flush(self, goal=0):
        '''
        Decrease the number of stack items that are cached in C variables,
        if necessary. Returns a Code to move values between variables
        and to memory. Also updates the C variable `cached_depth`.

         - goal - a CacheState to match, or an int to specify a desired
           `cache_depth`. Default is `0`.
        '''
        if type(goal) is int:
            goal = CacheState(goal, self.checked_depth)
        assert goal.cached_depth <= self.cached_depth, (goal, self)
        assert goal.checked_depth <= self.checked_depth, (goal, self)
        self.checked_depth = goal.checked_depth
        if goal.cached_depth == self.cached_depth: return Code()
        code = Code()
        for pos in reversed(range(self.cached_depth)):
            code.append('{} = {};'.format(goal.lvalue(pos), self.lvalue(pos)))
        self.cached_depth = goal.cached_depth
        code.append('cached_depth = {};'.format(self.cached_depth))
        return code


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

def gen_case(instruction, cache_state):
    '''
    Generate a Code for an Instruction.

    In the code, S is the mit_state, and errors are reported by calling
    RAISE(). When calling RAISE(), the C variable `cached_depth` will contain
    the number of stack items cached in C locals.

     - instruction - Instruction.
     - cache_state - CacheState - Which StackItems are cached.
       Updated in place.
    '''
    assert instruction.args is not None and instruction.results is not None
    effect = StackEffect(
        StackPicture.of(instruction.args),
        StackPicture.of(instruction.results),
    )
    code = Code()
    # Flush cached items, if necessary.
    args_limit = cache_limit(effect.args)
    if args_limit is not None and args_limit < cache_state.cached_depth:
        code.extend(cache_state.flush(args_limit))
    # Load the arguments into C variables.
    code.extend(effect.declare_vars())
    count = effect.args.by_name.get('COUNT')
    if count is not None:
        # If we have COUNT, check its stack position is valid, and load it
        code.extend(cache_state.check_underflow(count.depth + count.size))
        code.extend(cache_state.load(count))
    code.extend(cache_state.check_underflow(effect.args.size))
    code.extend(
        cache_state.check_overflow(effect.args.size, effect.results.size),
    )
    code.extend(cache_state.load_args(effect.args))
    code.append('S->STACK_DEPTH -= {};'.format(effect.args.size))
    # Adjust cache_state.
    if args_limit is None:
        code.extend(cache_state.add(-int(effect.args.size)))
    else:
        code.extend(cache_state.add(-args_limit))
        assert cache_state.cached_depth == 0
    # Inline `instruction.code`.
    # Note: `S->STACK_DEPTH` and `cached_depth` must be correct for RAISE().
    code.append(instruction.code)
    # Adjust cache_state.
    results_limit = cache_limit(effect.results)
    if results_limit is None:
        code.extend(cache_state.add(int(effect.results.size)))
    else:
        code.extend(cache_state.flush())
        code.extend(cache_state.add(results_limit))
    # Store the results from C variables.
    code.append('S->STACK_DEPTH += {};'.format(effect.results.size))
    code.extend(cache_state.store_results(effect.results))
    return code
