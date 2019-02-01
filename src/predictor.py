#!/usr/bin/python3
'''
Process an instruction trace, and build a specialised interpreter. Unfinished.

For the purposes of this program, a trace is an (ASCII) text file with one "event" per line. Events are therefore newline-free byte strings, and distinct byte strings are distinct events.

The abstraction of events is compatible with traces recorded using "smite --trace". [TODO: Change "smite --trace" behaviour so the values of number literals are suppressed.]

When finished, the program will compute the control-flow structure of an interpreter specialised for the instruction trace. This can be used to compile a version of smite that is fast for programs similar to the instruction trace. (For other programs it is correct and no slower than an unspecialised smite).
'''

import sys, pickle

from events import ALL_EVENTS, EVENT_TRACE_NAMES, EVENT_NAMES

if len(sys.argv) != 2:
    print("Usage: predictor.py TRACE-FILE")
    sys.exit(1)
trace_filename = sys.argv[1]

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
     - predictions - a dict from history value (int) to a dict from event
       (bytes) to count (int). The new history value arising from an event can
       be computed using `step()`.
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
            self.predictions[history] = {}
        counts = self.predictions[history]
        if event.name not in counts:
            counts[event.name] = 0
        counts[event.name] += 1

    def event_count(self, history, event):
        if history not in self.predictions:
            return 0
        return self.predictions[history][event.name]

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
            if line in EVENT_TRACE_NAMES:
                yield EVENT_TRACE_NAMES[line]
            elif line.startswith(b'0 '):
                yield EVENT_TRACE_NAMES[b'0 n']
            else:
                raise ValueError(line)

predictor = Predictor()
history = 0
progress = 0
for event in open_trace(trace_filename):
    predictor.record_event(history, event)
    history = step(history, event)
    progress += 1
    if progress >= 1000000:
        progress = 0
        print('.', end='', flush=True)

# Dump to a file, abstracting history, and removing rare states.

all_histories = [
    history
    for history, counts in predictor.predictions.items()
    if sum(counts.values()) >= 100
]

history_index = {
    history: state
    for state, history in enumerate(all_histories)
}

state_table = [
    {
        event: (history_index[step(history, EVENT_NAMES[event])], count)
        for (event, count) in predictor.predictions[history].items()
        if step(history, EVENT_NAMES[event]) in history_index
        if count > 0
    }
    for history in all_histories
]

out_filename = '/tmp/predictor.pickle'
with open(out_filename, 'wb') as f:
    # [{event_name: (new_state, count)]
    pickle.dump(state_table, f)
print('Wrote {}'.format(out_filename))
