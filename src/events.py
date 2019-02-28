import hashlib

import vm_data

# Database of all possible trace events.

class Event:
    '''
    An event that might occur in a trace.

     - trace_name - bytes - the text that appears in a trace.
     - name - str - the human-readable name of the event.
     - guess_code - str - C expression to test if this is the next event.
     - exec_code - str - C statements to execute when the event happens.
     - hash0 - a random-looking 63-bit mask.
     - hash1 - a random-looking 63-bit mask.

    `guess_code` must be side-effect-free; in particular it must not access
    memory. On evaluation, `NEXT` will be the first byte of the
    instruction.

    On entry to `exec_code`:
     - `S->PC` is one byte beyond the beginning of the instruction,
     - `ITYPE` is undefined.
     - `S->I` is undefined.
     - (Deprecated) `exception` is 0.
    On exit:
     - `S->PC` must point to the next instruction,
     - `ITYPE` is set to the value that `S->ITYPE` should hold.
     - `S->I` is set correctly.
    Exceptions can be thrown using the RAISE() macro, passing a non-zero code;
    RAISE(0) succeeds (does nothing). (Deprecated) Setting `exception` to a
    non-zero value on exit also works.
    Note that `exec_code` uses the local variable `ITYPE` to cache the value
    of the corresponding SMite register. This values is kept in a local
    variable because it is usually dead. Its value is only written to the
    SMite register if required.
    '''

    def __init__(
        self,
        trace_name,
        name,
        itype,
        args,
        results,
        guess_code,
        exec_code
    ):
        self.trace_name = trace_name
        self.name = name
        self.itype = itype
        self.args = args
        self.results = results
        self.guess_code = guess_code
        self.exec_code = exec_code
        # Compute hashes.
        h = hashlib.md5()
        h.update(trace_name)
        h = int.from_bytes(h.digest(), byteorder='little')
        self.hash0 = h & 0x7FFFFFFFFFFFFFFF; h >>= 63
        self.hash1 = h & 0x7FFFFFFFFFFFFFFF; h >>= 63

# FIXME: The `guess_code` implementations that follow make assumptions about
# the implementation of `smite_decode_instruction()`, and will break if the
# instruction encoding changes. This seems unavoidable without calling
# `smite_decode_instruction()` after every instruction.
ALL_EVENTS = []
# Instructions.
for a in vm_data.Actions:
    exec_code = '''\
        S->I = {};
{}
        trace(S, ITYPE, S->I);
    '''.format(a.value.opcode, a.value.code.rstrip())
    ALL_EVENTS.append(Event(
        b'1 %08x' % a.value.opcode,
        a.name,
        'INSTRUCTION_ACTION',
        a.value.args,
        a.value.results,
        'NEXT == {}'.format(a.value.opcode),
        exec_code,
    ))
# Common literals.
for n in [0, 1]:
    exec_code = '''\
        lit = {};
        S->I = lit;
        trace(S, ITYPE, S->I);
    '''.rstrip().format(n)
    ALL_EVENTS.append(Event(
        b'0 %08x' % n,
        'LIT{}'.format(n),
        'INSTRUCTION_NUMBER',
        [],
        ['lit'],
        'NEXT == ({} | INSTRUCTION_NUMBER_BIT)'.format(n),
        exec_code,
    ))
# General literals.
exec_code = '''\
        S->PC--;
        RAISE(smite_decode_instruction(S, &S->PC, &lit));
        S->I = lit;
        trace(S, ITYPE, S->I);
'''.rstrip()
ALL_EVENTS.append(Event(
    b'0 n',
    'LITn',
    'INSTRUCTION_NUMBER',
    [],
    ['lit'],
    '(NEXT & INSTRUCTION_CONTINUATION_BIT) != 0 || (\
      (NEXT & INSTRUCTION_NUMBER_BIT) != 0 && \
      (NEXT & ~INSTRUCTION_NUMBER_BIT) > 1 \
     )',
    exec_code,
))

# Indices for finding Events.
EVENT_TRACE_NAMES = {event.trace_name: event for event in ALL_EVENTS}
EVENT_NAMES = {event.name: event for event in ALL_EVENTS}
