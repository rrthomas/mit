#!/usr/bin/env python3
# Set up an interactive Python session for use with libsmite
# Usage: [i]python3 -i python-test.py

import sys
from ctypes import *
from ctypes.util import find_library

from instructions import Opcodes, Types

libsmite = CDLL(find_library("smite"))

# Constants
word_size = c_int.in_dll(libsmite, "smite_word_size")
native_pointer_size = c_int.in_dll(libsmite, "smite_native_pointer_size")
byte_bit = c_int.in_dll(libsmite, "smite_byte_bit")
byte_mask = c_int.in_dll(libsmite, "smite_byte_mask")
word_bit = c_int.in_dll(libsmite, "smite_word_bit")
word_mask = c_int.in_dll(libsmite, "smite_word_mask")
uword_max = c_int.in_dll(libsmite, "smite_uword_max")
word_min = c_int.in_dll(libsmite, "smite_word_min")
stack_direction = c_int.in_dll(libsmite, "smite_stack_direction")

# FIXME: Allow multiple states
S = libsmite.smite_init_default_stacks(0x100000)

# Debugger API
here = 0

def ass_action(instr):
    here = libsmite.smite_encode_instruction(S, here, Types.ACTION, instr)

def ass_number(v):
    here = libsmite.smite_encode_instruction(S, here, Types.NUMBER, v)

def ass_native_pointer(pointer):
    for i in range(libsmite.smite_align(sizeof(pointer)) / word_size):
        ass_number(S, ptr & word_mask)
        ptr = ptr >> word_bit

def ass_byte(byte):
    store_byte(here, byte)
    here += 1

def disass(ty, opcode):
    if ty == Types.NUMBER:
        return f"{opcode} ({opcode:x})"
    elif ty == Types.ACTION:
        if opcode < 0 or opcode >= Opcodes.UNDEFINED:
            return "undefined"
        return mnemonic[opcode]
    else:
        return "invalid type!"

def _val_data_stack(with_hex):
    picture = ""
    if not libsmite.smite_stack_underflow(libsmite.smite_get_SP(S), libsmite.smite_get_S0(S)):
        i = 0
        while i != libsmite.smite_get_SP(S) - libsmite.smite_get_S0(S):
            i += stack_direction
            if not libsmite.smite_stack_valid(libsmite.smite_get_S0(S) + i, libsmite.smite_get_S0(S), libsmite.smite_get_SSIZE(S)):
                picture += "invalid address!"
                break
            picture += str(libsmite.smite_get_S0(S)[i])
            if with_hex:
                picture += f" ({libsmite.smite_get_S0(S)[i]:x}) "
            if i != libsmite.smite_get_SP(S) - libsmite.smite_get_S0(S):
                picture += " "
    return picture

def val_data_stack():
    return _val_data_stack(False)

def show_data_stack():
    if libsmite.smite_get_SP(S) == libsmite.smite_get_S0(S):
        printf("Data stack empty")
    elif libsmite.smite_stack_underflow(libsmite.smite_get_SP(S), libsmite.smite_get_S0(S)):
        print("Data stack underflow")
    else:
        print(f"Data stack: {_val_data_stack(S, True)}")

def show_return_stack():
    if libsmite.smite_get_RP(S) == libsmite.smite_get_R0(S):
        print("Return stack empty")
    elif libsmite.smite_stack_underflow(libsmite.smite_get_RP(S), libsmite.smite_get_R0(S)):
        print("Return stack underflow")
    else:
        print("Return stack: ", end="")
        i = 0
        while i != libsmite.smite_get_RP(S) - libsmite.smite_get_R0(S):
            i += stack_direction
            if not libsmite.smite_stack_valid(libsmite.smite_get_R0(S) + i, libsmite.smite_get_R0(S), libsmite.smite_get_RSIZE(S)):
                print("invalid address!", end="")
                break
            print("{libsmite.smite_get_R0(S)[i]:x} ", end="")
        print()

# TODO:
# Register short names
# REGISTERS command
# Stack manipulation and display
# Assembly: NUMBER, BYTE, POINTER and opcodes
# DUMP and DISASSEMBLE commands
# Memory assignment and display (word & byte)
# API short names
# INITIALISE command
# STEP|TRACE TO|N commands
# LOAD command
# SAVE command
