'''
Generate code for the specialized interpreter.

Copyright (c) 2018-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from code_util import Code
from stack import Size


# TODO: Unify with path.State?
class CacheState:
    '''
    As an optimization, StackItems that have recently been pushed are cached
    in C variables, as they are likely to be popped soon.
    This class represents the current cacheing situation.

    Caching items does not affect `stack_depth`.
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
        return f'CacheState({self.cached_depth}, {self.checked_depth})'

    def underflow_test(self, num_pops):
        '''
        Returns a C boolean expression (a str) to check that the stack
        contains enough items to pop the specified number of items.
         - num_pops - int
        '''
        assert type(num_pops) is int
        if self.cached_depth >= num_pops: return '1'
        return f'stack_depth >= {num_pops}'

    def overflow_test(self, num_pops, num_pushes):
        '''
        Returns a C boolean expression (a str) to check that the stack
        contains enough space to push `num_pushes` items, given that
        `num_pops` items will first be popped.
         - num_pops - int.
         - num_pushes - int.
        '''
        assert type(num_pops) is int
        assert type(num_pushes) is int
        depth_change = num_pushes - num_pops
        if self.checked_depth >= depth_change: return '1'
        return f'(stack_words - stack_depth) >= {depth_change}'

    def load_args(self, args):
        '''
        Returns a Code to read the arguments from the stack into C
        variables. `stack_depth` is not modified.

         - args - list of str.
        '''
        return Code(*[
            f'{item.name} = {self.lvalue(pos)};'
            for pos, item in enumerate(reversed(args.items))
        ])

    def store_results(self, results):
        '''
        Returns a Code to write the results from C variables into the
        stack. `stack_depth` must be modified first.

         - results - list of str.
        '''
        return Code(*[
            f'{self.lvalue(pos)} = {item.name};'
            for pos, item in enumerate(reversed(results.items))
        ])

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
        return Code(f'cached_depth = {self.cached_depth};')

    def var(self, pos):
        '''
        Calculate the name of the stack cache variable for position pos.
        This is chosen so that `pop()` and `push()` do not require moving
        values between variables.
        '''
        assert 0 <= pos < self.cached_depth
        return f'stack_{self.cached_depth - 1 - pos}'

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
            return f'*mit_stack_pos(stack, stack_depth, {pos})'

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
            code.append(f'{goal.lvalue(pos)} = {self.lvalue(pos)};')
        self.cached_depth = goal.cached_depth
        code.append(f'cached_depth = {self.cached_depth};')
        return code


def gen_case(instruction, cache_state):
    '''
    Generate a Code for a member of Instruction. It is the caller's
    responsibility to ensure that it's the right instruction to execute, and
    that the stack won't underflow or overflow.

    In the code, errors are reported by calling THROW(). When calling
    THROW(), the C variable `cached_depth` will contain the number of stack
    items cached in C locals.

     - instruction - Instructions.
     - cache_state - CacheState - Which StackItems are cached.
       Updated in place.
    '''
    code = Code()
    num_args = len(instruction.action.effect.args.items)
    num_results = len(instruction.action.effect.results.items)
    # Declare C variables for args and results.
    code.extend(Code(*[
        f'mit_word_t {name};'
        for name, item in instruction.action.effect.by_name.items()
    ]))
    # Load the arguments into their C variables.
    code.extend(cache_state.load_args(instruction.action.effect.args))
    # Inline `instruction.action.code`.
    # Note: `stack_depth` and `cache_state` must be correct for THROW().
    code.extend(instruction.action.code)
    # Update stack pointer and cache_state.
    code.append(f'stack_depth -= {num_args};')
    code.extend(cache_state.add(-num_args))
    code.extend(cache_state.add(num_results))
    code.append(f'stack_depth += {num_results};')
    # Store the results from their C variables.
    code.extend(cache_state.store_results(instruction.action.effect.results))
    return code