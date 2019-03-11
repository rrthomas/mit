import hashlib

from smite_core import vm_data

# Database of all possible trace events.

class Event:
    '''
    An event that might occur in a trace.

     - trace_name - bytes - the text that appears in a trace.
     - name - str - the human-readable name of the event.
     - guess_code - str - C expression to test if this is the next event.
     - code - str - C statements to execute when the event happens.
     - hash0 - a random-looking 63-bit mask.
     - hash1 - a random-looking 63-bit mask.

    `guess_code` must be side-effect-free; in particular it must not access
    memory. On evaluation, `NEXT` will be the first byte of the
    instruction.

    On entry to `code`:
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
    Note that `code` uses the local variable `ITYPE` to cache the value
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
        code
    ):
        self.trace_name = trace_name
        self.name = name
        self.itype = itype
        self.args = args
        self.results = results
        self.guess_code = guess_code
        self.code = code
        # Compute hashes.
        h = hashlib.md5()
        h.update(trace_name)
        h = int.from_bytes(h.digest(), byteorder='little')
        self.hash0 = h & 0x7FFFFFFFFFFFFFFF; h >>= 63
        self.hash1 = h & 0x7FFFFFFFFFFFFFFF; h >>= 63

ALL_EVENTS = []
# Instructions.
for a in vm_data.Actions:
    code = '''\
{}
        TRACE(INSTRUCTION_ACTION, {});
    '''.format(a.value.code.rstrip(), a.value.opcode)
    ALL_EVENTS.append(Event(
        b'1 %08x' % a.value.opcode,
        a.name,
        'INSTRUCTION_ACTION',
        a.value.args,
        a.value.results,
        'NEXT == {}'.format(a.value.opcode),
        code,
    ))
# Common literals.
for n in [0, 1]:
    code = '''\
        lit = {};
        TRACE(INSTRUCTION_NUMBER, lit);
    '''.rstrip().format(n)
    ALL_EVENTS.append(Event(
        b'0 %08x' % n,
        'LIT{}'.format(n),
        'INSTRUCTION_NUMBER',
        [],
        ['lit'],
        'NEXT == ({} | INSTRUCTION_NUMBER_BIT)'.format(n),
        code,
    ))
# General literals.
code = '''\
        S->PC--;
        smite_UWORD itype;
        error = smite_decode_instruction(S, &S->PC, &itype, &lit);
        if (error != 0)
            RAISE(error);
        assert(itype == INSTRUCTION_NUMBER);
        TRACE(INSTRUCTION_NUMBER, lit);
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
    code,
))

# Indices for finding Events.
EVENT_TRACE_NAMES = {event.trace_name: event for event in ALL_EVENTS}
EVENT_NAMES = {event.name: event for event in ALL_EVENTS}
