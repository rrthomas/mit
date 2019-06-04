'''
Count the frequency of opcodes in a predictor.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import json


def counts(Instruction, predictor_file):
    '''
    Returns a list of (count, instruction) sorted by descending count for a
    predictor file.

     - Instruction - InstructionEnum
     - predictor_file - file - output of gen-predictor (q.v.)
    '''
    # Read trace, computing opcode counts
    counts = {instruction.opcode: 0 for instruction in Instruction}
    for state in json.load(predictor_file):
        for opcode, obj in state.items():
            # We'll get an error for an illegal opcode!
            counts[int(opcode, 16)] += obj['count']

    # Compute instruction frequencies
    freqs = sorted([(count, opcode)
                   for opcode, count in counts.items()],
                  reverse=True)

    # Return instruction frequencies
    by_opcode = {i.opcode: i for i in Instruction}
    return [(count, by_opcode[opcode]) for count, opcode in freqs]
