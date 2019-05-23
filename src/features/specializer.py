'''
Generate code for the specialized interpreter.

Copyright (c) 2018-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from mit_core.code_buffer import Code
from mit_core.vm_data import Instruction
from mit_core.instruction import AbstractInstruction


def _replace_items(picture, replacement):
    '''
    Replaces 'ITEMS' with `replacement` in `picture`
    '''
    ret = []
    for item in picture:
        if item == 'ITEMS':
            ret.extend(replacement)
        else:
            ret.append(item)
    return ret

def _gen_specialized_instruction(instruction, tos_constant):
    replacement = ['x{}'.format(i) for i in range(tos_constant)]
    code = Code()
    code.append('assert(COUNT == {});'.format(tos_constant))
    code.extend(instruction.code)
    return (
        instruction.opcode,
        _replace_items(instruction.args, replacement),
        _replace_items(instruction.results, replacement),
        code,
        instruction.terminal,
    )

SpecializedInstruction = AbstractInstruction('SpecializedInstruction', {
    '{name}_WITH_{tos_constant}'.format(
        name=instruction.name,
        tos_constant=tos_constant,
    ): _gen_specialized_instruction(instruction, tos_constant)
    for instruction in Instruction
    if 'ITEMS' in instruction.args
    for tos_constant in range(4)
})


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

    def underflow_test(self, num_pops):
        '''
        Returns a C boolean expression (a str) to check that the stack
        contains enough items to pop the specified number of items.
         - num_pops - int
        '''
        assert type(num_pops) is int
        if self.cached_depth >= num_pops: return '1'
        return 'S->STACK_DEPTH >= {}'.format(num_pops)

    def overflow_test(self, num_pops, num_pushes):
        '''
        Returns a C boolean expression (a str) to check that the stack
        contains enough space to push `num_pushes` items, given that
        `num_pops` items will first be popped. Updates `checked_depth`.
         - num_pops - int.
         - num_pushes - int.
        '''
        assert type(num_pops) is int
        assert type(num_pushes) is int
        depth_change = num_pushes - num_pops
        if self.checked_depth >= depth_change: return '1'
        self.checked_depth = depth_change
        return '(S->stack_size - S->STACK_DEPTH) >= {}'.format(depth_change)

    def check_underflow(self, num_pops):
        '''
        Returns a Code to check that the stack contains enough items to
        pop the specified number of items.
         - num_pops - int
        '''
        return Code(
            'if (!({test})) {{',
            Code(
                'S->BAD = {num_pops} - 1;',
                'RAISE(MIT_ERROR_INVALID_STACK_READ);',
            ),
            '}}',
        ).format(test=self.underflow_test(num_pops), num_pops=num_pops)

    def check_overflow(self, num_pops, num_pushes):
        '''
        Returns a Code to check that the stack contains enough space to
        push `num_pushes` items, given that `num_pops` items will first be
        popped. Updates `checked_depth`.
         - num_pops - Size.
         - num_pushes - Size.
        '''
        depth_change = num_pushes - num_pops
        return Code(
            'if (!({test})) {{',
            Code(
                'S->BAD = {depth_change} - (S->stack_size - S->STACK_DEPTH);',
                'RAISE(MIT_ERROR_STACK_OVERFLOW);',
            ),
            '}}',
        ).format(
            test=self.overflow_test(num_pops, num_pushes),
            depth_change=depth_change,
        )

    def load_args(self, args):
        '''
        Returns a Code to read the arguments from the stack into C
        variables. `S->STACK_DEPTH` is not modified.

         - args - list of str.
        '''
        return Code(*[
            '{} = {};'.format(name, self.lvalue(pos))
            for pos, name in enumerate(reversed(args))
        ])

    def store_results(self, results):
        '''
        Returns a Code to write the results from C variables into the
        stack. `S->STACK_DEPTH` must be modified first.

         - results - list of str.
        '''
        return Code(*[
            '{} = {};'.format(self.lvalue(pos), name)
            for pos, name in enumerate(reversed(results))
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
        return Code('cached_depth = {};').format(self.cached_depth)

    def var(self, pos):
        '''
        Calculate the name of the stack cache variable for position pos.
        This is chosen so that `pop()` and `push()` do not require moving
        values between variables.
        '''
        assert 0 <= pos < self.cached_depth
        return 'stack_{}'.format(self.cached_depth - 1 - pos)

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
    code = Code()
    # Assert that we have a sufficiently simple Instruction.
    assert all(
        name != 'ITEMS' and ':' not in name
        for name in instruction.args + instruction.results
    ), instruction
    num_args = len(instruction.args)
    num_results = len(instruction.results)
    # Check for underflow and overflow.
    # TODO: Move these checks into the caller.
    code.extend(cache_state.check_underflow(num_args))
    code.extend(cache_state.check_overflow(num_args, num_results))
    # Declare C variables for args and results.
    code.extend(Code(*[
        'mit_word {};'.format(name)
        for name in set(instruction.args + instruction.results)
    ]))
    # Load the arguments into their C variables.
    code.extend(cache_state.load_args(instruction.args))
    code.append('S->STACK_DEPTH -= {};'.format(num_args))
    code.extend(cache_state.add(-num_args))
    # Inline `instruction.code`.
    # Note: `S->STACK_DEPTH` and `cache_state` must be correct for RAISE().
    code.extend(instruction.code)
    # Store the results from their C variables.
    code.extend(cache_state.add(num_results))
    code.append('S->STACK_DEPTH += {};'.format(num_results))
    code.extend(cache_state.store_results(instruction.results))
    return code
