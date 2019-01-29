#!/usr/bin/python3
'''
Process an instruction trace, and build a specialised interpreter. Unfinished.

For the purposes of this program, a trace is an (ASCII) text file with one "event" per line. Events are therefore newline-free byte strings, and distinct byte strings are distinct events.

The abstraction of events is compatible with traces recorded using "smite --trace". [TODO: Change "smite --trace" behaviour so the values of number literals are suppressed.]

When finished, the program will compute the control-flow structure of an interpreter specialised for the instruction trace. This can be used to compile a version of smite that is fast for programs similar to the instruction trace. (For other programs it is correct and no slower than an unspecialised smite).
'''

import sys, hashlib, pickle

import smite

if len(sys.argv) != 2:
    print("Usage: predictor.py <trace-filename>")
    sys.exit(1)
trace_filename = sys.argv[1]

VM = smite.State()

ALL_EVENTS = {
    (b'1 %08x' % opcode): bytes(name, 'ASCII')
    for opcode, name in VM.mnemonic.items()
}

ALL_EVENTS.update({
    b'0 0': b'LIT_0',
    b'1 1': b'LIT_1',
})

def open_trace(trace_filename):
    '''Yields bytes object.'''
    with open(trace_filename, 'rb') as trace:
        for line in trace:
            line = line.strip()
            if line in ALL_EVENTS:
                yield ALL_EVENTS[line]
            elif line.startswith(b'0 '):
                yield b'LIT'
            else:
                raise ValueError(line)

def event_hash(event):
    '''Returns a 128-bit integer hash of an integer input.'''
    h = hashlib.md5()
    h.update(event)
    return int.from_bytes(h.digest(), byteorder='little')

def step(history, event):
    '''
    Given a hash of recent history and an event that occurred, returns the
    new hash of recent history.
     - history - a 32-bit hash of history.
     - event - bytes.
    '''
    h = event_hash(event)
    h0 = h & 0xFFFFFFFF; h >>= 32
    h1 = h & 0xFFFFFFFF; h >>= 32
    return (history | h0) & h1        

class Predictor:
    '''
    Public fields:
     - predictions - a dict from history value (int) to a dict from event
       (bytes) to count (int). The new history value can be computed using
       `step()`.
    '''

    def __init__(self):
        self.predictions = {} # history (int) -> event (bytes) -> count (int).

    def record_event(self, history, event):
        '''
        Records that `event` occurred at `history`.
         - history - 32-bit hash of history.
         - event - bytes.
        '''
        if history not in self.predictions:
            self.predictions[history] = {}
        counts = self.predictions[history]
        if event not in counts:
            counts[event] = 0
        counts[event] += 1

    def event_count(self, history, event):
        if history not in self.predictions:
            return 0
        if event not in self.predictions[history]:
            return 0
        return self.predictions[history][event]

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

predictor = Predictor()
history = 0
for event in open_trace(trace_filename):
    predictor.record_event(history, event)
    history = step(history, event)

# Eliminate all the rare state transitions.

print("Deleting the rare bits")

predictions = {
    history: {
        event: count
        for (event, count) in predictor.predictions[history].items()
        #if count >= 1000
    }
    for (history, transitions) in predictor.predictions.items()
}

# Find all paths through the predictor.

print("Finding paths")

paths = {} # path (tuple of event (bytes)) -> estimated count (float)

def accumulate(path, count):
    '''
     - path - tuple of event.
     - count - float
    '''
    if path not in paths:
        paths[path] = 0
    paths[path] += count

def is_repeating(path):
    return False
    for n in range(1, len(path)//2 + 1):
        if path[-n:]==path[-2*n:-n]:
            return True
    return False

path = []

def walk(history, estimated_count):
    if estimated_count < 10000. or is_repeating(path):
        return
    accumulate(tuple(path), estimated_count)
    transitions = predictions[history]
    total_count = float(sum(transitions.values()) + 64)
    for (event, count) in transitions.items():
        probability = count/total_count
        if probability >= 0.1:
            path.append(event)
            walk(step(history, event), estimated_count*probability)
            path.pop()

for (history, transitions) in predictions.items():
    assert path == []
    walk(history, float(sum(transitions.values())))

# Make sure we have the singleton string for each event.
for event in ALL_EVENTS.values():
    accumulate((), 1.0)
    accumulate((event,), 1.0)

# Dump to a file.

out_filename = '/tmp/language'
with open(out_filename, 'wb') as f:
    pickle.dump(paths, file=f)
print('Wrote {}'.format(out_filename))
