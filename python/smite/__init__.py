'''
SMite

This module provides SMite bindings for Python 3, and offers a convenient
set of functions and variables to interact with SMite in a Python REPL.
Module smite.assembler provides Assembler and Disassembler.

(c) SMite authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

When run as a script (SMite provides 'smite-shell' to do this), the module
provides a global SMite instance in VM, and defines various globals. See
`globalize()` for details.

Registers: a variable for each register; also a list, 'registers'
Memory: M, M_word
Stacks: S, R
Managing the VM state: load, save, initialise
Controlling and observing execution: run, step
Examining memory: dump, disassemble
'''

import os
import sys
import collections.abc

from .vm_data import *
from .ext import *
from .binding import *
from .assembler import *


# Set up binary I/O flag
O_BINARY = 0
try:
    O_BINARY = os.O_BINARY
except:
    pass

# State
class State:
    '''A VM state.'''

    def __init__(self, memory_size=1024*1024, stack_size=1024):
        '''Initialise the VM state.'''
        self.state = libsmite.smite_init(memory_size, stack_size)
        if self.state == None:
            raise Error("error creating virtual machine state")

        self.registers = {
            name: ActiveRegister(self.state, name, register.value)
            for (name, register) in Registers.__members__.items()
        }
        self.M = Memory(self)
        self.memory_size = memory_size
        self.M_word = WordMemory(self)
        self.S = Stack(
            self.state,
            self.registers["STACK_DEPTH"],
        )
        self.stack_size = stack_size

    def __del__(self):
        libsmite.smite_destroy(self.state)

    def globalize(self, globals_dict):
        '''
        Make the state accessible through global variables and functions:

        Registers: a variable for each register; also a list 'registers'
        Managing the VM state: load, save
        Controlling and observing execution: run, step
        Memory: M[], M_word[], dump
        Assembly: Assembler, Disassembler, assembler,
            word, bytes, instruction, lit, lit_pc_rel, label, goto
        Abbreviations: ass=assembler.instruction, dis=self.disassemble

        The instruction opcodes are available as constants.
        '''
        globals_dict.update({
            name: register
            for name, register in self.registers.items()
        })
        globals_dict.update({
            name: self.__getattribute__(name)
            for name in [
                "M", "M_word", "S", "registers",
                "load", "save", "run", "step",
                "dump", "disassemble",
            ]
        })
        assembler = Assembler(self)
        globals_dict['assembler'] = assembler
        globals_dict.update({
            name: assembler.__getattribute__(name)
            for name in [
                "instruction", "lit", "lit_pc_rel",
                "word", "bytes", "label", "goto"
            ]
        })

        # Abbreviations
        globals_dict["ass"] = assembler.__getattribute__("instruction")
        globals_dict["dis"] = self.__getattribute__("disassemble")

        # Opcodes
        globals_dict.update({
            instruction.name: instruction.value.opcode
            for instruction in Instructions
        })
        globals_dict["UNDEFINED"] = 1 + max([
            instruction.value.opcode for instruction in Instructions])
        globals_dict.update({
            instruction.name: instruction.value.opcode
            for instruction in LibInstructions
        })
        for (name, instruction) in LibInstructions.__members__.items():
            globals_dict.update({
                '{}_{}'.format(name, function.name): function.value.opcode
                for function in instruction.value.library
            })

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

    def run(self, args=None):
        '''
        Run until HALT or error. Register any given command-line `args`.
        '''
        if args == None:
            args = []
        args.insert(0, b"smite-shell")
        self.register_args(*args)
        try:
            libsmite.smite_run(self.state)
        except ErrorCode as e:
            if e.args[0] == 128:
                # Halt.
                return
            else:
                raise

    def _print_trace_info(self):
        print("step: PC={} I={:#x} instruction={}".format(
            self.registers["PC"].get(),
            self.registers["I"].get(),
            Disassembler(self).disassemble(),
        ))
        print(str(self.S))

    def step(self, n=1, addr=None, trace=False, auto_NEXT=True):
        '''
        Single-step for n steps, or until PC=addr.
        Does not count NEXT as a step, but always stops when PC changes.
        '''
        try:
            done = 0
            ret = 0
            while True:
                if trace: self._print_trace_info()
                libsmite.smite_single_step(self.state)
                if (auto_NEXT and
                    self.registers["I"].get() & instruction_mask ==
                        Instructions.NEXT.value.opcode
                ):
                    if trace: self._print_trace_info()
                    ret = libsmite.smite_single_step(self.state)
                done += 1
                if (self.registers["PC"].get() == addr or
                    (addr == None and done == n)
                ):
                    break
        except ErrorCode as e:
            ret = e.args[0]

            if ret != 0:
                print("Error code {} was returned".format(ret), end='')
                if n > 1:
                    print(" after {} steps".format(done), end='')
                if addr != None:
                    print(" at PC = {:#x}".format(
                        self.registers["PC"].get()),
                        end='',
                    )
                print("")
            raise

    def load(self, file, addr=0):
        '''
        Load an object file at the given address. Returns the length.
        '''
        fd = os.open(file, os.O_RDONLY | O_BINARY)
        if fd < 0:
            raise Error("cannot open file {}".format(file))
        try:
            return libsmite.smite_load_object(self.state, addr, fd)
        finally:
            os.close(fd)

    def save(self, file, address=0, length=None):
        '''
        Save an object file from the given address and length.
        '''
        assert length is not None
        ptr = libsmite.smite_native_address_of_range(self.state, address, length)
        if not is_aligned(address) or ptr == None:
            return -1

        fd = os.open(file, os.O_CREAT | os.O_RDWR | O_BINARY, mode=0o666)
        if fd < 0:
            raise Error("cannot open file {}".format(file))
        try:
            return libsmite.smite_save_object(self.state, address, length, fd)
        finally:
            os.close(fd)

    # Disassembly
    def disassemble(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Disassemble `length` bytes from `start`, or from `start` to `end`.
        '''
        if length != None:
            end = start + length
        for inst in Disassembler(self, pc=start, end=end, i=0):
            print(inst, file=file)

    def dump(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Dump `length` bytes from `start` (rounded down to nearest 16),
        or from `start` to `end`.
        Defaults to 256 bytes from `start`.
        '''
        chunk = 16
        if start == None:
            start = max(0, self.registers["PC"].get())
        start -= start % chunk
        if length != None:
            end = start + length
        elif end == None:
            end = start + 256

        p = start
        while p < end:
            print("{:#08x} ".format(p), end='', file=file)
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
        self.name = name
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
            print("{} is read-only!".format(self.name))
        else:
            self.setter(self.state, v)


# Stacks
class Stack:
    '''VM stack.'''
    def __init__(self, state, depth):
        self.state = state
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

    def pop(self):
        '''Pop a word off the stack.'''
        v = c_word()
        ret = libsmite.smite_pop_stack(self.state, byref(v))
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
        else:
            return self.load(index)

    def __setitem__(self, index, value):
        if type(index) == slice:
            index_ = slice(index.start, index.stop, self.element_size)
            j = 0
            for i in range(*index_.indices(len(self))):
                self[i] = value[j]
                j += 1
        else:
            self.store(index, value)

    def load(self, index):
        '''
        Return the value at `index`.
        This is an abstract method, which must be overridden.
        '''
        raise NotImplementedError

    def store(self):
        '''
        Store `value` at `index`.
        This is an abstract method, which must be overridden.
        '''
        raise NotImplementedError

    def __len__(self):
        return self.memory_size * word_bytes

class Memory(AbstractMemory):
    '''A VM memory (byte-accessed).'''
    def load(self, index):
        word = c_word()
        libsmite.smite_load(self.VM.state, index, 0, byref(word))
        return word.value

    def store(self, index, value):
        libsmite.smite_store(self.VM.state, index, 0, c_word(value))

class WordMemory(AbstractMemory):
    '''A VM memory (word-accessed).'''
    def __init__(self, VM):
        super().__init__(VM)
        self.element_size = word_bytes

    def load(self, index):
        word = c_word()
        libsmite.smite_load(self.VM.state, index, size_word, byref(word))
        return word.value

    def store(self, index, value):
        libsmite.smite_store(self.VM.state, index, size_word, c_word(value))
