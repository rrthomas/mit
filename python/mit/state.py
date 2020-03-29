'''
VM state.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

Registers: a variable for each register; also a list, 'registers'
Memory: M, M_word
Stack: S
Managing the VM state: load, save
Controlling and observing execution: run, step, trace
Examining memory: dump, disassemble, dump_files
'''

import sys
from ctypes import create_string_buffer

from . import enums
from .binding import (
    libmit, libmitfeatures,
    Error, VMError, is_aligned,
    word_bytes, word_mask, opcode_mask,
    c_word, c_uword, c_void_p, c_char_p, byref,
    hex0x_word_width,
)
from .memory import Memory
from .assembler import Assembler, Disassembler


class State:
    '''
    A VM state.

         - stack_words - int - number of words of stack space.
         - args - list of str - command-line arguments to register.
         - memory - ctypes.Array of c_char - main memory.

    Note: For some reason, an array created as a "multiple" of c_char does
    not have the right type. ctypes.create_string_buffer must be used.
    '''
    def __new__(cls, memory_words=1024*1024, stack_words=1024, args=None):
        '''
        Create the VM state.

         - memory_words - int - number of words of main memory.
        '''
        state = super().__new__(cls)
        state.state = libmit.mit_new_state(stack_words)
        if state.state is None:
            raise Error("error creating virtual machine state")
        state.registers = {
            register.name: Register(state.state, register)
            for register in enums.Register
        }
        if memory_words is not None:
            state.set_memory(create_string_buffer(memory_words * word_bytes))
        state.S = Stack(state.state)
        if args is None:
            args = []
        args.insert(0, b"mit-shell")
        state.register_args(*args)
        return state

    def set_memory(self, memory):
        self.memory = memory
        self.M = Memory(self.memory)
        self.registers['pc'].set(self.M.addr)
        self.M_word = Memory(self.memory, element_size=word_bytes)

    def __del__(self):
        libmit.mit_free_state(self.state)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['registers']
        state['registers'] = {
            name: register.get()
            for name, register in self.registers.items()
            if name not in ('stack', 'stack_words')
        }
        del state['memory']
        del state['M']
        del state['M_word']
        state['M'] = bytes(self.M.buffer)[0:-1] # Remove trailing NUL
        del state['S']
        state['S'] = self.S[0:self.registers["stack_depth"].get()]
        del state['state']
        if 'argv' in state:
            state['argv'] = [cstr for cstr in state['argv']]
        return state

    def __getnewargs__(self):
        return (libmit.mit_get_stack_words(self.state),)

    def __setstate__(self, state):
        for name, value in state['registers'].items():
            self.registers[name].set(value)
        self.set_memory(create_string_buffer(state['M']))
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
        assert libmitfeatures.mit_register_args(argc, self.argv) == 0

    def do_extra_instruction(self):
        libmitfeatures.mit_extra_instruction(self.state)
        self.registers["ir"].set(0) # Skip to next instruction

    def run(self, optimize=True):
        '''
        Run until `halt` or error.

         - optimize - bool - if True, run with optimization.
        '''
        while True:
            try:
                if optimize == True:
                    libmitfeatures.mit_specializer_run(self.state)
                else:
                    libmit.mit_run(self.state)
            except VMError as e:
                if e.args[0] == enums.MitErrorCode.HALT:
                    return
                elif (
                    e.args[0] == 1 and (
                        self.registers["ir"].get() & opcode_mask ==
                        enums.Instruction.JUMP
                    )
                ):
                    self.do_extra_instruction()
                else:
                    raise

    def _report_step_error(self, e, done, addr):
        ret = e.args[0]
        print("Error code {} was returned".format(ret), end='')
        print(" after {} step{}".format(done, 's' if done != 1 else ''), end='')
        if addr is not None:
            print(" at pc={:#x}".format(
                self.registers["pc"].get()),
                end='',
            )
        print()
        if ret != 0 and ret != enums.MitErrorCode.HALT:
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
        except VMError as e:
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
            try:
                libmit.mit_single_step(self.state)
            except VMError as e:
                if (
                    e.args[0] == 1 and (
                        self.registers["ir"].get() & opcode_mask ==
                        enums.Instruction.JUMP
                    )
                ):
                    self.do_extra_instruction()
                else:
                    self._report_step_error(e, done, addr)
            print("pc={:#x} ir={:#x}".format(
                self.registers["pc"].get(),
                self.registers["ir"].get(),
            ))
            print(str(self.S))
            done += 1

    def load(self, file, addr=None):
        '''
        Load a binary file at the given address (default is `memory`).
        Returns the length in words.
        '''
        def strip_hashbang(data):
            if data[:2] == b'#!':
                try:
                    i = data.index(b'\n')
                except ValueError: # No \n, so just a #! line
                    i = len(data) - 1
                data = data[i + 1:]
            return data

        with open(file, 'rb') as h:
            data = h.read()
        data = strip_hashbang(data)
        length = len(data)
        if length > len(self.M):
            raise Error('file {} is too big to fit in memory'.format(file))
        if length % word_bytes != 0:
            raise Error('file {} is not a whole number of words'.format(file))
        if addr is None:
            addr = self.M.addr
        self.M[addr:addr + length] = data
        return length // word_bytes

    def save(self, file, addr=None, length=None):
        '''
        Save a binary file from the given address and length.
        '''
        assert length is not None
        if addr is None:
            addr = self.M.addr
        if (not is_aligned(addr) or
            addr < self.M.addr or addr + length * word_bytes > self.M.addr + len(self.M)):
            raise Error("invalid or unaligned address")

        with open(file, 'wb') as h:
            h.write(bytes(self.M[addr:addr + length * word_bytes]))

    def disassemble(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Disassemble `length` words from `start`, or from `start` to `end`.
        '''
        if length is not None:
            end = start + length * word_bytes
        for inst in Disassembler(self, pc=start, end=end):
            print(inst, file=file)

    def dump(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Dump `length` words from `start` (rounded down to nearest 16),
        or from `start` to `end`.
        Defaults to 64 words from `start`.
        '''
        chunk = 16
        if start is None:
            start = max(0, self.registers["pc"].get())
        start -= start % chunk
        if length is not None:
            end = start + length * word_bytes
        elif end is None:
            end = start + 64 * word_bytes

        p = start
        while p < end:
            print(("{:#0" + str(hex0x_word_width) + "x} ").format(p), end='', file=file)
            ascii = ""
            i = 0
            while i < chunk and p < end:
                if i % 8 == 0:
                    print(" ", end='', file=file)
                byte = M[p + i]
                print("{:02x} ".format(byte), end='', file=file)
                i += 1
                c = chr(byte)
                ascii += c if c.isprintable() else '.'
            p += chunk
            print(" |{0:.{1}}|".format(ascii, chunk), file=file)

    def dump_files(self, basename, addr, length):
        '''
        Dump memory as assembly to `basename.asm` and as hex to `basename.hex`.
        '''
        asm_file = '{}.asm'.format(basename)
        with open(asm_file, 'w') as h:
            self.disassemble(addr, length, file=h)
        hex_file = '{}.hex'.format(basename)
        with open(hex_file, 'w') as h:
            self.dump(addr, length, file=h)


class Register:
    '''
    A VM register.

     - state - a c_void_p which is a mit_state *.
     - register - an enums.Register indicating which register this is.
    '''
    def __init__(self, state, register):
        self.state = state
        self.register = register
        self.getter = libmit["mit_get_{}".format(register.name)]
        self.getter.restype = c_uword
        self.getter.argtypes = [c_void_p]
        self.setter = libmit["mit_set_{}".format(register.name)]
        self.setter.restype = None
        self.setter.argtypes = [c_void_p, c_uword]

    def __index__(self):
        return self.get()

    def __int__(self):
        return self.__index__()

    def __str__(self):
        return str(hex(int(self)))

    def __repr__(self):
        return str(self)

    def get(self):
        return int(self.getter(self.state))

    def set(self, v):
        self.setter(self.state, v)


class Stack:
    '''
    VM stack.

     - state - a c_void_p which is a mit_state *.

    When specifying stack indices, this class uses the Python convention, so
    0 is the base of the stack. In contrast, the C API (`mit_load_stack()`
    etc.) use the convention that 0 is the top of the stack.
    '''
    def __init__(self, state):
        self.state = state
        self.stack_depth = Register(state, enums.Register.stack_depth)

    def __str__(self):
        return '[{}]'.format(', '.join(
            ['{} ({:#x})'.format(v, v & word_mask) for v in self])
        )

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.stack_depth.get()

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        else:
            v = c_word()
            libmit.mit_load_stack(self.state, len(self) - 1 - index, byref(v))
            return v.value

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            for i, v in zip(range(*index.indices(len(self))), value):
                self[i] = v
        else:
            libmit.mit_store_stack(self.state, len(self) - 1 - index, value)

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def push(self, v):
        '''Push a word on to the stack.'''
        ret = libmit.mit_push_stack(self.state, v)

    def pop(self):
        '''Pop a word off the stack.'''
        v = c_word()
        ret = libmit.mit_pop_stack(self.state, byref(v))
        return v.value
