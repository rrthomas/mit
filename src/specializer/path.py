'''
Tools for optimizing sequences of Instructions.

Copyright (c) 2018-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import re, functools

from mit_core.params import word_bit
from mit_core.spec import opcode_bit
from spec import Instruction


class State:
    '''
    Accumulates information about the effect of executing instructions.
     - stack_pos - int - the stack depth change.
     - stack_min - int - the minimal `stack_pos` encountered so far.
       Typically this will have occurred in the middle of an instruction,
       after popping but before pushing.
     - stack_max - int - the maximal `stack_pos` encountered so far.
     - max_cached_depth - the maximum `cached_depth()` at any point along this
       Path. In general, this will have occurred in the middle of an
       instruction, after popping but before pushing. This may be larger than
       the maximum of `cached_depth()` between instructions. This may be
       smaller than `stack_max - stack_min`.
     - i_bits - int - the number of bits of `ir` executed since the last
       terminal instruction.
    '''
    def __init__(
        self,
        stack_pos=0,
        stack_min=0,
        stack_max=0,
        max_cached_depth=0,
        i_bits=0,
    ):
        self.stack_pos = stack_pos
        self.stack_min = stack_min
        self.stack_max = stack_max
        self.max_cached_depth = max_cached_depth
        self.i_bits = i_bits

    def cached_depth(self):
        '''
        Returns the number of stack items that are known to be cacheable.
        '''
        return self.stack_pos - self.stack_min

    def checked_depth(self):
        '''
        Returns the number of free stack slots that are known to exist.
        '''
        return self.stack_max - self.stack_pos

    def step(self, instruction):
        '''
        Returns the State that results from executing `instruction` in this
        State. Raises ValueError if `instruction` is variadic.
         - instruction - a Instruction.
        '''
        assert isinstance(instruction, Instruction)
        # Simulate popping arguments.
        stack_pos = self.stack_pos - len(instruction.effect.args.items)
        stack_min = min(self.stack_min, stack_pos)
        cd1 = stack_pos - stack_min
        # Simulate pushing results.
        stack_pos += len(instruction.effect.results.items)
        stack_max = max(self.stack_max, stack_pos)
        cd2 = stack_pos - stack_min
        # Simulate consuming `ir`.
        i_bits = self.i_bits + opcode_bit
        if instruction.terminal:
            i_bits = 0
        return State(
            stack_pos=stack_pos,
            stack_min=stack_min,
            stack_max=stack_max,
            max_cached_depth=max(self.max_cached_depth, cd1, cd2),
            i_bits=i_bits,
        )


@functools.total_ordering
class Path:
    '''
    Represents a sequence of Instructions.

     - instructions - tuple of Instructions.
     - state - the State that exists at the end of this Path.
    '''
    def __init__(self, instructions):
        '''
        Construct a Path for `instructions`.
        '''
        assert type(instructions) is tuple
        self.instructions = instructions
        self.state = State()
        for instruction in instructions:
            if instruction.effect is not None:
                self.state = self.state.step(instruction)

    def _opcodes(self):
        return [i.opcode for i in self.instructions]

    def __repr__(self):
        return 'Path(({}))'.format(
            ', '.join(i.name for i in self.instructions)
        )

    def __le__(self, other):
        return self._opcodes().__le__(other._opcodes())

    def __eq__(self, other):
        return self.instructions == other.instructions

    def __hash__(self):
        return hash(self.instructions)

    def __len__(self):
        return len(self.instructions)

    def __getitem__(self, index_or_slice):
        if isinstance(index_or_slice, slice):
            return Path(self.instructions[index_or_slice])
        elif isinstance(index_or_slice, int):
            return self.instructions[index_or_slice]
        else:
            raise TypeError('Path indices must be integers or slices')

    def __add__(self, sequence):
        return Path(self.instructions + sequence)

    def is_suffix_of(self, other):
        '''Tests whether `self` is a suffix of `other`.'''
        pos = len(other) - len(self)
        return other.instructions[pos:] == self.instructions

    def is_proper_suffix_of(self, other):
        return len(self) < len(other) and self.is_suffix_of(other)

    def is_prefix_of(self, other):
        '''Tests whether `self` is a prefix of `other`.'''
        pos = len(self)
        return other.instructions[:pos] == self.instructions

    def is_proper_prefix_of(self, other):
        return len(self) < len(other) and self.is_prefix_of(other)

    def _end_of_prefix(self, other):
        '''
        Returns the last instruction of `other` that is not in `self`.
        Requires that `self` is a proper suffix of `other`.
        '''
        assert self.is_proper_suffix_of(other)
        pos = len(other) - len(self)
        return other[pos - 1]
