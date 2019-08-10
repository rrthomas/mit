'''
VM state.

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

Registers: a variable for each register; also a list, 'registers'
Memory: M, M_word
Stack: S
Managing the VM state: load, save
Controlling and observing execution: run, step
Examining memory: dump, disassemble
'''

import os
import sys

from .binding import (
    libmit, libmitfeatures,
    ErrorCode, is_aligned,
    word_bytes, opcode_mask,
    c_uword, c_void_p, c_char_p, byref,
    hex0x_word_width,
)
from .errors import MitErrorCode
from .opcodes import (
    Register,
    Instruction, InternalExtraInstruction, LibInstruction,
)
from .memory import Memory, WordMemory
from .stack import Stack
from .assembler import Assembler, Disassembler


# Set up binary I/O flag
O_BINARY = 0
try:
    O_BINARY = os.O_BINARY
except:
    pass

# State
class State:
    '''A VM state.'''
    def __new__(cls, memory_bytes=1024*1024 * word_bytes if word_bytes > 2 else 16*1024, stack_words=1024):
        '''Create the VM state.'''
        state = super().__new__(cls)
        state.state = libmit.mit_init(memory_bytes, stack_words)
        if state.state is None:
            raise Error("error creating virtual machine state")
        state.registers = {
            register.name: ActiveRegister(state.state, register.name, register)
            for register in Register
        }
        state.M = Memory(state)
        state.M_word = WordMemory(state)
        state.S = Stack(
            state.state,
            state.registers["stack_depth"],
        )
        state.memory_bytes = memory_bytes
        state.stack_words = stack_words
        return state

    def __del__(self):
        libmit.mit_destroy(self.state)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['registers']
        state['registers'] = {
            register.name: self.registers[register.name].get()
            for register in Register
        }
        del state['registers']['memory']
        del state['registers']['stack']
        del state['M']
        del state['M_word']
        state['M_word'] = self.M_word[0:len(self.M_word)]
        del state['S']
        state['S'] = self.S[0:self.registers["stack_depth"].get()]
        del state['state']
        if 'argv' in state:
            state['argv'] = [cstr for cstr in state['argv']]
        return state

    def __getnewargs__(self):
        return (self.memory_bytes, self.stack_words)

    def __setstate__(self, state):
        for name in state['registers']:
            self.registers[name].set(state['registers'][name])
        self.M_word[0:len(self.M_word)] = state['M_word']
        for item in state['S']: self.S.push(item)
        if 'argv' in state:
            self.register_args(*state['argv'])

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
        self.registers["ir"].set(0) # Skip to next instruction

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
                if e.args[0] == MitErrorCode.HALT:
                    return
                elif (e.args[0] == 1 and
                      self.registers["ir"].get() & opcode_mask == Instruction.JUMP
                ):
                    self.do_extra_instruction()
                else:
                    raise

    def _report_step_error(self, e, done, addr):
        ret = e.args[0]
        print("Error code {} was returned".format(ret), end='')
        print(" after {} step{}".format(done, 's' if done > 1 else ''), end='')
        if addr is not None:
            print(" at pc={:#x}".format(
                self.registers["pc"].get()),
                end='',
            )
        if ret != 0 and ret != MitErrorCode.HALT:
            raise

    def step(self, n=1, addr=None, auto_NEXT=True):
        '''
        Single-step for n steps (excluding NEXT when pc does not change), or
        until pc=addr.
        '''
        if addr is None:
            assert n != 0
            addr = 0
        else:
            n = 0

        n_ptr = c_uword(n)
        try:
            libmitfeatures.mit_step_to(self.state, byref(n_ptr), addr, auto_NEXT)
        except ErrorCode as e:
            self._report_step_error(e, n_ptr.value, addr)

    def trace(self, n=1, addr=None, auto_NEXT=True):
        '''
        Single-step (see `step`), printing the instruction being executed, and
        pc, ir, and the stack after each instruction.
        '''
        done = 0
        ret = 0
        while addr is not None or done < n:
            if auto_NEXT and self.registers["ir"].get() == 0:
                libmit.mit_single_step(self.state) # safe to assume no error
            if self.registers["pc"].get() == addr: break
            print("trace: instruction={}".format(
                Disassembler(self).disassemble(),
            ))
            print(str(self.S))
            try:
                libmit.mit_single_step(self.state)
            except ErrorCode as e:
                if (e.args[0] == 1 and
                    self.registers["ir"].get() & opcode_mask == Instruction.JUMP
                ):
                    self.do_extra_instruction()
                else:
                    self._report_step_error(e, done, addr)
            print("pc={:#x} ir={:#x}".format(
                self.registers["pc"].get(),
                self.registers["ir"].get(),
            ))
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
        for inst in Disassembler(self, pc=start, end=end):
            print(inst, file=file)

    def dump(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Dump `length` bytes from `start` (rounded down to nearest 16),
        or from `start` to `end`.
        Defaults to 256 bytes from `start`.
        '''
        chunk = 16
        if start is None:
            start = max(0, self.registers["pc"].get())
        start -= start % chunk
        if length is not None:
            end = start + length
        elif end is None:
            end = start + 256

        p = start
        while p < end:
            print(("{:#0" + str(hex0x_word_width) + "x} ").format(p), end='', file=file)
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
