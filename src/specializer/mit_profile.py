'''
Library for reading and processing mit-profile data files.

(c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import json

from mit_core.spec import Instruction


class State:
    '''
    Represents a state of the interpreter that we profiled.
     - index - the index of this State in `profile`.
     - path - str (space-separated Instruction name) - the canonical path to
       this State.
     - guess - str (space-separated Instruction name) - the guessed
       continuation.
     - correct_state - int - the index of the State to jump to if `guess` is
       correct, or `-1` for the fallback state.
     - wrong_state - int - the index of the State to jump to if `guess` is
       wrong, or `-1` for the fallback state.
     - correct_count - the number of times `guess` was correct.
     - wrong_count - the number of times `guess` was wrong.
     - total_count - `correct_count + wrong_count`.
    '''
    def __init__(
        self,
        index,
        path,
        guess,
        correct_state,
        wrong_state,
        correct_count,
        wrong_count,
    ):
        self.index = index
        self.path = path
        self.guess = guess
        self.correct_state = correct_state
        self.wrong_state = wrong_state
        self.correct_count = correct_count
        self.wrong_count = wrong_count
        self.total_count = correct_count + wrong_count

    def __repr__(self):
        return 'State({}, {!r}, {!r}, {}, {}, {}, {})'.format(
            self.index,
            self.path,
            self.guess,
            self.correct_state,
            self.wrong_state,
            self.correct_count,
            self.wrong_count,
        )


def load(filename):
    '''
    Load a profile data file, and initialize `profile` and `ROOT_NODE`.
    '''
    global profile, ROOT_NODE
    with open(filename) as h:
        profile = [
            State(
                index,
                profile['path'],
                profile['guess'],
                profile['correct_state'],
                profile['wrong_state'],
                profile['correct_count'],
                profile['wrong_count'],
            )
            for index, profile in enumerate(json.load(h))
        ]
    root_state = 0 if len(profile) > 0 else -1
    ROOT_NODE = PathNode((), get_state(root_state), 1.0)


def get_state(index):
    if index == -1:
        return None
    else:
        return profile[index]


def counts():
    '''
    Returns a list of (count, instruction) sorted by descending count.
    '''
    # Read trace, computing opcode counts
    counts = {instruction: 0 for instruction in Instruction}
    for state in profile:
        for name in state.guess.split():
            # We'll get an error for an illegal opcode!
            counts[Instruction[name]] += state.correct_count

    # Compute instruction frequencies
    freqs = sorted([(count, instruction)
                    for instruction, count in counts.items()],
                   reverse=True,
                   key=lambda x: x[0])

    # Return instruction frequencies
    return freqs


class PathNode:
    '''
    Represents a node of the tree of probable paths.
     - guess - a tuple of Instructions that we've committed to.
     - profile_state - the State we'll reach after exhausting `guess`,
       or `None`.
     - frequency - an estimate of the relative frequency of this PathNode.
    '''
    def __init__(self, guess, profile_state, frequency):
        assert type(guess) is tuple
        assert profile_state is None or isinstance(profile_state, State)
        assert type(frequency) is float
        self.guess = guess
        self.profile_state = profile_state
        self.frequency = frequency

    def __repr__(self):
        return 'Node({!r}, {!r}, {})'.format(
            ' '.join(i.name for i in self.guess),
            self.profile_state,
            self.frequency,
        )

    def predict(self):
        '''
        Yields (Instruction, PathNode).
        '''
        if len(self.guess) > 0:
            yield (
                self.guess[0],
                PathNode(
                    self.guess[1:],
                    self.profile_state,
                    self.frequency,
                )
            )
        else:
            for successor in self._successors():
                for instruction, path_node in successor.predict():
                    yield (instruction, path_node)

    def _successors(self):
        '''
        Requires `self.guess` to be empty.
        Yields PathNodes whose union describes the same tree as `self`.
        '''
        assert len(self.guess) == 0
        if self.profile_state is not None and self.frequency > 0.0:
            ps = self.profile_state
            assert ps.total_count != 0
            # The successor if the guess is correct.
            yield PathNode(
                tuple(Instruction[name] for name in ps.guess.split()),
                get_state(ps.correct_state),
                self.frequency * ps.correct_count / ps.total_count,
            )
            # The successor if the guess is wrong.
            yield PathNode(
                (),
                get_state(ps.wrong_state),
                self.frequency * ps.wrong_count / ps.total_count,
            )
