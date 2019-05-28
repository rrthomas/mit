'''
Count the frequency of opcodes or pairs in a trace.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

def counts(Instruction, trace):
    '''
    Returns a list of (count, instruction) sorted by descending count for a
    trace.

     - Instruction - InstructionEnum
     - trace - bytes - opcode values
    '''
    counts = {instruction.opcode: 0 for instruction in Instruction}
    for opcode in trace: counts[opcode] += 1
    freq = sorted([(count, opcode) for opcode, count in counts.items()],
                  reverse=True)
    by_opcode = {instruction.opcode: instruction for instruction in Instruction}
    return [(count, by_opcode[opcode]) for count, opcode in freq]

def pair_counts(Instruction, trace):
    '''
    Returns a list of (count, (instruction1, instruction2)) sorted by
    descending count for a trace.

     - Instruction - InstructionEnum
     - trace - bytes - opcode values
    '''
    counts = {(instruction1.opcode, instruction2.opcode): 0
              for instruction1 in Instruction
              for instruction2 in Instruction}
    for opcode1, opcode2 in zip(trace, trace[1:]):
        counts[(opcode1, opcode2)] += 1
    freq = sorted([(count, (opcode1, opcode2))
                   for (opcode1, opcode2), count in counts.items()],
                  reverse=True)
    by_opcode = {instruction.opcode: instruction for instruction in Instruction}
    return [(count, (by_opcode[opcode1], by_opcode[opcode2]))
            for count, (opcode1, opcode2) in freq]
