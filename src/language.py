#!/usr/bin/python3
'''
Process an instruction trace, and build a specialised interpreter. Unfinished.

For the purposes of this program, a trace is an (ASCII) text file with one "event" per line. Events are therefore newline-free byte strings, and distinct byte strings are distinct events.

The abstraction of events is compatible with traces recorded using "smite --trace". [TODO: Change "smite --trace" behaviour so the values of number literals are suppressed.]

When finished, the program will compute the control-flow structure of an interpreter specialised for the instruction trace. This can be used to compile a version of smite that is fast for programs similar to the instruction trace. (For other programs it is correct and no slower than an unspecialised smite).
'''

import sys, pickle

if len(sys.argv) != 2:
    print("Usage: language.py <predictor-filename>")
    sys.exit(1)
predictor_filename = sys.argv[1]

with open(predictor_filename, 'rb') as f:
    # [{event_name: (new_state, count)]
    predictor = pickle.load(f)

# Find all paths through the predictor.

print("Finding paths")

def is_repeating(path):
    for n in range(1, len(path)//2):
        if path[-n:]==path[-2*n:-n]:
            return True
    return False

# Total visit count of each state.
# [int]
state_counts = [
    sum(count for _, count in transitions)
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
        for event, (new_state, count) in transitions
    }
    for transitions in predictor
]

paths = [] # [(tuple of events (bytes), estimated_count (int))]

def walk(path, distribution):
    '''
     - path - list of event (bytes).
     - distribution - list of estimated frequency (float).
    '''
    estimated_count = sum(distribution.values)
    if estimated_count < 10000. or is_repeating(path):
        return
    paths.append((tuple(path), estimated_count))
    successors = {} # event (bytes) -> distribution

    def accumulate(event, new_state, additional_count):
        if additional_count < 1.:
            return
        if event not in successors:
            successors[event] = [0] * len(predictor)
        successors[event][new_state] += additional_count

    for state, estimated_count in enumerate(distribution):
        if estimated_count > 1.:
            for event, (new_state, probability) in state_probabilities[state]:
                accumulate(event, new_state, estimated_count * probability)
    for event, new_distribution in successors.items():
        new_path = path + [event]
        walk(new_path, new_distribution)

walk([], [float(x) for x in total_counts])

# TODO: Make sure we have the singleton string for each event.

# Dump to a file.

out_filename = '/tmp/language'
with open(out_filename, 'wb') as f:
    # [((bytes, ...), float)]
    pickle.dump(paths, file=f)
print('Wrote {}'.format(out_filename))
