import hashlib

import vm_data

# Database of all possible trace events.

class Event:
    '''
    An event that might occur in a trace.

     - trace_name - bytes - the text that appears in a trace.
     - name - str - the human-readable name of the event.
     - exec_code - str - C statements to execute when the event happens.
     - guess_code - str - C if statement to test if this is the next event.
     - hash0 - a random-looking 63-bit mask.
     - hash1 - a random-looking 63-bit mask.

    On entry to `exec_code`, S->PC will be one byte beyond the beginning of
    the instruction. On exit, S->PC must point to the next instruction.

    `guess_code` must be side-effect-free; in particular it must not access
    memory. On evaluation, `next_byte` will be the first byte of the
    instruction.
    '''

    def __init__(self, trace_name, name, exec_code, guess_code):
        self.trace_name = trace_name
        self.name = name
        self.exec_code = exec_code
        self.guess_code = guess_code
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
for i, a in enumerate(vm_data.Actions):
    ALL_EVENTS.append(Event(b'1 %08x' % a.value.opcode, a.name, a.value.code,
        'next_byte == INSTRUCTION_ACTION_BIT | {}'.format(a.value.opcode),
    ))
for n in [0, 1]:
    ALL_EVENTS.append(Event(b'0 %08x' % n, 'LIT{}'.format(n), '''\
    PUSH({});'''.format(n),
        'next_byte == {}'.format(n),
    ))
ALL_EVENTS.append(Event(b'0 n', 'LITn', '''\
    S->PC--;
    RAISE(smite_decode_instruction(S, &S->PC, &S->I));
    PUSH(S->I)''',
    '(next_byte & INSTRUCTION_ACTION_BIT) == 0 && next_byte > 1',
))

# Indices for finding Events.
EVENT_TRACE_NAMES = {event.trace_name: event for event in ALL_EVENTS}
EVENT_NAMES = {event.name: event for event in ALL_EVENTS}
