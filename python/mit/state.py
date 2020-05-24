'''
VM state.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import sys
from types import FunctionType
from dataclasses import dataclass
from ctypes import create_string_buffer, byref, POINTER, cast, c_void_p

from . import enums
from .binding import (
    run, run_ptr, run_fast, run_break, break_fn_ptr,
    Error, VMError, is_aligned,
    stack_words,
    word_bytes, uword_max,
    c_word, c_uword, c_mit_fn,
    hex0x_word_width, register_args,
)
from .memory import Memory
from .assembler import Assembler
from .disassembler import Disassembler


class State:
    '''
    A VM state.

     - args - list of str - command-line arguments to register.
     - memory - Memory - the memory used. (The VM can use other memory, but
       the block of memory supplied can be accessed conveniently from
       Python.)

    Note: For some reason, an array created as a "multiple" of c_char does
    not have the right type. ctypes.create_string_buffer must be used.
    '''
    def __new__(cls, memory_words=1024*1024, args=None):
        '''
        Create the VM state.

         - memory_words - int - number of words of main memory.
        '''
        state = super().__new__(cls)
        if memory_words is not None:
            state.M = Memory(create_string_buffer(memory_words * word_bytes))
            state.M_word = Memory(state.M.buffer, element_size=word_bytes)
            state.pc = state.M.addr
        else:
            state.pc = None
        if args is not None:
            assert isinstance(args, list)
            args.insert(0, b"python")
            register_args(*args)
        return state

    def run(self, run_fn=run_fast):
        '''
        Run until execution halts.

         - run_fn - optional c_mit_fn - c_mit_fn to use. Defaults to
           `run_fast`.
        '''
        run_ptr.contents = run_fn
        run(
            cast(self.pc, POINTER(c_word)),
            0,
            cast((c_word * stack_words.value)(), POINTER(c_word)),
            byref(c_uword(0)),
        )

    def step(self, n=1, addr=None, trace=False, step_callback=None, final_callback=None):
        'Single-step for `n` steps, or until `pc`=addr.'
        with BreakHandler(self, n, addr, trace, step_callback, final_callback) as handler:
            try:
                self.run(run_fn=run_break)
            except VMError as e:
                if e.args[0] != enums.MitErrorCode.BREAK:
                    ret = e.args[0]
                    steps = " after {} step{}".format(
                        handler.done,
                        's' if handler.done != 1 else ''
                    )
                    print(f"Error code {ret} was returned{steps}", end='')
                    if addr is not None:
                        print(f" at pc={self.pc:#x}", end='')
                    print()
                    raise

    def log(self, *args):
        print(*args, file=sys.stderr)

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
        Save a binary image of the VM memory.

         - addr - int - start address, defaults to `self.M.addr`.
         - length - int - length in words, defaults to `len(self.M_word)`.
        '''
        if addr is None:
            addr = self.M.addr
            length = len(self.M_word)
        else:
            assert length is not None
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


@dataclass
class BreakHandler:
    '''
    Callback provider for `mit_run()`'s `break_fn`.

     - state - State - state to use.
     - n - int or None - number of instructions (including `next` and
       `nextff`) to run.
     - addr - int or None - address to run to.
     - trace - bool - if true, print tracing information for each
       instruction.
     - step_callback - optional function - if not None, a function `f(state,
       stack)` to call before each instruction is executed, which returns a
       MitErrorCode to pass as the return value of `break_fn`, or `None` to
       return the default value.
     - final_callback - optional function - like `step_callback`, but called
       when the exit condition is reached.
     - done - int - number of instructions run so far.

    If both `addr` and `n` are set, `addr` takes priority.
    '''
    state: State
    n: int=1
    addr: int=None
    trace: bool=False
    step_callback: FunctionType=None
    final_callback: FunctionType=None

    def __post_init__(self):
        self.done = 0

    def log(self, *args):
        print(*args, file=sys.stderr)
        sys.stderr.flush()

    def __enter__(self):
        self._old_break_fn = break_fn_ptr.value if break_fn_ptr else None
        # Prevent c_break_fn being GC'ed.
        self._new_break_fn = c_mit_fn(self.break_fn)
        # We need the actual C function entry point, not the address of the
        # Python object, which is what we would get from a `CFunctionType`.
        break_fn_ptr.value = cast(self._new_break_fn, c_void_p).value
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._old_break_fn is not None:
            break_fn_ptr.value = self._old_break_fn
        self._new_break_fn = None

    def break_fn(self, pc, ir, stack, stack_depth):
        '''
        This is a `mit_fn_t` (see run.h).
        '''
        self.state.pc = cast(pc, c_void_p).value
        self.state.ir = ir
        if stack:
            stack = (c_word * stack_words.value).from_address(
                cast(stack, c_void_p).value
            )[0:stack_depth.contents.value]
        else:
            stack = []
        if (self.addr is not None and self.state.pc != self.addr) or self.done < self.n:
            if self.trace:
                self.log(f"{stack}")
                self.log(f"pc={self.state.pc:#x} ir={ir & uword_max:#x} {Disassembler(self.state, ir=ir).disassemble()}")
            if self.step_callback is not None:
                error = self.step_callback(self, stack)
                if error is not None:
                    return error
            self.done += 1
            return enums.MitErrorCode.BREAK
        if self.final_callback is not None:
            error = self.final_callback(self, stack)
            if error is not None:
                return error
        return enums.MitErrorCode.OK
