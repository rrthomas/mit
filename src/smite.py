# Set up an interactive Python session for use with libsmite
# Usage:
#     PYTHONPATH=src ipython3 -i --autocall 2 -m smite
# or: PYTHONPATH=src python3 -i -m smite

'''SMite shell

This module offers a convenient set of functions and variables to interact
with an SMite instance in a Python REPL.

When run as a script, the module provides a global SMite instance in VM,
with the following attributes and methods available as globals, as well as
the action opcode enumeration:

Registers: a variable for each register; also a list, 'registers'
Memory: M, M_word
Stacks: S, R
Managing the VM state: load, save, initialise
Controlling and observing execution: run, step, trace
Examining memory: dump, disassemble
Assembly: action, number, byte, pointer. Assembly is at address 'here',
which defaults to 0.
'''

import os
import sys
import glob
import collections.abc
from ctypes import *
from ctypes.util import find_library
from curses.ascii import isprint

from vm_data import *
from opcodes_extra import *

libsmite = CDLL(find_library("smite"))


# Utility functions
def globfile(file):
    file = os.path.expanduser(file)
    files = glob.glob(file)
    if len(files) == 0:
        raise Error("cannot find file '{}'".format(file))
    elif len(files) > 1:
        raise Error("'{}' matches more than one file".format(file))
    return files[0]

def globdirname(file):
    if file.find('/') == -1:
        return file
    return globfile("{}/{}".format(os.path.dirname(file), os.path.basename(file)))


# Errors
class Error(Exception):
    pass


# Constants (all of type unsigned)
for c in ["word_size", "native_pointer_size", "byte_bit", "byte_mask",
          "word_bit", "stack_direction"]:
    vars().update([(c, c_uint.in_dll(libsmite, "smite_{}".format(c)).value)])
vars().update([("byte_bit", 8)])


# Types
if word_size == sizeof(c_int):
    c_word = c_int
    c_uword = c_uint
elif word_size == sizeof(c_long):
    c_word = c_long
    c_uword = c_ulong
elif word_size == sizeof(c_longlong):
    c_word = c_longlong
    c_uword = c_ulonglong
else:
    raise Exception("Could not find Python C type matching WORD (size {})".format(word_size))

SMITE_CALLBACK_FUNCTYPE = CFUNCTYPE(None, c_void_p)


# Constants that require VM types
for (c, cty) in [
        ("word_mask", c_word),
        ("uword_max", c_uword),
        ("word_min", c_word),
        ("default_memory_size", c_uword),
        ("max_memory_size", c_uword),
        ("default_stack_size", c_uword),
        ("max_stack_size", c_uword),
]:
    vars().update([(c, cty.in_dll(libsmite, "smite_{}".format(c)).value)])


# Functions
c_ptrdiff_t = c_ssize_t

# public.h
libsmite.smite_load_word.argtypes = [c_void_p, c_uword, POINTER(c_word)]
libsmite.smite_store_word.argtypes = [c_void_p, c_uword, c_word]
# N.B. load/store_byte in Python use UBYTE, not BYTE
libsmite.smite_load_byte.argtypes = [c_void_p, c_uword, POINTER(c_ubyte)]
libsmite.smite_store_byte.argtypes = [c_void_p, c_uword, c_ubyte]

libsmite.smite_load_stack.argtypes = [c_void_p, c_uword, POINTER(c_word)]
libsmite.smite_store_stack.argtypes = [c_void_p, c_uword, c_word]
libsmite.smite_pop_stack.argtypes = [c_void_p, POINTER(c_word)]
libsmite.smite_push_stack.argtypes = [c_void_p, c_word]

libsmite.smite_load_return_stack.argtypes = [c_void_p]
libsmite.smite_store_return_stack.argtypes = [c_void_p]
libsmite.smite_pop_return_stack.argtypes = [c_void_p]
libsmite.smite_push_return_stack.argtypes = [c_void_p]

libsmite.smite_native_address_of_range.restype = POINTER(c_ubyte)
libsmite.smite_native_address_of_range.argtypes = [c_void_p, c_uword, c_uword]

libsmite.smite_run.restype = c_word
libsmite.smite_run.argtypes = [c_void_p]

libsmite.smite_single_step.restype = c_word
libsmite.smite_single_step.argtypes = [c_void_p]

libsmite.smite_load_object.restype = c_ptrdiff_t
libsmite.smite_load_object.argtypes = [c_void_p, c_uword, c_int]

libsmite.smite_save_object.argtypes = [c_void_p, c_uword, c_uword, c_int]

libsmite.smite_init.restype = c_void_p
libsmite.smite_init.argtypes = [c_size_t, c_size_t, c_size_t]

libsmite.smite_mem_realloc.argtypes = [c_void_p, c_int, c_void_p]

libsmite.smite_destroy.restype = None
libsmite.smite_destroy.argtypes = [c_void_p]

libsmite.smite_register_args.argtypes = [c_void_p, c_int, c_void_p]

# aux.h
libsmite.smite_align.restype = c_uword
libsmite.smite_align.argtypes = [c_uword]

libsmite.smite_is_aligned.argtypes = [c_uword]

libsmite.smite_find_msbit.argtypes = [c_word]

libsmite.smite_byte_size.argtypes = [c_word]

libsmite.smite_init_default_stacks.restype = c_void_p
libsmite.smite_init_default_stacks.argtypes = [c_size_t]

libsmite.smite_encode_instruction_file.restype = c_ptrdiff_t
libsmite.smite_encode_instruction_file.argtypes = [c_int, c_int, c_word]

libsmite.smite_encode_instruction.restype = c_ptrdiff_t
libsmite.smite_encode_instruction.argtypes = [c_void_p, c_uword, c_int, c_word]

libsmite.smite_decode_instruction_file.restype = c_ptrdiff_t
libsmite.smite_decode_instruction_file.argtypes = [c_int, POINTER(c_word)]

libsmite.smite_decode_instruction.restype = c_ptrdiff_t
libsmite.smite_decode_instruction.argtypes = [c_void_p, POINTER(c_uword), POINTER(c_word)]


# State
class State:
    '''A VM state.'''

    def __init__(self, memory_size=default_memory_size,
                 data_stack_size=default_stack_size,
                 return_stack_size=default_stack_size):
        '''Initialise the VM state.'''
        self.state = libsmite.smite_init(memory_size, data_stack_size, return_stack_size)
        if self.state == None:
            raise Exception("error creating virtual machine state")

        self.registers = {name : ActiveRegister(self.state, name, register.value) for (name, register) in Registers.__members__.items()}
        self.M = Memory(self)
        self.M_word = WordMemory(self)
        self.S = Stack(self.state, self.registers["S0"], self.registers["SSIZE"], self.registers["SDEPTH"])
        self.R = Stack(self.state, self.registers["R0"], self.registers["RSIZE"], self.registers["RDEPTH"])
        self.here = 0

    def __del__(self):
        libsmite.smite_destroy(self.state)

    def globalize(self, globals=globals()):
        '''Make the state accessible through global variables and functions:

        Registers: a variable for each register; also a list 'registers'
        Managing the VM state: load, save
        Controlling and observing execution: run, step, trace
        Examining memory: dump, disassemble
        Assembly: action, number, byte, pointer. Assembly is at address
        'VM.here', which defaults to 0. The actions are available as
        constants.'''

        for name, register in self.registers.items():
            globals.update([(name, register)])
        for name in ["M", "M_word", "S", "R", "registers",
                     "load", "save",
                     "run", "step", "trace", "dump", "disassemble",
                     "disassemble_instruction",
                     "action", "number", "byte", "pointer"]:
            globals.update([(name, self.__getattribute__(name))])

        # Opcodes
        for opcode in Opcodes:
            globals.update([(opcode.name, opcode)])
        globals.update([("UNDEFINED", max(list(map(int, Opcodes))) + 1)])

    def run(self, trace=False):
        '''Run (or trace if trace is True) until HALT or exception.'''
        if trace == True:
            return self.step(addr=self.registers["MEMORY"].get() + 1, trace=True)
        else:
            ret = libsmite.smite_run(self.state)
            if ret != -258:
                print("HALT code {} was returned".format(ret));
            return ret

    def step(self, n=1, addr=None, trace=False):
        '''Single-step (or trace if trace is True) for n steps,
    or until PC=addr.'''
        done = 0
        for i in range(n):
            ret = libsmite.smite_single_step(self.state)
            if ret != -258 or self.registers["PC"].get() == addr:
                done = i
                break

        if ret != -258:
            if ret != 0:
                print("HALT code {} was returned".format(ret), end='')
            if n > 1:
                print(" after {} steps".format(done), end='')
            if addr != None:
                print(" at PC = {:#x}".format(self.registers["PC"].get()), end='')
            print("")

        return ret

    def trace(self, n=1, addr=None):
        '''Alias for step with trace=True.'''
        step(n, addr=addr, trace=True)

    class LoadError(Exception):
        pass

    def load(self, file, addr=0):
        '''Load an object file at the given address.
        Returns the length.'''

        fd = os.open(globdirname(file), os.O_RDONLY)
        if fd < 0:
            raise Error("cannot open file {}".format(file))
        ret = libsmite.smite_load_object(self.state, addr, fd)
        os.close(fd)
        if ret < 0:
            try:
                err = {
                    -1: "address out of range or unaligned, or module too large",
                    -2: "module header invalid",
                    -3: "error while loading module",
                    -4: "module has wrong ENDISM",
                    -5: "module has wrong WORD_SIZE",
                }[ret]
            except:
                err = "unknown error!"
            raise self.LoadError(err, ret)
        return ret

    def save(self, file, address=0, length=None):
        '''Save an object file from the given address and length.
    length defaults to 'here'.'''
        if length == None:
            length = self.here - address
        ptr = libsmite.smite_native_address_of_range(self.state, address, length)
        if not libsmite.smite_is_aligned(address) or ptr == None:
            return -1

        fd = os.open(globdirname(file), os.O_CREAT | os.O_RDWR)
        if fd < 0:
            fatal("cannot open file {}".format(file))
        ret = libsmite.smite_save_object(self.state, address, length, fd)
        os.close(fd)
        return ret

    # Assembly
    def action(self, instr):
        '''Assemble an action at 'here'.'''
        self.here += libsmite.smite_encode_instruction(self.state, self.here, Types.ACTION, instr)

    def number(self, value):
        '''Assemble a number at 'here'.'''
        self.here += libsmite.smite_encode_instruction(self.state, self.here, Types.NUMBER, value)

    def byte(self, byte):
        '''Assemble a byte at 'here'.'''
        self.M[self.here] = byte
        self.here += 1

    def pointer(self, pointer):
        '''Assemble a native pointer at 'here'.'''
        for i in range(libsmite.smite_align(native_pointer_size) // word_size):
            self.number(pointer & word_mask)
            pointer = pointer >> word_bit


    # Disassembly
    mnemonic = {}
    for opcode in Opcodes:
        mnemonic[opcode] = opcode

    def disassemble_instruction(self, ty, opcode):
        if ty == Types.NUMBER:
            return "{} ({:#x})".format(opcode, opcode)
        elif ty == Types.ACTION:
            try:
                return self.mnemonic[opcode].name
            except KeyError:
                return "undefined"
        else:
            return "invalid type!"

    def disassemble(self, start=None, length=None, end=None):
        '''Disassemble from start to start+length or from start to end.
    Defaults to 64 bytes from 16 bytes before PC.'''
        if start == None:
            start = max(0, self.registers["PC"].get() - 16)
        if length != None:
            end = start + length
        elif end == None:
            end = start + 64

        p = start
        while p < end:
            print("{:#x}: ".format(p), end='')

            ptr = c_word(p)
            val = c_word()
            ty = libsmite.smite_decode_instruction(self.state, byref(ptr), byref(val))
            p = ptr.value

            if ty < 0:
                print("Error reading memory")
            else:
                s = self.disassemble_instruction(ty, val.value)
                if s == "undefined":
                    print("Undefined instruction")
                else:
                    print(s)

    def dump(self, start=None, length=None, end=None):
        '''Dump memory from start to start+length or from start to end.
    Defaults to 256 bytes from start - 64.'''
        if start == None:
            start = max(0, self.registers["PC"].get() - 64)
        if length != None:
            end = start + length
        elif end == None:
            end = start + 256

        p = start
        while p < end:
            print("{:#08x} ".format(p), end='')
            chunk = 16
            ascii = ""
            i = 0
            while i < chunk and p < end:
                if i % 8 == 0:
                    print(" ", end='')
                byte = M[p + i]
                print("{:02x} ".format(byte), end='')
                i += 1
                ascii += chr(byte) if isprint(byte) else '.'
            p += chunk
            print(" |{0:.{1}}|".format(ascii, chunk))


# Registers
type_equivalents = {
    "WORD": c_word,
    "UWORD": c_uword,
    "WORDP": POINTER(c_word),
}
class ActiveRegister:
    '''A VM register.'''
    def __init__(self, state, name, register):
        self.state = state
        self.register = register
        self.getter = libsmite["smite_get_{}".format(name)]
        self.getter.restype = type_equivalents[register.ty]
        self.getter.argtypes = [c_void_p]
        if not register.read_only:
            self.setter = libsmite["smite_set_{}".format(name)]
            self.setter.restype = None
            self.setter.argtypes = [c_void_p, type_equivalents[register.ty]]

    # After https://github.com/ipython/ipython/blob/master/IPython/lib/pretty.py
    def __str__(self):
        return str(self.get())

    def get(self):
        return self.getter(self.state)

    def set(self, v):
        if self.register.read_only:
            print("{} is read-only!".format(self.register.name))
        else:
            self.setter(self.state, v)


# Stacks
class Stack:
    class StackError(Exception):
        pass

    '''VM stack.'''
    def __init__(self, state, base, size, depth):
        self.state = state
        self.base = base
        self.size = size
        self.depth = depth

    # After https://github.com/ipython/ipython/blob/master/IPython/lib/pretty.py
    def __str__(self):
        l = []
        for i in range(self.depth.get(), 0, -1):
            v = c_int()
            libsmite.smite_load_stack(self.state, i - 1, byref(v))
            l.append(v.value)
        return str(l)

    def push(self, v):
        '''Push a word on to the stack.'''
        ret = libsmite.smite_push_stack(self.state, v)
        if ret < 0:
            raise self.StackError("error pushing to stack")

    def pop(self):
        '''Pop a word off the stack.'''
        v = c_word()
        ret = libsmite.smite_pop_stack(self.state, byref(v))
        if ret < 0:
            raise self.StackError("error popping from stack")
        return v.value


# Memory access (word & byte)
class AbstractMemory(collections.abc.Sequence):
    '''A VM memory (abstract superclass).'''
    def __init__(self, VM):
        self.VM = VM
        self.element_size = 1

    def __getitem__(self, index):
        if isinstance(index, slice):
            index_ = slice(index.start, index.stop, self.element_size)
            return [self[i] for i in range(*index_.indices(len(self)))]
        elif type(index) != int:
            raise TypeError
        elif index >= len(self) or index % self.element_size != 0:
            raise IndexError
        else:
            return self.load(index)

    def __setitem__(self, index, value):
        if type(index) == slice:
            index_ = slice(index.start, index.stop, self.element_size)
            j = 0
            for i in range(*index_.indices(len(self))):
                self[i] = value[j]
                j += 1
        elif type(index) != int:
            raise TypeError
        elif index >= len(self) or index % self.element_size != 0:
            raise IndexError
        else:
            self.store(index, value)

    def __len__(self):
        return self.VM.registers["MEMORY"].get()

class Memory(AbstractMemory):
    '''A VM memory (byte-accessed).'''
    def load(self, index):
        byte = c_ubyte()
        libsmite.smite_load_byte(self.VM.state, index, byref(byte))
        return byte.value

    def store(self, index, value):
        libsmite.smite_store_byte(self.VM.state, index, c_ubyte(value))

class WordMemory(AbstractMemory):
    '''A VM memory (word-accessed).'''
    def __init__(self, VM):
        super().__init__(VM)
        self.element_size = word_size

    def load(self, index):
        word = c_word()
        libsmite.smite_load_word(self.VM.state, index, byref(word))
        return word.value

    def store(self, index, value):
        libsmite.smite_store_word(self.VM.state, index, c_word(value))


# Make some handy globals for interactive use
if __name__ == "__main__":
    global VM
    VM = State()
    VM.globalize()
