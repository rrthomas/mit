# Test the control instructions and `lit_pc_rel`. Also uses instructions
# tested by earlier tests. See errors.py for address error handling tests.
# The test program contains an infinite loop, but this is only executed
# once.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.globals import *
from mit.enums import Instructions


# Test results
correct = []

# Code
jump_rel(M.addr + 0x60)
goto(M.addr + 0x60)

correct.append(assembler.pc)
lit_pc_rel(M.addr + 0x30)
correct.append(assembler.pc)
ass(JUMP)
goto(M.addr + 0x30)

correct.append(assembler.pc)
lit_pc_rel(M.addr + 0x3000)
correct.append(assembler.pc)
ass(JUMP)
goto(M.addr + 0x3000)

correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
lit(M.addr + 0x2fff)
correct.append(assembler.pc)
ass(JUMPZ)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
lit(M.addr)
correct.append(assembler.pc)
ass(JUMPZ)
correct.append(assembler.pc)
lit(0)
label() # Ensure that jump_rel will be able to assemble the jump using immediate operand
correct.append(assembler.pc)
jump_rel(M.addr + 0x4008, JUMPZ)
goto(M.addr + 0x4008)

correct.append(assembler.pc)
lit(0)
label() # Ensure that jump_rel will be able to assemble the jump using immediate operand
correct.append(assembler.pc)
jump_rel(M.addr + 0x4008 + word_bytes * 8, JUMPZ)
goto(M.addr + 0x4008 + word_bytes * 8)

correct.append(assembler.pc)
lit(42)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
lit(0)
label() # Ensure that jump_rel will be able to assemble the jump using immediate operand
correct.append(assembler.pc)
jump_rel(M.addr + 0x260, CALL)
goto(M.addr + 0x260)

correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit_pc_rel(M.addr + 0xd0)
correct.append(assembler.pc)
ass(CALL)
# Record address we will return to later.
ret_addr = label()
goto(M.addr + 0xd0)

correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit(M.addr + 0x130)
correct.append(assembler.pc)
ass(CALL)
goto(M.addr + 0x130)

correct.append(assembler.pc)
ass(RET)
goto(M.addr + 0xd0 + word_bytes * 2)

correct.append(assembler.pc)
ass(RET)
goto(ret_addr)

correct.append(assembler.pc)
lit(M.addr + 0x40)
correct.append(assembler.pc)
lit(M.addr + 0x20)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
ass(SWAP)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
ass(DUP)
correct.append(assembler.pc)
ass(STORE)
correct.append(assembler.pc)
ass(LOAD)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
ass(SWAP)
correct.append(assembler.pc)
ass(CALL)
goto(M.addr + 0x40)
correct.append(assembler.pc)

# Test
opcode = None
done = 0
def test_callback(handler, stack):
    global opcode, done
    # Check results after each non-NEXT instruction.
    previous_opcode = opcode
    opcode = handler.state.ir & 0xff
    if previous_opcode in (None, Instructions.NEXT, Instructions.NEXTFF):
        return
    correct_pc = correct[done] - VM.M.addr
    pc = handler.state.pc - VM.M.addr
    handler.log(f"Instruction {done}: pc = {pc:#x} should be {correct_pc:#x}")
    if pc != correct_pc:
        print(f"Error in branch tests: pc = {pc:#x}")
        sys.exit(1)
    done += 1
    if done == len(correct):
        return MitErrorCode.OK
trace(addr=0, step_callback=test_callback)

print("Branch tests ran OK")
