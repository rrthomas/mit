'''SMite

This module provides SMite bindings for Python 3, and offers a convenient
set of functions and variables to interact with SMite in a Python REPL.

When run as a script (SMite provides 'smite-shell' to do this), the module
provides a global SMite instance in VM, with the following attributes and
methods available as globals, as well as the action opcode enumeration:

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
import collections.abc
from ctypes import *
from ctypes.util import find_library

from .vm_data import *
from .vm_data_extra import *

library_file = find_library("smite")
assert(library_file)
libsmite = CDLL(library_file)
assert(libsmite)


# Errors
class Error(Exception):
    pass


# Constants (all of type unsigned)
vars().update([(c, c_uint.in_dll(libsmite, "smite_{}".format(c)).value)
               for c in ["word_size", "byte_bit", "byte_mask", "word_bit"]])
vars()["byte_bit"] = 8


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
vars().update([(c, cty.in_dll(libsmite, "smite_{}".format(c)).value)
               for (c, cty) in [
                       ("word_mask", c_word),
                       ("uword_max", c_uword),
                       ("word_min", c_word),
                       ("word_max", c_word),
               ]])


# Functions
c_ptrdiff_t = c_ssize_t

# smite.h
libsmite.smite_load_word.argtypes = [c_void_p, c_uword, POINTER(c_word)]
libsmite.smite_store_word.argtypes = [c_void_p, c_uword, c_word]
# N.B. load/store_byte in Python use UBYTE, not BYTE
libsmite.smite_load_byte.argtypes = [c_void_p, c_uword, POINTER(c_ubyte)]
libsmite.smite_store_byte.argtypes = [c_void_p, c_uword, c_ubyte]

libsmite.smite_load_stack.argtypes = [c_void_p, c_uword, POINTER(c_word)]
libsmite.smite_store_stack.argtypes = [c_void_p, c_uword, c_word]
libsmite.smite_pop_stack.argtypes = [c_void_p, POINTER(c_word)]
libsmite.smite_push_stack.argtypes = [c_void_p, c_word]

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
libsmite.smite_init.argtypes = [c_size_t, c_size_t]

libsmite.smite_realloc_memory.argtypes = [c_void_p, c_int]

libsmite.smite_realloc_stack.argtypes = [c_void_p, c_int]

libsmite.smite_destroy.restype = None
libsmite.smite_destroy.argtypes = [c_void_p]

libsmite.smite_register_args.argtypes = [c_void_p, c_int, c_void_p]

# aux.h
libsmite.smite_align.restype = c_uword
libsmite.smite_align.argtypes = [c_uword]

libsmite.smite_is_aligned.argtypes = [c_uword]


# State
class State:
    '''A VM state.'''

    def __init__(self, memory_size=1024*1024, stack_size=1024):
        '''Initialise the VM state.'''
        self.state = libsmite.smite_init(memory_size, stack_size)
        if self.state == None:
            raise Exception("error creating virtual machine state")

        self.registers = {name : ActiveRegister(self.state, name, register.value) for (name, register) in Registers.__members__.items()}
        self.M = Memory(self)
        self.M_word = WordMemory(self)
        self.S = Stack(self.state, self.registers["S0"], self.registers["STACK_SIZE"], self.registers["STACK_DEPTH"])
        self.here = 0

    def __del__(self):
        libsmite.smite_destroy(self.state)

    def globalize(self, globals_dict):
        '''Make the state accessible through global variables and functions:

        Registers: a variable for each register; also a list 'registers'
        Managing the VM state: load, save
        Controlling and observing execution: run, step, trace
        Examining memory: dump, disassemble
        Assembly: action, number, byte, pointer. Assembly is at address
        'VM.here', which defaults to 0. The actions are available as
        constants.'''

        globals_dict.update([(name, register) for name, register in self.registers.items()])
        globals_dict.update([(name, self.__getattribute__(name)) for
                             name in ["M", "M_word", "S", "registers",
                                      "load", "save",
                                      "run", "step", "trace", "dump", "disassemble",
                                      "disassemble_instruction",
                                      "assemble", "lit", "lit_pc_rel", "byte"]])

        # Abbreviations
        globals_dict["ass"] = self.__getattribute__("assemble")
        globals_dict["dis"] = self.__getattribute__("disassemble")

        # Opcodes
        globals_dict.update([(action.name, action.value.opcode) for action in Actions])
        globals_dict["UNDEFINED"] = max([action.value.opcode for action in Actions]) + 1
        globals_dict.update([(action.name, action.value.opcode) for action in LibActions])
        for (name, action) in LibActions.__members__.items():
            globals_dict.update([('{}_{}'.format(name, function.name), function.value.opcode) for function in action.value.library])

    def register_args(self, *args):
        argc = len(args)
        arg_strings = c_char_p * argc
        bargs = []
        for arg in args:
            if type(arg) == str:
                arg = bytes(arg, 'utf-8')
            elif type(arg) == int:
                arg = bytes(arg)
            bargs.append(arg)
        self.argv = arg_strings(*bargs)
        assert(libsmite.smite_register_args(self.state, argc, self.argv) == 0)

    def run(self, trace=False, args=None):
        '''
        Run (or trace if trace is True) until HALT or error. Register any given
        command-line `args`.
        '''
        if args == None:
            args = []
        args.insert(0, b"smite-shell")
        self.register_args(*args)
        if trace == True:
            return self.step(addr=self.registers["MEMORY"].get() + 1, trace=True)
        else:
            ret = libsmite.smite_run(self.state)
            if ret != 128:
                print("Error code {} was returned".format(ret));
            return ret

    def step(self, n=1, addr=None, trace=False):
        '''Single-step (or trace if trace is True) for n steps,
    or until PC=addr.'''
        done = 0
        while True:
            ret = libsmite.smite_single_step(self.state)
            done += 1
            if ret != 128 or self.registers["PC"].get() == addr or (addr == None and done == n):
                break

        if ret != 128:
            if ret != 0:
                print("Error code {} was returned".format(ret), end='')
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

        fd = os.open(file, os.O_RDONLY)
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

        fd = os.open(file, os.O_CREAT | os.O_RDWR)
        if fd < 0:
            fatal("cannot open file {}".format(file))
        ret = libsmite.smite_save_object(self.state, address, length, fd)
        os.close(fd)
        return ret

    # Assembly
    def assemble(self, instr):
        '''Assemble an instruction at 'here'.'''
        ptr = c_uword(self.here)
        libsmite.smite_store_byte(self.state, ptr, instr)
        self.here += 1

    def byte(self, byte):
        '''Assemble a byte at 'here'.'''
        self.M[self.here] = byte
        self.here += 1

    def lit(self, value):
        '''Assemble LIT 'value' at 'here'.'''
        self.assemble(Actions.LIT.value.opcode)
        self.M_word[self.here] = value
        self.here += word_size

    def lit_pc_rel(self, value):
        '''
        Assemble 'value' at 'here' as a PC-relative value relative to 'here' +
        1.
        '''
        self.assemble(Actions.LIT_PC_REL.value.opcode)
        self.M_word[self.here] = value - self.here
        self.here += word_size


    # Disassembly
    mnemonic = {instruction.value.opcode:instruction.name for instruction in Actions}
    mnemonic.update({instruction.value.opcode:instruction.name for instruction in LibActions})

    def disassemble_instruction(self, addr):
        try:
            opcode = self.M[addr]
        except IndexError:
            opcode = "invalid adddress!"
        try:
            addr, inst = addr + 1, self.mnemonic[opcode]
        except KeyError:
            return addr + 1, "undefined"
        if inst.startswith("LIT"):
            return addr + word_size, "{inst} {addr} ({addr:#x})".format(inst=inst, addr=self.M_word[addr])
        return addr, inst

    def disassemble(self, start=None, length=None, end=None, file=sys.stdout):
        '''Disassemble from start to start+length or from start to end.
    Defaults to 32 bytes from 4 bytes before PC.'''
        if start == None:
            start = max(0, self.registers["PC"].get() - 4)
        if length != None:
            end = start + length
        elif end == None:
            end = start + 32

        p = start
        while p < end:
            print("{:#x}: ".format(p), end='', file=file)

            p, s = self.disassemble_instruction(p)
            print(s, file=file)

    def dump(self, start=None, length=None, end=None, file=sys.stdout):
        '''Dump memory from start to start+length or from start to end.
    Defaults to 256 bytes from start - 16.'''
        if start == None:
            start = max(0, self.registers["PC"].get() - 16)
        if length != None:
            end = start + length
        elif end == None:
            end = start + 256

        p = start
        while p < end:
            print("{:#08x} ".format(p), end='', file=file)
            chunk = 16
            ascii = ""
            i = 0
            while i < chunk and p < end:
                if i % 8 == 0:
                    print(" ", end='', file=file)
                byte = self.M[p + i]
                print("{:02x} ".format(byte), end='', file=file)
                i += 1
                c = chr(byte)
                ascii += c if c.isprintable() else '.'
            p += chunk
            print(" |{0:.{1}}|".format(ascii, chunk), file=file)


# Registers
type_equivalents = {
    "smite_WORD": c_word,
    "smite_UWORD": c_uword,
    "smite_WORDP": POINTER(c_word),
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
            v = c_word()
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
        elif index >= len(self):
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
        elif index >= len(self):
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
        if libsmite.smite_is_aligned(index):
            word = c_word()
            libsmite.smite_load_word(self.VM.state, index, byref(word))
            return word.value
        else:
            value = 0
            for i in reversed(range(0, word_size)):
                value = (value << byte_bit) | self.VM.M[index + i]
            return value

    def store(self, index, value):
        if libsmite.smite_is_aligned(index):
            libsmite.smite_store_word(self.VM.state, index, c_word(value))
        else:
            for i in range(0, word_size):
                self.VM.M[index + i] = value & byte_mask
                value >>= byte_bit
