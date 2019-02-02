#!/usr/bin/python3
'''
Process an instruction trace, and build a specialised interpreter. Unfinished.

For the purposes of this program, a trace is an (ASCII) text file with one "event" per line. Events are therefore newline-free byte strings, and distinct byte strings are distinct events.

The abstraction of events is compatible with traces recorded using "smite --trace". [TODO: Change "smite --trace" behaviour so the values of number literals are suppressed.]

When finished, the program will compute the control-flow structure of an interpreter specialised for the instruction trace. This can be used to compile a version of smite that is fast for programs similar to the instruction trace. (For other programs it is correct and no slower than an unspecialised smite).
'''

import sys, pickle

from events import Event, ALL_EVENTS, EVENT_NAMES

if len(sys.argv) != 2:
    print("Usage: language.py <predictor-filename>", file=sys.stderr)
    sys.exit(1)
predictor_filename = sys.argv[1]

with open(predictor_filename, 'rb') as f:
    # [{event_name: (new_state, count)]
    predictor = pickle.load(f)

# Find all paths through the predictor.

print("Finding paths")

# Total visit count of each state.
# [int]
state_counts = [
    sum(count for _, count in transitions.values())
    for transitions in predictor
]

# Estimated probability distribution over events for each state.
# [{event: (new_state, probability)}]
state_probabilities = [
    {
        event: (
            new_state,
            float(count + 1) / float(state_counts[state] + 64),
        )
        for event, (new_state, count) in transitions.items()
    }
    for state, transitions in enumerate(predictor)
]

# TODO: This should be a dict, because the paths are distinct.
language = [] # [(tuple of events (str), estimated_count (int))]

def walk(path, distribution):
    '''
     - path - list of event (bytes).
     - distribution - list of estimated frequency (float).
    '''
    # Check for repetition.
    for n in range(1, len(path)//2):
        if path[-n:]==path[-2*n:-n]: return
    # Check for statistical irrelevance (but keep singleton paths).
    estimated_count = sum(distribution)
    if len(path) > 1 and estimated_count < 10000.: return
    # Okay, we'll keep it.
    language.append((tuple(path), estimated_count))
    # For all (state, action) pairs, propagate count to the successor state.
    successors = {event.name: [0.] * len(predictor) for event in ALL_EVENTS}
    for state, estimated_count in enumerate(distribution):
        if estimated_count > 1.:
            probabilities = state_probabilities[state]
            for event, (new_state, probability) in probabilities.items():
                additional_count = estimated_count * probability
                if additional_count >= 1.:
                    successors[event][new_state] += additional_count
    # Recurse down the tree.
    for event, new_distribution in successors.items():
        new_path = path + [event]
        walk(new_path, new_distribution)

walk([], [float(x) for x in state_counts])

# Dump to a file.

out_filename = '/tmp/language.pickle'
with open(out_filename, 'wb') as f:
    # [((str, ...), float)]
    pickle.dump(language, file=f)
print('Wrote {}'.format(out_filename))
