'''
VM state.

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

Registers: a variable for each register; also a list, 'registers'
Memory: M, M_word
Stack: S
Managing the VM state: load, save, initialise
Controlling and observing execution: run, step
Examining memory: dump, disassemble
'''

import os
import sys

from .binding import *
from .opcodes import *
from .memory import *
from .stack import *
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

    def __init__(self, memory_size=1024*1024 if word_bytes > 2 else 16*1024, stack_size=1024):
        '''Initialise the VM state.'''
        self.state = libmit.mit_init(memory_size, stack_size)
        if self.state is None:
            raise Error("error creating virtual machine state")

        self.registers = {
            register.name: ActiveRegister(self.state, register.name, register)
            for register in Register
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
        libmit.mit_destroy(self.state)

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
                "load", "run", "step",
                "dump", "disassemble",
            ]
        })
        assembler = Assembler(self)
        def _save(file, address=0, length=None):
            if length is None:
                length = assembler.pc - address
            self.save(file, address, length)
        globals_dict['save'] = _save
        globals_dict['assembler'] = assembler
        globals_dict.update({
            name: assembler.__getattribute__(name)
            for name in [
                "instruction", "lit", "lit_pc_rel",
                "label", "goto"
            ]
        })

        # Abbreviations and diambiguations
        globals_dict["ass_word"] = assembler.__getattribute__("word")
        globals_dict["ass_bytes"] = assembler.__getattribute__("bytes")
        globals_dict["ass"] = assembler.__getattribute__("instruction")
        globals_dict["ass_extra"] = assembler.__getattribute__("extra_instruction")
        globals_dict["dis"] = self.__getattribute__("disassemble")

        # Opcodes
        globals_dict.update({
            instruction.name: instruction
            for instruction in Instruction
        })
        globals_dict["UNDEFINED"] = 1 + max(Instruction)
        globals_dict.update({
            instruction.name: instruction
            for instruction in InternalExtraInstruction
        })
        globals_dict.update({
            instruction.name: instruction
            for instruction in LibInstruction
        })
        globals_dict.update({
            lib.library.__name__: lib.library
            for lib in LibInstruction
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
        assert(libmit.mit_register_args(self.state, argc, self.argv) == 0)

    def do_extra_instruction(self):
        libmitfeatures.mit_extra_instruction(self.state)
        self.registers["I"].set(0) # Skip to next instruction

    def run(self, args=None, predictor=False, optimize=True):
        '''
        Run until `halt` or error.

         - args - list of str - command-line arguments to register.
         - predictor - bool - if True, gather data to build a predictor.
         - optimize - bool - if True, run with optimization.
        '''
        if args is None:
            args = []
        args.insert(0, b"mit-shell")
        self.register_args(*args)
        while True:
            try:
                if predictor == True:
                    libmitfeatures.mit_predictor_run(self.state)
                elif optimize == True:
                    libmitfeatures.mit_specializer_run(self.state)
                else:
                    libmit.mit_run(self.state)
            except ErrorCode as e:
                if e.args[0] == MitError.HALT:
                    return
                elif e.args[0] == 1 and self.registers["I"].get() & opcode_mask == JUMP:
                    self.do_extra_instruction()
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
        done = 0
        ret = 0
        while addr is not None or done < n:
            if auto_NEXT and self.registers["I"].get() == 0:
                if trace: self._print_trace_info()
                ret = libmit.mit_single_step(self.state)
            if self.registers["PC"].get() == addr: break
            if trace: self._print_trace_info()
            try:
                libmit.mit_single_step(self.state)
            except ErrorCode as e:
                ret = e.args[0]
                if ret == 1 and self.registers["I"].get() & opcode_mask == JUMP:
                    self.do_extra_instruction()
                    ret = 0
                if ret != 0:
                    print("Error code {} was returned".format(ret), end='')
                    if n > 1:
                        print(" after {} steps".format(done), end='')
                    if addr is not None:
                        print(" at PC = {:#x}".format(
                            self.registers["PC"].get()),
                            end='',
                        )
                    print("")
                    raise
            done += 1

    def load(self, file, addr=0):
        '''
        Load an object file at the given address. Returns the length.
        '''
        fd = os.open(file, os.O_RDONLY | O_BINARY)
        if fd < 0:
            raise Error("cannot open file {}".format(file))
        try:
            return libmit.mit_load_object(self.state, addr, fd)
        finally:
            os.close(fd)

    def save(self, file, address=0, length=None):
        '''
        Save an object file from the given address and length.
        '''
        assert length is not None
        ptr = libmit.mit_native_address_of_range(self.state, address, length)
        if not is_aligned(address) or ptr is None:
            return -1

        fd = os.open(file, os.O_CREAT | os.O_RDWR | O_BINARY, mode=0o666)
        if fd < 0:
            raise Error("cannot open file {}".format(file))
        try:
            return libmit.mit_save_object(self.state, address, length, fd)
        finally:
            os.close(fd)

    # Disassembly
    def disassemble(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Disassemble `length` bytes from `start`, or from `start` to `end`.
        '''
        if length is not None:
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
        if start is None:
            start = max(0, self.registers["PC"].get())
        start -= start % chunk
        if length is not None:
            end = start + length
        elif end is None:
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
class ActiveRegister:
    '''A VM register.'''
    def __init__(self, state, name, register):
        self.state = state
        self.register = register
        self.name = name
        self.getter = libmit["mit_get_{}".format(name)]
        self.getter.restype = c_uword
        self.getter.argtypes = [c_void_p]
        self.setter = libmit["mit_set_{}".format(name)]
        self.setter.restype = None
        self.setter.argtypes = [c_void_p, c_uword]

    def __str__(self):
        return str(self.get())

    def get(self):
        return int(self.getter(self.state))

    def set(self, v):
        self.setter(self.state, v)