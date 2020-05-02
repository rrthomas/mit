'''
VM state.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

The mit_state: state
Registers: a variable for each register
Memory: M, M_word
Stack: S
Managing the VM state: load, save
Controlling and observing execution: run, step, trace
Examining memory: dump, disassemble, dump_files
'''

import sys
from ctypes import create_string_buffer, byref, addressof

from . import enums
from .binding import (
    libmit, run, run_ptr,
    Error, VMError, is_aligned,
    word_bytes, word_mask, opcode_mask,
    c_word, c_uword, c_mit_state,
    hex0x_word_width, register_args,
    run_specializer, run_profile,
)
from .memory import Memory
from .assembler import Assembler, Disassembler


class State:
    '''
    A VM state.

         - args - list of str - command-line arguments to register.
         - memory - ctypes.Array of c_char - main memory.
         - stack - ctypes.Array of c_char - stack.

    Note: For some reason, an array created as a "multiple" of c_char does
    not have the right type. ctypes.create_string_buffer must be used.
    '''
    def __new__(cls, memory_words=1024*1024, stack_words=1024, args=None):
        '''
        Create the VM state.

         - memory_words - int - number of words of main memory.
         - stack_words - int - number of words of stack space.
        '''
        state = super().__new__(cls)
        state.state = c_mit_state()
        state._stack = create_string_buffer(stack_words * word_bytes)
        if stack_words is not None:
            state.stack = addressof(state._stack)
            state.stack_words = stack_words
        if memory_words is not None:
            state.set_memory(create_string_buffer(memory_words * word_bytes))
        state.S = Stack(state.state)
        if args is None:
            args = []
        args.insert(0, b"mit-shell")
        register_args(*args)
        return state

    def set_memory(self, memory):
        self.memory = memory
        self.M = Memory(self.memory)
        self.pc = self.M.addr
        self.M_word = Memory(self.memory, element_size=word_bytes)

    def __getattr__(self, name):
        if name in enums.Register.__members__:
            return self.state.__getattribute__(name)
        raise AttributeError

    def __setattr__(self, name, value):
        if name in enums.Register.__members__:
            self.state.__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def __getstate__(self):
        state = self.__dict__.copy()
        state['registers'] = {
            name: self.__getattr__(name)
            for name in enums.Register.__members__
            if name not in ('stack', 'stack_words')
        }
        del state['memory']
        del state['M']
        del state['M_word']
        state['M'] = bytes(self.M.buffer)[0:-1] # Remove trailing NUL
        del state['S']
        state['S'] = self.S[0:self.stack_depth]
        del state['_stack']
        del state['state']
        if 'argv' in state:
            state['argv'] = [cstr for cstr in state['argv']]
        return state

    def __getnewargs__(self):
        return (self.stack_words,)

    def __setstate__(self, state):
        for name, value in state['registers'].items():
            self.__setattr__(name, value)
        self.set_memory(create_string_buffer(state['M']))
        for item in state['S']: self.S.push(item)
        if 'argv' in state:
            register_args(*state['argv'])

    def run(self, optimize=True, profile=False):
        '''
        Run until `halt` or error.

         - optimize - bool - if True, run with optimization.
         - profile - bool - if True, run with profiling.
        '''
        assert optimize or not profile
        if profile:
            run_ptr.contents = run_profile
        elif optimize:
            run_ptr.contents = run_specializer
        run(self.state)

    def step(self, n=1, addr=None, trace=False, auto_NEXT=True):
        '''
        Single-step for n steps (excluding NEXT when pc does not change), or
        until pc=addr.
        '''
        done = 0
        ret = 0
        while addr is not None or done < n:
            if auto_NEXT and self.ir == 0:
                try:
                    libmit.mit_single_step(self.state)
                    return
                except VMError as e:
                    if e.args[0] != enums.MitErrorCode.BREAK:
                        raise
            if self.pc == addr: break
            if trace:
                self.trace_print(f"trace: instruction={Disassembler(self).disassemble()}")
            try:
                libmit.mit_single_step(self.state)
                return
            except VMError as e:
                if e.args[0] != enums.MitErrorCode.BREAK:
                    ret = e.args[0]
                    print(f"Error code {ret} was returned", end='')
                    print(" after {} step{}".format(done, 's' if done != 1 else ''), end='')
                    if addr is not None:
                        print(f" at pc={self.pc:#x}", end='')
                    print()
                    raise
            if trace:
                self.trace_print(f"pc={self.pc:#x} ir={self.ir:#x}")
                self.trace_print(str(self.S))
            done += 1

    def trace_print(self, *args):
        print(*args, file=sys.stderr)

    def trace(self, n=1, addr=None, auto_NEXT=True):
        'A convenience wrapper for `step(trace=True)`.'
        self.step(n=n, addr=addr, trace=True, auto_NEXT=auto_NEXT)

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
            raise Error(f'file {file} is too big to fit in memory')
        if length % word_bytes != 0:
            raise Error(f'file {file} is not a whole number of words')
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
            start = max(0, self.pc)
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
                print(f"{byte:02x} ", end='', file=file)
                i += 1
                c = chr(byte)
                ascii += c if c.isprintable() else '.'
            p += chunk
            print(f" |{ascii:.{chunk}}|", file=file)

    def dump_files(self, basename, addr, length):
        '''
        Dump memory as assembly to `basename.asm` and as hex to `basename.hex`.
        '''
        asm_file = f'{basename}.asm'
        with open(asm_file, 'w') as h:
            self.disassemble(addr, length, file=h)
        hex_file = f'{basename}.hex'
        with open(hex_file, 'w') as h:
            self.dump(addr, length, file=h)


class Stack:
    '''
    VM stack.

     - state - a c_mit_state.

    When specifying stack indices, this class uses the Python convention, so
    0 is the base of the stack. In contrast, the C API (`mit_stack_position()`
    etc.) use the convention that 0 is the top of the stack.
    '''
    def __init__(self, state):
        self.state = state

    def __str__(self):
        return '[{}]'.format(', '.join(
            [f'{v} ({v & word_mask:#x})' for v in self])
        )

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.state.stack_depth

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        else:
            ptr = libmit.mit_stack_position(self.state, len(self) - 1 - index)
            if ptr is not None:
                return ptr.contents.value
            raise IndexError

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            for i, v in zip(range(*index.indices(len(self))), value):
                self[i] = v
        else:
            ptr = libmit.mit_stack_position(self.state, len(self) - 1 - index)
            if ptr is not None:
                ptr.contents.value = value
            else:
                raise IndexError

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
