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
Controlling and observing execution: run, step
Examining memory: dump, disassemble
'''

import os
import sys

from . import enums
from .binding import (
    libmit, libmitfeatures,
    Error, VMError, is_aligned,
    word_bytes, size_word, opcode_mask,
    c_word, c_uword, c_void_p, c_char_p, byref,
    hex0x_word_width,
)
from .assembler import Assembler, Disassembler


# Set up binary I/O flag
O_BINARY = 0
try:
    O_BINARY = os.O_BINARY
except:
    pass


class State:
    '''A VM state.'''
    def __new__(cls, memory_words=1024*1024 if word_bytes > 2 else 8*1024, stack_words=1024):
        '''Create the VM state.'''
        state = super().__new__(cls)
        state.state = libmit.mit_new_state(memory_words, stack_words)
        if state.state is None:
            raise Error("error creating virtual machine state")
        state.registers = {
            register.name: Register(state.state, register)
            for register in enums.Register
        }
        state.M = Memory(state.state)
        state.M_word = WordMemory(state.state)
        state.S = Stack(state.state)
        return state

    def __del__(self):
        libmit.mit_free_state(self.state)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['registers']
        state['registers'] = {
            name: register.get()
            for name, register in self.registers.items()
        }
        del state['M']
        del state['M_word']
        state['M_word'] = self.M_word[0:self.M.memory_words() * word_bytes]
        del state['S']
        state['S'] = self.S[0:self.registers["stack_depth"].get()]
        del state['state']
        if 'argv' in state:
            state['argv'] = [cstr for cstr in state['argv']]
        return state

    def __getnewargs__(self):
        return (self.M.memory_words(), libmit.mit_get_stack_words(self.state))

    def __setstate__(self, state):
        for name, value in state['registers'].items():
            self.registers[name].set(value)
        self.M_word[0:self.M.memory_words() * word_bytes] = state['M_word']
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
        assert(libmitfeatures.mit_register_args(argc, self.argv) == 0)

    def do_extra_instruction(self):
        libmitfeatures.mit_extra_instruction(self.state)
        self.registers["ir"].set(0) # Skip to next instruction

    def run(self, args=None, optimize=True):
        '''
        Run until `halt` or error.

         - args - list of str - command-line arguments to register.
         - optimize - bool - if True, run with optimization.
        '''
        if args is None:
            args = []
        args.insert(0, b"mit-shell")
        self.register_args(*args)
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
        print(" after {} step{}".format(done, 's' if done > 1 else ''), end='')
        if addr is not None:
            print(" at pc={:#x}".format(
                self.registers["pc"].get()),
                end='',
            )
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

    def load(self, file, addr=0):
        '''
        Load a binary file at the given address. Returns the length in words.
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
        if length > self.M.memory_words() * word_bytes:
            raise Error('file {} is too big to fit in memory'.format(file))
        if length % word_bytes != 0:
            raise Error('file {} is not a whole number of words'.format(file))
        self.M[addr:addr + length] = data
        return length // word_bytes

    def save(self, file, address=0, length=None):
        '''
        Save a binary file from the given address and length.
        '''
        assert length is not None
        ptr = libmit.mit_native_address_of_range(self.state, address, length * word_bytes)
        if not is_aligned(address) or not ptr:
            raise Error("invalid or unaligned address")

        with open(file, 'wb') as h:
            h.write(bytes(self.M[address:length * word_bytes]))

    # Disassembly
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
                byte = self.M[p + i]
                print("{:02x} ".format(byte), end='', file=file)
                i += 1
                c = chr(byte)
                ascii += c if c.isprintable() else '.'
            p += chunk
            print(" |{0:.{1}}|".format(ascii, chunk), file=file)


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
            ['{v} ({v:#x})'.format(v=v) for v in self])
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


class AbstractMemory:
    '''
    A view of VM memory (abstract superclass).

     - element_size - the number of bytes read/written at a time.

    Memory addresses are specified in bytes. Only addresses that are multiples
    of `element_size` are valid.

    Memory address slices' `start` and `stop` fields must be valid addresses.
    The `step` field must be `1` or `element_size`; either will be treated as
    `element_size`, i.e. only the valid addresses will be accessed.

    `len()` counts the valid addresses, i.e. the length is measured in
    elements. Use `memory_words()` for the number of words.
    '''
    def __init__(self, state, element_size):
        self.state = state
        self.element_size = element_size

    def memory_words(self):
        return int(libmit.mit_get_memory_words(self.state))

    def _slice_to_range(self, index):
        '''
        Returns a range that represents the valid addresses in `index`.
        '''
        index = range(*index.indices(self.memory_words() * word_bytes))
        assert index.start % self.element_size == 0
        assert index.stop % self.element_size == 0
        assert index.step in (1, self.element_size)
        return range(index.start, index.stop, self.element_size)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in self._slice_to_range(index)]
        else:
            return self.load(index)

    def __setitem__(self, index, value):
        if type(index) == slice:
            it = iter(value)
            for i in self._slice_to_range(index):
                self[i] = next(it)
            assert len(list(it)) == 0
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
        '''
        Returns the number of valid addresses. Note that this might not be the
        same as the number of bytes.
        '''
        return self.memory_words() * word_bytes // self.element_size


class Memory(AbstractMemory):
    '''A VM memory (byte-accessed).'''
    def __init__(self, state):
        super().__init__(state, 1)

    def load(self, index):
        word = c_word()
        libmit.mit_load(self.state, index, 0, byref(word))
        return word.value

    def store(self, index, value):
        libmit.mit_store(self.state, index, 0, value)


class WordMemory(AbstractMemory):
    '''A VM memory (word-accessed).'''
    def __init__(self, state):
        super().__init__(state, word_bytes)

    def load(self, index):
        word = c_word()
        libmit.mit_load(self.state, index, size_word, byref(word))
        return word.value

    def store(self, index, value):
        libmit.mit_store(self.state, index, size_word, value)
