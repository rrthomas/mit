'''
VM state.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import sys
from ctypes import POINTER, byref, c_void_p, cast, create_string_buffer
from dataclasses import dataclass
from types import FunctionType

from . import enums
from .assembler import Assembler
# from .binding import run_fast
from .binding import (
    Error, VMError, break_fn_ptr, c_mit_fn, c_uword, c_word, hex0x_word_width,
    is_aligned, register_args, run, run_break, run_ptr, run_simple,
    stack_words, uword_max, word_bytes
)
from .disassembler import Disassembler
from .memory import Memory


class State:
    '''
    A VM state.

     - pc - the initial value of `pc` used by `step()` and `run()`.
     - M - Memory - a byte view of some memory.
     - M_word - Memory - a word view of the same memory as `M`.
    '''
    def __init__(self, memory_words=1024*1024, args=None):
        '''
        Create the VM state.

         - memory_words - optional int - number of words of main memory to
           allocate. The VM can use other memory, but the block of memory
           allocated can be accessed conveniently from Python.
         - args - optional list of str - command-line arguments to register.
        '''
        if memory_words is not None:
            # Note: For some reason, an array created as a "multiple" of c_char
            # does not have the right type. ctypes.create_string_buffer must be
            # used.
            self.M = Memory(create_string_buffer(memory_words * word_bytes))
            self.M_word = Memory(self.M.buffer, element_size=word_bytes)
            self.pc = self.M.addr
        else:
            self.pc = None
        if args is not None:
            assert isinstance(args, list)
            args.insert(0, b"python")
            register_args(*args)

    def run(self, run_fn=run_simple):
        '''
        Run until execution halts. Execution will start at `self.pc` with an
        empty stack of capacity `stack_words`.

         - run_fn - optional c_mit_fn - c_mit_fn to use. Defaults to
           `run_simple`.
        '''
        run_ptr.contents = run_fn
        run(
            cast(self.pc, POINTER(c_word)),
            0, # ir
            cast((c_word * stack_words.value)(), POINTER(c_word)),
            stack_words.value,
            byref(c_uword(0)),
        )

    def step(self, n=1, addr=None, trace=False, step_callback=None, final_callback=None):
        '''
        Single-step for `n` steps, or until `pc`=addr. See class BreakHandler
        for details. Initial conditions are as for `run()`.
        '''
        with BreakHandler(self, n, addr, trace, step_callback, final_callback) as handler:
            try:
                self.run(run_fn=run_break)
            except VMError as e:
                if e.args[0] == enums.MitErrorCode.BREAK:
                    return
                ret = e.args[0]
                steps = "{} step{}".format(
                    handler.done,
                    's' if handler.done != 1 else ''
                )
                print(f"Error code {ret} was returned after {steps} at pc={self.pc:#x}")
                raise

    def load(self, file, addr=None):
        '''
        Load a binary file at the given address, which must be in `M`.
        `addr` defaults to `M.addr`. The length of `file` must be a whole
        number of words, not including any "#!" line.

        Returns the length of `file` in words.
        '''
        def strip_hashbang(data):
            if data[:2] != b'#!':
                return data
            try:
                return data[data.index(b'\n') + 1:]
            except ValueError: # No \n, so just a #! line
                return b''

        with open(file, 'rb') as h:
            data = h.read()
        data = strip_hashbang(data)
        if len(data) % word_bytes != 0:
            raise Error(f'file {file} is not a whole number of words')
        assert self.M is not None
        if addr is None:
            addr = self.M.addr
        end_addr = addr + len(data)
        if end_addr > self.M.addr + len(self.M):
            raise Error(f'file {file} does not fit in memory at {addr:#x}')
        try:
            self.M[addr:end_addr] = data
        except IndexError:
            raise Error("invalid or unaligned address")
        return len(data) // word_bytes

    def save(self, file, addr=None, length=None):
        '''
        Save a binary image of part of `M`.

         - addr - int - start address, defaults to `self.M.addr`.
         - length - int - length in words, defaults to saving up to the end of
           `self.M`.
        '''
        if addr is None:
            addr = self.M.addr
        if length is None:
            end_addr = self.M.addr + len(self.M)
        else:
            end_addr = addr + length * word_bytes
        try:
            data = bytes(self.M[addr:end_addr])
        except IndexError:
            raise Error("invalid or unaligned address")
        with open(file, 'wb') as h:
            h.write(data)

    def disassemble(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Disassemble `length` words from `start`, or from `start` to `end`.
        Arguments `start`, `length` and `end` are passed to Disassembler.
        '''
        for inst in Disassembler(self, pc=start, length=length, end=end):
            print(inst, file=file)

    def dump(self, start=None, length=None, end=None, file=sys.stdout):
        '''
        Dump `length` words from `start` (rounded down to nearest 16),
        or from `start` to `end`.
        Defaults to 64 words from `start`, which defaults to `pc`.
        '''
        if start is None:
            start = self.pc
        if length is not None:
            end = start + length * word_bytes
        elif end is None:
            end = min(start + 64 * word_bytes, self.M.addr + len(self.M))
        assert self.M.addr <= start <= end <= self.M.addr + len(self.M)

        chunk = 16
        p = start - start % chunk
        while p < end:
            print(("{:#0" + str(hex0x_word_width) + "x} ").format(p), end='', file=file)
            ascii = ""
            i = 0
            while i < chunk and p < end:
                if i % 8 == 0:
                    print(" ", end='', file=file)
                if start <= p + i < end:
                    byte = self.M[p + i]
                    byte_hex = f"{byte:02x}"
                    c = chr(byte)
                    c = c if c.isprintable() else '.'
                else:
                    byte_hex = "  "
                    c = " "
                print(f"{byte_hex} ", end='', file=file)
                ascii += c
                i += 1
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
     - step_callback - optional function - if not None, a function
       `f(BreakHandler, stack)` to call before each instruction is executed,
       which returns a MitErrorCode to pass as the return value of `break_fn`,
       or `None` to return the default value.
     - final_callback - optional function - like `step_callback`, but called
       when the exit condition is reached.
     - done - int - number of instructions run so far.

    If both `addr` and `n` are set, `addr` takes priority.
    '''
    state: State
    n: int = 1
    addr: int = None
    trace: bool = False
    step_callback: FunctionType = None
    final_callback: FunctionType = None

    # Returned by `break_fn` if `step_callback` or `final_callback` raises
    # an Exception.
    EXCEPTION_IN_BREAK_FN = -1024

    def __post_init__(self):
        self.done = 0

    def log(self, *args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)
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

    def break_fn(self, pc, ir, stack, stack_words, stack_depth):
        '''
        This is a `mit_fn_t` (see run.h).
        '''
        self.state.pc = cast(pc, c_void_p).value
        self.state.ir = ir
        if stack:
            stack = (c_word * stack_words).from_address(
                cast(stack, c_void_p).value
            )[0:stack_depth.contents.value]
        else:
            stack = []

        if self.addr is not None:
            terminate = self.state.pc == self.addr
        else:
            terminate = self.done >= self.n
        if terminate:
            if self.final_callback is not None:
                try:
                    error = self.final_callback(self, stack)
                except:
                    error = BreakHandler.EXCEPTION_IN_BREAK_FN
                if error is not None:
                    return error
            return enums.MitErrorCode.BREAK

        if self.trace:
            self.log(f"{stack}")
            self.log(f"pc={self.state.pc:#x} ir={ir & uword_max:#x} {Disassembler(self.state, ir=ir).disassemble()}")
        if self.step_callback is not None:
            try:
                error = self.step_callback(self, stack)
            except:
                error = BreakHandler.EXCEPTION_IN_BREAK_FN
            if error is not None:
                return error
        self.done += 1
        return enums.MitErrorCode.OK
