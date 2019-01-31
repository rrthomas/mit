#!/usr/bin/python3
'''
Process an instruction trace, and build a specialised interpreter. Unfinished.

For the purposes of this program, a trace is an (ASCII) text file with one "event" per line. Events are therefore newline-free byte strings, and distinct byte strings are distinct events.

The abstraction of events is compatible with traces recorded using "smite --trace". [TODO: Change "smite --trace" behaviour so the values of number literals are suppressed.]

When finished, the program will compute the control-flow structure of an interpreter specialised for the instruction trace. This can be used to compile a version of smite that is fast for programs similar to the instruction trace. (For other programs it is correct and no slower than an unspecialised smite).
'''

import sys, hashlib, pickle

import vm_data

if len(sys.argv) != 2:
    print("Usage: predictor.py TRACE-FILE")
    sys.exit(1)
trace_filename = sys.argv[1]

# Database of all possible events.

class Event:
    '''
    An event that might occur in a trace.

     - index - int - index at which this Event can be found in ALL_EVENTS.
     - trace_name - bytes - the text that appears in a trace.
     - name - str - the human-readable name of the event.
     - hash0 - a random-looking 63-bit mask.
     - hash1 - a random-looking 63-bit mask.
    '''

    def __init__(self, index, trace_name, name):
        self.trace_name = trace_name
        self.name = name
        # Compute hashes.
        h = hashlib.md5()
        h.update(event)
        g = int.from_bytes(h.digest(), byteorder='little')
        self.hash0 = h & 0x7FFFFFFFFFFFFFFF; h >>= 63
        self.hash1 = h & 0x7FFFFFFFFFFFFFFF; h >>= 63

ALL_EVENTS = [
    Event(i, b'1 %08x' % a.value.opcode, a.name)
    for i, a in enumerate(vm_data.Actions)
]

ALL_EVENTS.append(Event(len(ALL_EVENTS), b'0 0', 'LIT0'))
ALL_EVENTS.append(Event(len(ALL_EVENTS), b'0 1', 'LIT1'))
ALL_EVENTS.append(Event(len(ALL_EVENTS), b'0 ?', 'LIT'))

EVENT_INDEX = {event.trace_name: event for event in ALL_EVENTS}

# Predictor.

def step(history, event):
    '''
    Given a hash of recent history and an event that occurred, returns the
    new hash of recent history.
     - history - a 32-bit hash of history.
     - event - Event.
    '''
    or_mask = event.hash0 & event.hash1
    and_mask = event.hash0 | event.hash1
    return (history | or_mask) & and_mask

class Predictor:
    '''
    Public fields:
     - predictions - a dict from history value (int) to a list of count (int).
       The list is indexed by Event.index. The new history value arising from
       an event can be computed using `step()`.
    '''

    def __init__(self):
        self.predictions = {} # history (int) -> Event -> count (int).

    def record_event(self, history, event):
        '''
        Records that `event` occurred at `history`.
         - history - 63-bit hash of history.
         - event - Event.
        '''
        if history not in self.predictions:
            self.predictions[history] = [0] * len(ALL_EVENTS)
        counts = self.predictions[history]
        counts[event.index] += 1

    def event_count(self, history, event):
        if history not in self.predictions:
            return 0
        return self.predictions[history][event.index]

    def __str__(self):
        return 'Predictor({\n  %s\n})' % (
            '\n  '.join(
                '%08x: {\n    %s\n  }' % (
                    history,
                    ',\n    '.join(
                        '%08x: %d' % (event, count)
                        for (event, count) in counts.items()
                    ),
                )
                for (history, counts) in self.predictions.items()
            ),
        )

# Build a Predictor.

print("Building a predictor")

def open_trace(trace_filename):
    '''Yields Event objects.'''
    with open(trace_filename, 'rb') as trace:
        for line in trace:
            line = line.strip()
            if line in EVENT_INDEX:
                yield EVENT_INDEX[line]
            elif line.startswith(b'0 '):
                yield EVENT_INDEX[b'0 ?']
            else:
                raise ValueError(line)

predictor = Predictor()
history = 0
for event in open_trace(trace_filename):
    predictor.record_event(history, event)
    history = step(history, event)

# Dump to a file, abstracting history, and removing rare states.

all_histories = [
    history
    for history, counts in predictor.items()
    if sum(counts) >= 100
]

history_index = {
    history: state
    for state, history in enumerate(all_histories)
}

state_table = [
    {
        event.name: (history_index[step(history, event)], count)
        for (event, count) in predictor.predictions[history].items()
        if step(history, event) in history_index
        if count > 0
    }
    for history in all_histories
]

out_filename = '/tmp/predictor'
with open(out_filename, 'wb') as f:
    # [{event_name: (new_state, count)]
    pickle.dump(state_table, f)
print('Wrote {}'.format(out_filename))
