'''
Tools for optimizing sequences of Instructions.

Copyright (c) 2018-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import re, functools

from mit_core.code_util import Code
from mit_core.vm_data import Instruction
from mit_core.instruction import InstructionEnum
from mit_core.params import opcode_bit, word_bit


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

SpecializedInstruction = InstructionEnum('SpecializedInstruction', {
    '{name}_WITH_{tos_constant}'.format(
        name=instruction.name,
        tos_constant=tos_constant,
    ): _gen_specialized_instruction(instruction, tos_constant)
    for instruction in Instruction
    if 'ITEMS' in instruction.args
    for tos_constant in range(4)
})


class State:
    '''
    Accumulates information about the effect of executing instructions.
     - tos_constant - int - the constant value on the top of the stack,
       or `None` if unknown.
     - stack_pos - int - the stack depth change.
     - stack_min - int - the minimal `stack_pos` encountered so far.
       Typically this will have occurred in the middle of an instruction,
       after popping but before pushing.
     - stack_max - int - the maximal `stack_pos` encountered so far.
     - i_bits - int - the number of bits of ir executed since the last
       terminal instruction.
    '''
    def __init__(
        self,
        tos_constant=None,
        stack_pos=0,
        stack_min=0,
        stack_max=0,
        i_bits=0,
    ):
        self.tos_constant = tos_constant
        self.stack_pos = stack_pos
        self.stack_min = stack_min
        self.stack_max = stack_max
        self.i_bits = i_bits

    def cached_depth(self):
        '''
        Returns the number of stack items that can be cached in C variables
        after executing this Path.
        '''
        return self.stack_pos - self.stack_min

    def checked_depth(self):
        '''
        Returns the number of free stack slots that are known to exist
        after executing this Path.
        '''
        return self.stack_max - self.stack_pos

    def specialize_instruction(self, instruction):
        '''
        Tries to replace `instruction` with a specialized version that does
        the job in this State. Returns it, or `instruction` unchanged.
        '''
        assert isinstance(instruction, Instruction)
        try:
            name = '{}_WITH_{}'.format(instruction.name, self.tos_constant)
            return SpecializedInstruction[name]
        except KeyError:
            return instruction

    def step(self, instruction):
        '''
        Returns the State that results from executing `instruction` in this
        State. Raises ValueError if `instruction` is variadic.
         - instruction - an InstructionEnum, typically an Instruction or a
           SpecializedInstruction.
        '''
        assert isinstance(instruction, InstructionEnum)
        if 'ITEMS' in instruction.args or 'ITEMS' in instruction.results:
            # TODO: Use a more specific exception
            raise ValueError("non-constant variadic instruction")
        # Update `tos_constant`.
        m = re.match('LIT_(\d+)', instruction.name)
        if m:
            tos_constant = int(m.group(1))
        elif instruction == Instruction.NEXT:
            tos_constant = self.tos_constant
        else:
            tos_constant = None
        # Simulate popping arguments.
        stack_pos = self.stack_pos - len(instruction.args)
        stack_min = min(self.stack_min, stack_pos)
        # Simulate pushing results.
        stack_pos += len(instruction.results)
        stack_max = max(self.stack_max, stack_pos)
        # Simulate consuming ir.
        i_bits = self.i_bits + opcode_bit
        if instruction.terminal:
            i_bits = 0
        return State(
            tos_constant=tos_constant,
            stack_pos=stack_pos,
            stack_min=stack_min,
            stack_max=stack_max,
            i_bits=i_bits,
        )

    def is_worthwhile(self, instruction):
        '''
        Returns `True` if we have some hope of optimizing the implementation
        of `instruction` in this State.

        In practice, this method returns `False` only if `instruction` is
        variadic and the value at the top of the stack is not a known
        constant.
        '''
        bits_remaining = word_bit - self.i_bits
        if bits_remaining < 0:
            mask_remaining = 0
        else:
            mask_remaining = (1 << bits_remaining) - 1
        if instruction.opcode & mask_remaining != instruction.opcode:
            # There's no way of encoding the instruction.
            return False
        if 'ITEMS' in instruction.args or 'ITEMS' in instruction.results:
            # Variadic instruction. We can optimize only if we know `COUNT`.
            return (
                instruction.args[-1] == 'COUNT' and
                self.tos_constant is not None
            )
        else:
            # Ordinary instruction.
            return True


@functools.total_ordering
class Path:
    '''
    Represents a sequence of Instructions that is potentially optimizable.
    Does not handle variadic instructions unless there is a known constant
    on the top of the stack.

     - instructions - tuple of Instructions.
     - state - the State that exists at the end of this Path. Stack depths
       are measured relative to the beginning of this Path.
    '''
    def __init__(self, instructions):
        '''
        Construct a Path for `instructions`. The Path must not include a
        variadic instruction when the value at the top of the stack
        is not a known constant.
        '''
        assert type(instructions) is tuple
        self.instructions = instructions
        self.state = State()
        for instruction in instructions:
            instruction = self.state.specialize_instruction(instruction)
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

    def remove_repeating_part(self):
        '''
        If all of:
         - this Path ends with two repeats of some "loop body",
         - we know at least as much about the stack now as we did before
           the last repeat,
        returns the Path before the last repeat, otherwise returns `self`.
        '''
        if len(self.instructions) < 2:
            return self
        state = self.state
        for n in range(2, len(self)//2+1):
            if self.instructions[-n:] == self.instructions[-2*n:-n]:
                shorter = self[:-n]
                if (state.cached_depth() >= shorter.state.cached_depth() and
                    state.checked_depth() >= shorter.state.checked_depth()
                ):
                    return shorter
        return self

    def suffixes(self):
        '''Yields legal proper suffixes of this Path.'''
        for i in range(1, len(self) + 1):
            try:
                yield self[i:]
            except ValueError:
                pass

